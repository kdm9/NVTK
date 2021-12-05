#!/usr/bin/env python3
from labels import Specification, Sheet
from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import getFont, stringWidth
import qrencode

import argparse
import sys

__all__ = [
        "label_types",
        "CryoLabel",
        "L7658",
        "L3667",
        "L7636",
        "generate_labels",
        "main",
]

class LabelSpec(object):
    def __init__(self):
        self.spec = Specification(**self.page)

    def qrimg(self, data):
        qrv, qrs, qri = qrencode.encode(str(data), level=qrencode.QR_ECLEVEL_H,
                                        hint=qrencode.QR_MODE_8)
        return qri

    def qr_left(self, label, width, height, obj, *args, **kwargs):
        hm = self.hmargin       # horizontal margin
        vm = self.vmargin       # vertical margin
        ht = (height - 2*vm)    # Usable height
        wd = (width - 2*hm)     # Usable width
        qs = self.qrsize        # QRcode size
        assert qs <= ht
        assert ht <= height

        qleft = hm
        qbottom = vm + (ht - qs) / 2
        label.add(shapes.Image(qleft, qbottom, qs, qs, self.qrimg(obj)))

        tleft = qleft + qs + hm
        tavail = width - tleft - hm
        for font_size in range(self.font_size, 2, -1):
            twidth = stringWidth(str(obj), self.font_name, font_size)
            fnt = getFont(self.font_name).face
            textheight = (((fnt.ascent*font_size) -
                           (fnt.descent*font_size)) / 1000)
            if textheight > ht:
                continue
            tbottom = vm + (ht - textheight)/2
            if twidth < tavail:
                break
        else:
            print("WARNING: couldn't fit", str(obj), "into", f"{tavail / mm:0.1f}", "mm space availabe")
        label.add(shapes.String(tleft, tbottom, str(obj), fontName=self.font_name, fontSize=font_size))

class L7636(LabelSpec):
    description = "Mid-sized rounded rectangular labels (45x22mm) in sheets of 4x12"
    font_name = "Helvetica"
    font_size = 15
    name = "L7636"
    qrsize = 16*mm
    hmargin = 1.2*mm
    vmargin = 1.2*mm
    page = {
            "sheet_width": 210, "sheet_height": 297,
            "columns": 4, "rows": 12,
            "label_width": 45.7, "label_height": 21.2,
            "corner_radius": 2,
            "left_margin": 9, "top_margin": 21.5,
            "row_gap": 0, "column_gap": 3,
    }

class L3667(LabelSpec):
    description = "Mid-sized rectangular labels (48x17mm) in sheets of 4x16"
    font_name = "Helvetica"
    font_size = 12
    name = "L3667"
    qrsize = 13*mm
    hmargin = 1*mm
    vmargin = 1*mm
    page = {
            "sheet_width": 210, "sheet_height": 297,
            "columns": 4, "rows": 16,
            "label_width": 48.5, "label_height": 16.9,
            "corner_radius": 0,
            "left_margin": 7, "top_margin": 13,
            "row_gap": 0, "column_gap": 0,
    }

class L7658(LabelSpec):
    description = "Small labels (25x10mm) in sheets of 7x27"
    font_name = "Helvetica"
    font_size = 11
    name = "L7658"
    qrsize = 8*mm
    hmargin = 1*mm
    vmargin = 1*mm
    page = {
            "sheet_width": 210, "sheet_height": 297,
            "columns": 7, "rows": 27,
            "label_width": 25.4, "label_height": 10,
            "corner_radius": 1,
            "left_margin": 8.5, "top_margin": 13,
            "row_gap": 0, "column_gap": 2.5,
    }

class CryoLabel(LabelSpec):
    description = "Cryo Labels for screw-cap eppies. White on left half, clear on right. 63mmx15mm in sheets of 3x18"
    font_name = "Helvetica"
    font_size = 12
    name = "CryoLabel"
    qrsize = 10*mm
    hmargin = 1*mm
    vmargin = 1*mm
    page = {
            "sheet_width": 210, "sheet_height": 297,
            "columns": 3, "rows": 18,
            "label_width": 63, "label_height": 15,
            "corner_radius": 1,
            "left_margin": 6.7, "top_margin": 20,
            "row_gap": 0, "column_gap": 3,
    }

label_types = {
    "L7636": L7636,
    "L3667": L3667,
    "L7658": L7658,
    "CryoLabel": CryoLabel,
}


def generate_labels(labeltype, text_source, copies=1, border=True):
    sheet = Sheet(labeltype.spec, labeltype.qr_left, border=border)
    for obj in text_source:
        sheet.add_label(obj, count=copies)
    return sheet 

def main():
    morehelp  = """
There are four modes of operation: two for your assistance, and two actually functional modes

To simply list the support Avery label types:

    labelmaker --list-label-types

To make a demo page of labels for each label type:

    labelmaker --demo OUTDIR

To actually do anything, you need one of the following:

    labelmaker --output labels.pdf --id-file file_of_ids.txt [--copies N]
    labelmaker --output labels.pdf --id-format 'KDM{:04d}' --id-start 1 --id-end 2000 [--copies N]
"""
    ap = argparse.ArgumentParser(epilog=morehelp, formatter_class=argparse.RawDescriptionHelpFormatter, prog="labelmaker")
    ap.add_argument("--demo", type=str, metavar="DIR",
            help="Write a demo (10 labels, four reps per label) for each label type to DIR.")
    ap.add_argument("--list-label-types", action="store_true",
            help="Write a list of label types.")
    ap.add_argument("--label-type", choices=list(label_types.keys()),
            help="Label type.")
    ap.add_argument("--copies", type=int, default=1, metavar="N",
            help="Create N copies of each label.")
    ap.add_argument("--output", type=argparse.FileType("wb"), metavar="FILE",
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

    if args.demo is not None:
        for name, labelclass in label_types.items():
            sht = generate_labels(labelclass(), [f"{name}_{i}" for i in range(10)], copies=4)
            sht.save(f"{args.demo}/{name}.pdf")
        sys.exit(0)
    if args.list_label_types:
        for name, labelclass in label_types.items():
            print(f"{name}:  {labelclass.description}")
        sys.exit(0)
    if args.label_type is None and args.id_file is None and args.output is None and args.id_format is None:
        ap.print_help()
        sys.exit(1)
    if args.label_type is None:
        print("ERROR: must give a valid label type to --label-type")
        ap.print_help()
        sys.exit(1)
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

    sht = generate_labels(label_types[args.label_type](), ids, copies=args.copies)
    sht.save(args.output)


if __name__ == "__main__":
    main()
