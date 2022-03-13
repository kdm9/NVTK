#!/usr/bin/env python3
from labels import Specification, Sheet
from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import getFont, stringWidth
import qrcode
from tqdm import tqdm

import argparse
import sys

__all__ = [
        "label_types",
        "CryoLabel",
        "LCRY1700",
        "L7658",
        "L3667",
        "L7636",
        "generate_labels",
        "main",
]

class LabelSpec(object):
    hmargin = 1.5*mm
    hgap = 1*mm
    vmargin = 1.2*mm
    default_layout = "qr_left"
    layouts = ["qr_left", "qr_right"]

    def __init__(self, layout=None):
        self.spec = Specification(**self.page)
        if layout is None:
            layout = self.default_layout
        if layout not in self.layouts:
            raise ValueError(f"Invalid layout {layout}")
        self.layout = layout

    def qrimg(self, data):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=20,
            border=0
        )
        qr.add_data(str(data))
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")

    def fit_font(self, text, available_width, available_height):
        for font_size in range(self.font_size, 2, -1):
            twidth = stringWidth(text, self.font_name, font_size)
            if twidth > available_width:
                continue
            fnt = getFont(self.font_name).face
            textheight = (((fnt.ascent*font_size) -
                           (fnt.descent*font_size)) / 1000)
            if textheight > available_height:
                continue
            return font_size, twidth, textheight
        print("WARNING: couldn't fit", str(obj), "into", f"{tavail / mm:0.1f}", "mm space availabe")

    def make_label(self, label, width, height, obj, *args, **kwargs):
        text = str(obj)
        if text == "" or text == ".":
            return
        hm = self.hmargin       # horizontal margin
        vm = self.vmargin       # vertical margin
        hg = self.hgap          # inter-element gap
        ht = (height - 2*vm)    # Usable height
        wd = (width - 2*hm)     # Usable width
        qs = self.qrsize        # QRcode size
        if qs > ht:
            print(f"Scaling down QR size ({qs/mm:0.1f}mm) to available height ({ht/mm:0.1f}mm)")
            qs = ht
        assert ht <= height

        if self.layout == "qr_left":
            qleft = hm
            qbottom = vm + (ht - qs) / 2
            label.add(shapes.Image(qleft, qbottom, qs, qs, self.qrimg(obj)))

            tleft = qleft + qs + hg
            tavail = wd - tleft
            fsz, tw, th = self.fit_font(text, tavail, ht)
            tbottom = vm + (ht - th)/2
            label.add(shapes.String(tleft, tbottom, text, fontName=self.font_name, fontSize=fsz))
        elif self.layout == "qr_right":
            qleft = width - qs - hm
            qbottom = vm + (ht - qs) / 2
            label.add(shapes.Image(qleft, qbottom, qs, qs, self.qrimg(obj)))

            tright = qleft - hg
            tavail = tright - hm
            fsz, tw, th = self.fit_font(text, tavail, ht)
            tleft = tright - tw
            tbottom = vm + (ht - th)/2
            label.add(shapes.String(tleft, tbottom, text, fontName=self.font_name, fontSize=fsz))
        elif self.layout == "top_half":
            qs = qs/2
            ht = ht/2
            qleft = width - qs - hm
            qbottom = vm + ht + (ht - qs) / 2
            tright = qleft - hg
            tavail = tright - hm
            fsz, tw, th = self.fit_font(text, tavail, ht)
            tleft = tright - tw
            tbottom = vm + ht + (ht - th)/2
            hspace = width - (hm + tw + hg + qs + hm)
            qleft -= hspace/2
            tleft -= hspace/2
            label.add(shapes.Image(qleft, qbottom, qs, qs, self.qrimg(obj)))
            label.add(shapes.String(tleft, tbottom, text, fontName=self.font_name, fontSize=fsz))


class L7636(LabelSpec):
    description = "Mid-sized rounded rectangular labels (45x22mm) in sheets of 4x12"
    font_name = "Helvetica"
    font_size = 15
    name = "L7636"
    qrsize = 16*mm
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
    page = {
            "sheet_width": 210, "sheet_height": 297,
            "columns": 4, "rows": 16,
            "label_width": 48.5, "label_height": 16.9,
            "corner_radius": 0,
            "left_margin": 8, "top_margin": 13,
            "row_gap": 0, "column_gap": 0,
    }


class L3666(LabelSpec):
    description = "Mid-sized rectangular labels (38x22mm) in sheets of 5x13"
    font_name = "Helvetica"
    font_size = 12
    name = "L3666"
    qrsize = 13*mm
    layouts = ["qr_left", "qr_right", "top_half"]
    page = {
            "sheet_width": 210, "sheet_height": 297,
            "columns": 5, "rows": 13,
            "label_width": 38, "label_height": 21.2,
            "corner_radius": 0,
            "left_margin": 10, "top_margin": 10.7,
            "row_gap": 0, "column_gap": 0,
    }

class L7658(LabelSpec):
    description = "Small labels (25x10mm) in sheets of 7x27"
    font_name = "Helvetica"
    font_size = 11
    name = "L7658"
    qrsize = 7.5*mm
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
    font_size = 10
    name = "CryoLabel"
    qrsize = 9*mm
    hmargin = 2.5*mm
    vmargin = 2*mm
    layouts = ["qr_left", ]
    page = {
            "sheet_width": 210, "sheet_height": 297,
            "columns": 3, "rows": 18,
            "label_width": 63, "label_height": 15,
            "corner_radius": 1,
            "left_margin": 7, "top_margin": 21,
            "row_gap": 0, "column_gap": 3,
    }

class LCRY1700(LabelSpec):
    description = "Cryo Labels for screw-cap eppies."
    font_name = "Helvetica"
    font_size = 10
    name = "LCRY1700"
    qrsize = 8*mm
    hmargin = 1.8*mm
    vmargin = 1.8*mm
    layouts = ["qr_left", "qr_right"]
    page = {
            "sheet_width": 215, "sheet_height": 279,
            "columns": 5, "rows": 17,
            "label_width": 32.5, "label_height": 12.5,
            "corner_radius": 3,
            "left_margin": 19.5, "top_margin": 6.5,
            "row_gap": 3, "column_gap": 3.1,
    }


label_types = {
    "L7636": L7636,
    "L3667": L3667,
    "L3666": L3666,
    "L7658": L7658,
    "LCRY1700": LCRY1700,
    "CryoLabel": CryoLabel,
}


def generate_labels(labeltype, text_source, copies=1, border=True):
    sheet = Sheet(labeltype.spec, labeltype.make_label, border=border)
    for obj in tqdm(text_source):
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
    ap.add_argument("--layout", default=None,
            help="Label layout. See --list-label-types for a list of supported layouts per label type.")
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
    ap.add_argument("--border", action="store_true",
            help="Show a border around each label.")
    args = ap.parse_args()

    if args.demo is not None:
        for name, labelclass in label_types.items():
            sht = generate_labels(labelclass(), [f"{name}_{i}" for i in range(10)], copies=4)
            sht.save(f"{args.demo}/{name}.pdf")
        sys.exit(0)
    if args.list_label_types:
        for name, labelclass in label_types.items():
            print(f"{name}:  {labelclass.description} (supports layouts: {', '.join(labelclass.layouts)})")
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

    sht = generate_labels(label_types[args.label_type](layout=args.layout), ids, copies=args.copies, border=args.border)
    sht.save(args.output)


if __name__ == "__main__":
    main()
