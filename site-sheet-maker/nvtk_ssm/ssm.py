#!/usr/bin/env python3
import svglue
import cairosvg
import qrcode
from PyPDF2 import PdfFileMerger
from tqdm import tqdm

import argparse
import sys
from sys import stderr
import io

def one_page(id_str, template):
    of = io.BytesIO()
    tpl = svglue.load(file=template)

    tpl.set_text('id_text', id_str)

    img_io = io.BytesIO()
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=20, border=0)
    qr.add_data(id_str)
    qr.make(fit=True)
    img =  qr.make_image(fill_color="black", back_color="white")
    img.save(img_io, "PNG")
    for img_key in tpl._rect_subs:
        if img_key.startswith("id_image"):
            tpl.set_image(img_key, src=img_io.getvalue(), mimetype='image/png')
        else:
            print("WARNING: skipping rect with template-id", img_key, "as it doesn't start with 'id_image'. Check your SVG", file=stderr)
    cairosvg.svg2pdf(bytestring=str(tpl), write_to=of)
    return of



def main():
    ap = argparse.ArgumentParser()
    morehelp  = """
"""
    ap = argparse.ArgumentParser(epilog=morehelp, formatter_class=argparse.RawDescriptionHelpFormatter, prog="site-sheet-maker")
    ap.add_argument("--template", "-t", type=str, required=True,
            help="SVG template file. Must define id_image and id_text as custom template-id attributes on a rectangle and tspan respectively.")
    ap.add_argument("--output", "-o", type=argparse.FileType("wb"), metavar="FILE",
            help="Output PDF file.")
    ap.add_argument("--id-file", "-f", type=argparse.FileType("r"), metavar="FILE",
            help="File of IDs, one per line.")
    ap.add_argument("--id-format", type=str, metavar="FORMAT",
            help="Python-style format string governing ID format e.g. WGL{:04d} gives WGL0001..WGL9999")
    ap.add_argument("--id-start", type=int, default=1, metavar="N",
            help="First ID number (default 1)")
    ap.add_argument("--id-end", type=int, default=100, metavar="N",
            help="Last ID number (default 100)")
    args = ap.parse_args()

    if args.id_file is None and args.id_format is None:
        print("ERROR: must give eihter a file of ids to --id-file or an ID format to --id-format and --id-start and --id-end.")
        ap.print_help()
        sys.exit(1)
    if args.output is None:
        print("ERROR: must give an output PDF file --output")
        ap.print_help()
        sys.exit(1)
    if args.id_file is not None:
        ids = [x.strip() for x in args.id_file.readlines()]
    else:
        ids = [args.id_format.format(i) for i in range(args.id_start, args.id_end+1)]

    pdfmerge = PdfFileMerger()
    for id in tqdm(ids):
        if id == "." or id == "":
            continue
        pdfmerge.append(one_page(id, template=args.template))
    pdfmerge.write(args.output)

if __name__ == "__main__":
    main()
