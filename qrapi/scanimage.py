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


def dataURI_to_file(uri):
    with urlopen(uri) as response:
        return BytesIO(response.read())


class ImgData(object):
    MIDSIZE_HEIGHT = 1080
    THUMB_HEIGHT = 100

    def __init__(self, path):
        self.path = Path(path)
        try:
            self.image = Image.open(path)
            self.width, self.height = self.image.size
        except Exception as exc:
            LOG.error("Couldn't read image '%s'", f)
            LOG.info("ERROR: %s", str(exc))
        self.parse_exif()
        self.scan_codes()
        self.midsize = self.scale_img(h=self.MIDSIZE_HEIGHT)
        self.thumb = self.scale_img(h=self.THUMB_HEIGHT)
        del self.image

    def __repr__(self):
        return f"{self.path} qr={self.qrcode} dt={self.datetime} lt={self.lat} ln={self.lon} at={self.alt} cm={self.camera}"



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
        codes = decode(self.image, [ZBarSymbol.QRCODE,])
        if len(codes) > 0:
            self.qrcode = [d.data.decode('utf8').strip() for d in codes]
            return
        # Reduce image size until the barcode scans. For some stupid reason this
        # works pretty well.
        #x, y = self.image.size
        #for scalar in [0.7, 0.5, 0.3]:
        #    LOG.debug("scalar is: %r", scalar)
        #    img_scaled = self.image.resize((int(x*scalar), int(y*scalar)))
        #    codes = decode('qrcode', img_scaled)
        #    LOG.debug("got codes: %r", codes)
        #    if codes is not None:
        #        if len(codes) == 1:
        #            self.qrcode = codes[0].decode('utf8')
        #        elif len(codes) > 1:
        #            LOG.warn("Image with more than 1 QR code: '%s'", self.image.filename)
        #            self.qrcode = None
        #        return

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


LOG = get_logger()
