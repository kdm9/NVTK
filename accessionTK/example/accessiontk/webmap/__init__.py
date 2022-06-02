#!/usr/bin/env
from PIL import Image
try:
    import HeifImagePlugin
except ImportError:
    print("Failed to load HeifImagePlugin. *.HEIF won't be supported.", file=stderr)
from tqdm import tqdm


import argparse
from pathlib import Path
from csv import DictReader
from glob import glob
from collections import defaultdict
import json


def write_images(outprefix: str, srcpath: Path, widths: dict[str, int] = {"thumb": 200, "large": 1920}) -> list[str]:
    outpaths = {}
    src = Image.open(srcpath)
    for size, width in widths.items():
        if width == 0: # use 0 as width to preserve original dimensions
            resized = src.copy()
        else:
            w, h = src.width, src.height
            if w > h: # "width" acutally means the longer dimensions, which for portrait pics is height
                nw = min(w, width)
                nh = round(nw/w*h)
            else:
                nh = min(h, width)
                nw = round(nh/h*w)
            resized = src.resize((nw, nh), Image.LANCZOS)
        outfile = f"{outprefix}_{size}.jpg"
        outpaths[size] = outfile
        resized.save(outfile)
    return outpaths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--individual-colname", default="individual",
            help="Column name of individual ID")
    ap.add_argument("--locality-colname", default="locality",
            help="Column name of locality ID")
    ap.add_argument("--latitude-colname", default="latitude",
            help="Column name of latitude")
    ap.add_argument("--longitude-colname", default="longitude",
            help="Column name of latitude")
    ap.add_argument("--datetime-colname", default="datetime",
            help="Column name of datetime")
    ap.add_argument("--outdir", "-o", required=True,
            help="Output directory.")
    ap.add_argument("--srcimgdir", "-i", required=True,
            help="Directory of source image directories.")
    ap.add_argument("--indiv-table", "-t", required=True,
            help="Table of individuals as .csv or .tsv (delimiter must match filename).")
    args = ap.parse_args()


    localities = {}
    outdir = Path(args.outdir)

    with open(args.indiv_table) as fh:
        indivs = DictReader(fh, dialect="excel-tab")
        for indiv in tqdm(indivs):
            indiv_out = {}
            name = indiv[args.individual_colname]
            outimgs = []
            srcimgs = glob(f"{str(args.srcimgdir)/{name}/*.*")
            for i, srcimg in enumerate(map(Path, srcimgs)):
                outimgprefix = Path(f"{outdir}/{name}/{i+1:03d}")
                outimgprefix.parent.mkdir(exist_ok=True, parents=True)
                images = write_images(outimgprefix, srcimg)
                images_pathfix = {k: str(Path(v).relative_to(outdir)) for k, v in images.items()}
                outimgs.append(images_pathfix)
            loc = indiv[args.locality_colname]
            indiv_out = {
                "individual": name,
                "images": outimgs,
                "datetime": indiv[args.datetime_colname],
            }
            try:
                localities[loc]["individuals"].append(indiv)
            except KeyError:
                localities[loc] = {
                    "locality_name": loc,
                    "locality_description": indiv.get(args.locality_description, ""),
                    "lat": indiv[args.latitude_colname],
                    "lon": indiv[args.longitude_colname],
                    "individuals": [indiv_out,],
                }
        for locality in localities:
            srcimgs = glob(f"{str(args.srcimgdir)/{locality}/*.*")
            for i, srcimg in tqdm(enumerate(map(Path, srcimgs))):
                outimgprefix = Path(f"{outdir}/{locality}/{i+1:03d}")
                outimgprefix.parent.mkdir(exist_ok=True, parents=True)
                images = write_images(outimgprefix, srcimg)
                images_pathfix = {k: str(Path(v).relative_to(outdir)) for k, v in images.items()}
                outimgs.append(images_pathfix)
            localities[locality]["images"] = outimgs

    with open(outdir / "localities.json", "w") as jf:
        print(json.dumps(localities, indent=2), file=jf)

if __name__ == "__main__":
    main()
