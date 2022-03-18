from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont
from PIL.ExifTags import TAGS, GPSTAGS
from pyzbar.pyzbar import decode, ZBarSymbol
from tqdm import tqdm
import cv2
import numpy as np

import argparse
from sys import stderr
from concurrent.futures import as_completed, ProcessPoolExecutor
from pathlib import Path
DEBUG=False


def write_on_image(image, text):
    image = image.copy()
    font = ImageFont.load_default()
    bottom_margin = 3   # bottom margin for text
    text_height = font.getsize(text)[1] + bottom_margin
    left, top = (5, image.size[1] - text_height)
    text_width = font.getsize(text)[0]
    locus = np.asarray(image.crop((left, top, left + text_width, top + text_height)))
    meancol = tuple(list(locus.mean(axis=(0,1)).astype(int)))
    opposite = (int(locus.mean()) + 96)
    if opposite > 255:
        opposite = (int(locus.mean()) - 96)
    oppositegrey = (opposite, ) * 3
    draw = ImageDraw.Draw(image)
    draw.rectangle((left-3, top-3, left + text_width + 3, top + text_height + 3),
                   fill=meancol)
    draw.text((left, top), text, fill=oppositegrey, font=font)
    return image


def scale_image(image, scalar=None, h=None):
    x, y = image.size
    if scalar is None:
        if h is None:
            raise ValueError("give either h or scalar")
        scalar = 1 if h > y else h/y
    return image.resize((int(round(x*scalar)), int(round(y*scalar))))

class KImage(object):
    def __init__(self, filename):
        self.image = Image.open(filename)
        self.filename = Path(filename)

class Decoder(object):
    def __init__(self):
        pass

    def preprocess(self, image):
        return image

    def decode(self, image):
        return None

    def __call__(self, image):
        image = self.preprocess(image)
        return image, self.decode(image)
    

class ZbarDecoder(Decoder):
    name = "pyzbar"

    def decode(self, image):
        qrcode = None
        codes = decode(image, [ZBarSymbol.QRCODE,])
        return [d.data.decode('utf8').strip() for d in codes]
        if len(codes) > 0:
            qrcode = ";".join(sorted([d.data.decode('utf8').strip() for d in codes]))
        return qrcode


class ScaledZbarDecoder(ZbarDecoder):
    def __init__(self, scale):
        self.scale = scale
        self.name = f"scaled_pyzbar_{scale}"

    def preprocess(self, image):
        image2 = scale_image(image, scalar=self.scale)
        return image2


class CLAHEZbarDecoder(ZbarDecoder):
    name = "CLAHE-normalised_pyzbar"
    def preprocess(self, image):
        cvim = np.array(ImageOps.grayscale(image))
        clahe = cv2.createCLAHE()
        clahe_im = clahe.apply(cvim)
        cv2.imshow("clahe", clahe_im)
        return Image.fromarray(clahe_im)

class ScaledCLAHEZbarDecoder(ScaledZbarDecoder):
    def __init__(self, scale):
        self.name = f"CLAHE-normalised_scaled_{scale}_pyzbar"
        self.scale=scale

    def preprocess(self, image):
        image = ScaledZbarDecoder.preprocess(self, image)
        image = CLAHEZbarDecoder.preprocess(self, image)
        return image


class AutoScaledZbarDecoder(ZbarDecoder):
    name = "autoscaled_pyzbar"

    def decode(self, image):
        for scalar in [0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1]:
            image2 = scale_image(image, scalar=scalar)
            res = ZbarDecoder.decode(self, image2)
            if res is not None:
                return res


class RotatedZbarDecoder(Decoder):
    name = "rotated_pyzbar"

    def decode(self, image):
        qrcode = None
        for rot in range(10, 91, 10):
            imrot = image.rotate(rot, expand=1)
            res = ZbarDecoder.decode(self, imrot)
            if res is not None:
                return res


