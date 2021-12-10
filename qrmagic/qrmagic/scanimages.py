import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pyzbar.pyzbar import decode, ZBarSymbol

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

    def __init__(self, filedata):
        try:
            self.image = Image.open(filedata)
            self.width, self.height = self.image.size
        except Exception as exc:
            LOG.error("Couldn't read image '%s'", f)
            LOG.info("ERROR: %s", str(exc))
        self.parse_exif()
        self.scan_codes()
        self.midsize = self.scale_img(h=self.MIDSIZE_HEIGHT)
        del self.image

    def scale_img(self,h):
        try:
            x, y = self.image.size
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
        exifdata = self.image._getexif()
        decoded = dict((TAGS.get(key, key), value) for key, value in exifdata.items())
        datetime = decoded['DateTimeOriginal']

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

        self.datetime = dt.datetime.strptime(datetime, "%Y:%m:%d %H:%M:%S")
        self.camera = camera
        self.lat = lat
        self.lon = lon
        self.alt = alt
    
    def scan_codes(self):
        self.qrcode = None
        # Reduce image size until the barcode scans. For some stupid reason this
        # works pretty well.
        x, y = self.image.size
        for scalar in [0.1, 0.5, 1.0]:
            LOG.debug("scalar is: %r", scalar)
            img_scaled = self.image.resize((int(x*scalar), int(y*scalar)))

            codes = decode(self.image, [ZBarSymbol.QRCODE,])
            if len(codes) > 0:
                self.qrcode = [d.data.decode('utf8').strip() for d in codes]
                LOG.debug("got codes: %r", self.qrcode)
                return


def rat2float(rat):
    """EXIF data is either a IFDRational type which we can just call float()
    on, or a tuple of (num, denom) which we can't."""
    if isinstance(rat, tuple):
        return float(rat[0]) / float(rat[1])
    else:
        return float(rat)


def degrees(dms, card):
    dms = rat2float(dms[0]) + rat2float(dms[1])/60 + rat2float(dms[2])/3600
    if card.upper() in ["S", "W"]:
        dms *= -1
    return dms


def cli_main():
    extrahelp = """
    This program detects QRcodes and other metadata in a folder of images, and
    saves it as a TSV.

    If you want a nice way of doing this in a semi-automated way, use the web UI.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--threads", type=int, default=mp.cpu_count(),
            help="Number of CPUs to use for image decoding/scanning")
    ap.add_argument("-s", "--delay-seconds", type=int, default=0,
            help="Persist a QRcode scan for N seconds (default 0).")
    ap.add_argument("-M", "--metadata", type=argparse.FileType('w'), required=True,
            help="Write metadata to TSV file here")
    ap.add_argument("images", nargs="+", help="List of images")
    args = ap.parse_args()

    # Setup output
    if args.threads > 1:
        pool = mp.Pool(args.threads)
        map_ = pool.imap
    else:
        map_ = map

    metadata = [x for x in tqdm(map_(ImgData, args.images))]
    del pool

    if args.metadata:
        print("File", "ID", "DateTime", "Lat", "Lon", "Alt", "CameraID", sep='\t', file=args.metadata)
    last = None
    for img in sorted(metadata, key=lambda x: (x.camera, x.datetime, x.path)):
        this_id = "NOQRCODE"
        if img.qrcode is None:
            if last is not None and \
                    img.datetime is not None and \
                    last.datetime is not None and \
                    (img.datetime - last.datetime).total_seconds() < args.delay_seconds:
                this_id = last.qrcode
        else:
            last = img
            this_id = img.qrcode

        cam = "CAMUNKNOWN"
        if img.camera is not None:
            cam = img.camera

        def b(val):
            """Blank 'None's"""
            if val is None:
                return ""
            else:
                return val

        if args.metadata:
            print(img.path.resolve(), this_id, b(img.datetime), b(img.lat),
                    b(img.lon), b(img.alt), b(img.camera), sep='\t',
                    file=args.metadata)
