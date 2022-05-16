# Copyright 2021-2022  Kevin Murray, MPI Biologie Tübingen
# Copyright 2021-2022  Gekkonid Consulting
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from sys import stderr
from PIL import Image
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont
try:
    import HeifImagePlugin
except ImportError:
    print("Failed to load HeifImagePlugin. *.HEIF won't be supported.", file=stderr)
from PIL.ExifTags import TAGS, GPSTAGS
from pyzbar.pyzbar import decode, ZBarSymbol
from tqdm import tqdm


import argparse
import logging
from logging import ERROR, WARNING, INFO, DEBUG
import os
import re
import shutil
from pathlib import Path
import datetime as dt
import json
import base64
from io import BytesIO
from urllib.request import urlopen
import multiprocessing as mp

# TODO: make scale_image a separate function, reduce duplication
# TODO: PIL image to jpeg dataurl helper function


def get_logger(level=INFO):
    log = logging.getLogger(__name__)
    log.setLevel(level)
    stderr = logging.StreamHandler()
    stderr.setLevel(DEBUG)
    stderr.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(stderr)
    return log
LOG = get_logger()


def dataURI_to_file(uri):
    with urlopen(uri) as response:
        return BytesIO(response.read())


class ImgData(object):
    MIDSIZE_HEIGHT = 720

    def __init__(self, path=None, filename=None, data=None):
        self.qrcode = None
        self.camera = None
        self.datetime = None
        self.lat = None
        self.lon = None
        self.alt = None
        self.midsize = None
        filedata = None
        if path is not None:
            self.filename = Path(path).name
            filedata = path
        else:
            assert filename is not None and data is not None
            filedata = data
            self.filename = filename
        try:
            self.image = Image.open(filedata)
            self.midsize = self.scale_img(h=self.MIDSIZE_HEIGHT)
            self.width, self.height = self.image.size
            self.scan_codes()
            self.parse_exif()
            del self.image
        except Exception as exc:
            LOG.error("Couldn't read or process image '%s'", self.filename)
            LOG.info("ERROR: %s", str(exc))

    def scale_img(self,h):
        try:
            x, y = self.image.size
            if x == 0 or y == 0:
                return None
            scalar = 1 if h > y else h/y
            img_scaled = self.image.resize((int(round(x*scalar)), int(round(y*scalar))))
            buf = BytesIO()
            img_scaled.save(buf, format="JPEG")
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"data:image/jpeg;charset=utf-8;base64,{b64}"
        except Exception:
            return ""

    def __repr__(self):
        return f"qr={self.qrcode} dt={self.datetime} lt={self.lat} ln={self.lon} at={self.alt} cm={self.camera}"

    def parse_exif(self):
        exifdata = self.image.getexif()
        decoded = dict((TAGS.get(key, key), value) for key, value in exifdata.items())
        try:
            datetime = decoded['DateTimeOriginal']
            self.datetime = dt.datetime.strptime(datetime, "%Y:%m:%d %H:%M:%S").isoformat()
        except KeyError:
            self.datetime = None

        try:
            camera = f"{decoded['Make']} {decoded['Model']}"
            camera = re.sub(r'[^\w\-_\.]', '', camera)
        except KeyError:
            camera = None

        try:
            lat = degrees(decoded['GPSInfo'][2], decoded['GPSInfo'][1])
            lon = degrees(decoded['GPSInfo'][4], decoded['GPSInfo'][3])
        except KeyError:
            lat = None
            lon = None

        try:
            alt = rat2float(decoded['GPSInfo'][6])
        except KeyError:
            alt = None

        self.camera = camera
        self.lat = lat
        self.lon = lon
        self.alt = alt
    
    def scan_codes(self):
        self.qrcode = None
        x, y = self.image.size
        image = ImageOps.grayscale(self.image)
        for scalar in [0.2, 0.5, 0.1, 1.0]:
            LOG.debug("scalar is: %r", scalar)
            img_scaled = image.resize((int(x*scalar), int(y*scalar)))
            for sharpness in [0.1, 0.5, 1.5]:
                LOG.debug("sharpness is: %r", scalar)
                if sharpness != 1:
                    sharpener = ImageEnhance.Sharpness(img_scaled)
                    img_scaled = sharpener.enhance(sharpness)

                    codes = decode(img_scaled, [ZBarSymbol.QRCODE,])
                    if len(codes) > 0:
                        self.qrcode = [d.data.decode('utf8').strip() for d in codes]
                        LOG.debug("got codes: %r", self.qrcode)
                        return

    def as_response_json(self):
        return {
            "filename": self.filename,
            "qrcodes": self.qrcode,
            "camera": self.camera,
            "datetime": self.datetime,
            "lat": self.lat,
            "lng": self.lon,
            "alt": self.alt,
            "midsize": self.midsize,
        }


def rat2float(rat):
    """EXIF data is either a IFDRational type which we can just call float()
    on, or a tuple of (num, denom) which we can't."""
    if isinstance(rat, tuple):
        n, d = float(rat[0]), float(rat[1])
        if d == 0:
            return None
        else:
            return n/d
    else:
        return float(rat)


def degrees(dms, card):
    dms = rat2float(dms[0]) + rat2float(dms[1])/60 + rat2float(dms[2])/3600
    if card.upper() in ["S", "W"]:
        dms *= -1
    return dms


def climain():
    extrahelp = """
    This program detects QRcodes and other metadata in a folder of images, and
    saves it as a json for importing into the web gui.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--threads", type=int, default=mp.cpu_count(),
            help="Number of CPUs to use for image decoding/scanning")
    ap.add_argument("-o", "--output", type=argparse.FileType("w"), required=True,
            help="ND-JSON output file.")
    ap.add_argument("images", nargs="+", help="List of images")
    args = ap.parse_args()

    # Setup output
    if args.threads > 1:
        pool = mp.Pool(args.threads)
        map_ = pool.imap
    else:
        map_ = map

    for img in tqdm(map_(ImgData, args.images), unit="images", total=len(args.images)):
        print(json.dumps(img.as_response_json()), file=args.output)
