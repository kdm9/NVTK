#!/usr/bin/env python3
import imagehash
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from tqdm import tqdm

import argparse
import logging
from logging import ERROR, WARNING, INFO, DEBUG
import re
from pathlib import Path
import datetime as dt
import math
import json
import multiprocessing as mp
from collections import defaultdict
from sys import stderr, stdout, stdin
from hashlib import sha1


def get_logger(level=INFO):
    log = logging.getLogger(__name__)
    log.setLevel(level)
    stderr = logging.StreamHandler()
    stderr.setLevel(DEBUG)
    stderr.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(stderr)
    return log
LOG = get_logger()

def sha1hash(pathorbytes):
    if isinstance(pathorbytes, bytes):
        h = sha1(pathorbytes)
    else:
        h = sha1()
        with open(pathorbytes, "rb") as fh:
            while True:
                buf = fh.read(1024**2)
                if not buf:
                    break
                h.update(buf)
    return h.hexdigest()

class ImgMetaHash(object):

    def __init__(self, path=None, filename=None, data=None):
        self.qrcode = None
        self.camera = None
        self.datetime = None
        self.lat = None
        self.lon = None
        self.width = None
        self.height = None
        self.alt = None
        self.hash = None
        self.sha1 = None
        filedata = None
        if path is not None:
            self.filename = path
            filedata = Path(path)
        else:
            assert filename is not None and data is not None
            filedata = data
            self.filename = filename
        try:
            self.sha1 = sha1hash(filedata)
            self.image = Image.open(filedata)
            self.width, self.height = self.image.size
            self.hash = imagehash.whash(self.image)
            self.parse_exif()
            del self.image
        except Exception as exc:
            LOG.error("Couldn't read or process image '%s'", self.filename)
            LOG.info("ERROR: %s", str(exc))

    def __repr__(self):
        return f"qr={self.qrcode} dt={self.datetime} lt={self.lat} ln={self.lon} at={self.alt} cm={self.camera} ph={self.hash} sha={self.sha1}"

    def json(self):
        return {"filename": self.filename,
                "datetime": self.datetime,
                "lat": self.lat,
                "lon": self.lon,
                "alt": self.alt,
                "camera": self.camera,
                "width": self.width,
                "height": self.height,
                "hash": str(self.hash),
                "sha1": self.sha1}

    def parse_exif(self):
        exifdata = self.image._getexif()
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
        except (KeyError, ZeroDivisionError):
            lat = None
            lon = None

        try:
            alt = rat2float(decoded['GPSInfo'][6])
        except (KeyError, ZeroDivisionError):
            alt = None

        self.camera = camera
        self.lat = lat
        self.lon = lon
        self.alt = alt



def rat2float(rat):
    """EXIF data is either a IFDRational type which we can just call float()
    on, or a tuple of (num, denom) which we can't."""
    if isinstance(rat, tuple):
        n, d = float(rat[0]), float(rat[1])
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
    This script will cluster images by their exif data and/or pecerptual
    hashes. This is useful for when images are almost but not quite exact
    duplicates, and allows us to fuzzily de-duplicate images.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--threads", type=int, default=mp.cpu_count(),
            help="Number of CPUs to use for image decoding/scanning")
    ap.add_argument("-o", "--output", type=argparse.FileType("w"), default="-",
            help="ND-JSON output file.")
    ap.add_argument("images", nargs="+", help="List of images. Give '-' to accept newline delimited list from stdin.")
    args = ap.parse_args()

    if args.images[0] == "-":
        args.images = [l.rstrip("\n") for l in stdin]
        
    # Setup output
    if args.threads > 1:
        pool = mp.Pool(args.threads)
        map_ = pool.imap
    else:
        map_ = map

    images = []
    for img in tqdm(map_(ImgMetaHash, args.images), unit="images", total=len(args.images)):
        images.append(img)
        #print(json.dumps(img.json()), file=args.output)
    
    byhash = defaultdict(list)
    for image in images:
        byhash[str(image.hash)].append(image.json())

    json.dump(byhash, args.output, indent=4)



if __name__ == "__main__":
    climain()