class TiledZbarDecoder(Decoder):
    name = "tiled_pyzbar"

    def decode(self, image):
        w, h = image.size
        orig = np.asarray(image)
        for x in range(5):
            tw = w/6
            l = int(x*tw)
            r = min(w, int(l + 2*tw))
            for y in range(5):
                th = h/6
                b = int(y*th)
                t = min(h, int(b + 2*th))
                crop = Image.fromarray(orig[l:r, b:t, :])
                crop.save(f"{x}X{y}.jpg")
                res = ZbarDecoder.decode(self, crop)
                if res is not None:
                    return res

class AutoZbarDecoder(ZbarDecoder):
    name = "auto_pyzbar"

    def decode(self, image):
        for scalar in [0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1]:
            image2 = scale_image(image, scalar=scalar)
            res = ZbarDecoder.decode(self, image2)
            if res is not None:
                return res
            image3 = ImageOps.autocontrast(image2)
            res = ZbarDecoder.decode(self, image3)
            if res is not None:
                return res

class AutoWithContrastZbarDecoder(ZbarDecoder):
    name = "auto_contrast_pyzbar"

    def decode(self, image):
        barcodes = set()
        for scalar in [0.1, 0.2, 0.5, 1]:
            image2 = scale_image(image, scalar=scalar)
            res = ZbarDecoder.decode(self, image2)
            if DEBUG:
                m = f"scaled {scalar}: {res}"
                print(m)
                image2 = write_on_image(image2, m)
                image2.save(f"debug/{Path(image.filename).name}_scale_{scalar}.jpg")
            if res is not None:
                for barcode in res:
                    barcodes.add(barcode)
                break
            #image3 = ImageOps.autocontrast(image2)
            #res = ZbarDecoder.decode(self, image3)
            #if DEBUG:
            #    m = f"scaled {scalar} + autocontrast: {res}"
            #    print(m)
            #    image3 = write_on_image(image3, m)
            #    image3.save(f"debug/{Path(image.filename).name}_scale_{scalar}_autocontrast.jpg")
            #if res is not None:
            #    for barcode in res:
            #        barcodes.add(barcode)
            for sharpness in [2, 0.5, 4]:
                sharpener = ImageEnhance.Sharpness(image2)
                image4 = sharpener.enhance(sharpness)
                res = ZbarDecoder.decode(self, image4)
                if DEBUG:
                    m = f"scaled {scalar} + sharpen {sharpness}: {res}"
                    print(m)
                    image4 = write_on_image(image4, m)
                    image4.save(f"debug/{Path(image.filename).name}_scale_{scalar}_sharpness_{sharpness}.jpg")
                if res is not None:
                    for barcode in res:
                        barcodes.add(barcode)
                    break
        return barcodes


all_scanners = [
    ZbarDecoder(),
    #CLAHEZbarDecoder(),
    #AutoScaledZbarDecoder(),
    #RotatedZbarDecoder(),
    #TiledZbarDecoder(),
    #AutoZbarDecoder(),
    AutoWithContrastZbarDecoder(),
]



def do_one(scanner, image):
    image = KImage(image)
    res = scanner(image.image)
    return {"result": res[1],
            "scanner": scanner.name,
            "image": image.filename,
            #"pixels": res[0],
            }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--threads", type=int, default=None,
            help="Number of CPUs to use for image decoding/scanning")
    ap.add_argument("images", nargs="+", help="List of images")
    args = ap.parse_args()

    jobs = set()
    with ProcessPoolExecutor(args.threads) as exc:
        for image in args.images:
            for scanner in all_scanners:
                jobs.add(exc.submit(do_one, scanner, image))
    finished = []
    for fut in tqdm(as_completed(jobs), desc="Scanning", total=len(jobs)):
        finished.append(fut.result())
    
    print("Scanner", "Image", "Result", sep="\t")
    for res in finished:
        barcodes = ";".join(sorted(res["result"]))
        print(res["scanner"], res["image"], barcodes, sep="\t")


if __name__ == "__main__":
    main()
