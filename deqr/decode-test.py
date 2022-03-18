from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont
from pyzbar.pyzbar import decode, ZBarSymbol
from tqdm import tqdm
import cv2
import numpy as np

import argparse
from sys import stderr
import multiprocessing as mp
from pathlib import Path
from time import time
DEBUG=False


class KImage(object):
    def __init__(self, filename):
        self.image = Image.open(filename)
        self.filename = Path(filename).name

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
    if scalar == 1:
        return image
    x, y = image.size
    if scalar is None:
        if h is None:
            raise ValueError("give either h or scalar")
        scalar = 1 if h > y else h/y
    return image.resize((int(round(x*scalar)), int(round(y*scalar))))


def qrdecode(image):
    codes = decode(image, [ZBarSymbol.QRCODE,])
    return list(sorted(d.data.decode('utf8').strip() for d in codes))


def normalise_CLAHE(image):
    cvim = np.array(ImageOps.grayscale(image))
    clahe = cv2.createCLAHE()
    clahe_im = clahe.apply(cvim)
    #cv2.imshow("clahe", clahe_im)
    return Image.fromarray(clahe_im)


def rotate(image, rot=30):
    return image.copy().rotate(rot, expand=1)


def autocontrast(image):
    return ImageOps.autocontrast(image)


def sharpen(image, amount=1):
    sharpener = ImageEnhance.Sharpness(image)
    return sharpener.enhance(amount)


def do_one(image):
    image = KImage(image)
    l = time()
    def tick():
        nonlocal l
        n = time()
        t = n - l
        l = n
        return t

    union = set()
    total_t = 0
    results = []
    for scalar in [0.1, 0.2, 0.5, 1]:
        tick()
        image_scaled = scale_image(image.image, scalar=scalar)
        st = tick()
        res = qrdecode(image_scaled)
        union.update(res); total_t += st
        results.append({"file": image.filename,
                        "what": f"scaled-{scalar}",
                        "result": res,
                        "time": st})

        tick()
        image_scaled_autocontrast = autocontrast(image_scaled)
        t = tick()
        res = qrdecode(image_scaled_autocontrast)
        union.update(res); total_t += st + t
        results.append({"file": image.filename,
                        "what": f"scaled-{scalar}_autocontrast",
                        "result": res,
                        "time": t + st})
                   
        for sharpness in [0.5, 0.1, 2]:
            tick()
            image_scaled_sharp = sharpen(image_scaled, sharpness)
            t = tick()
            res = qrdecode(image_scaled_sharp)
            union.update(res); total_t += st + t
            results.append({"file": image.filename,
                            "what": f"scaled-{scalar}_sharpen-{sharpness}",
                            "result": res,
                            "time": t + st})
    results.append({"file": image.filename,
                    "what": f"do-all-the-things",
                    "result": list(union),
                    "time": total_t})
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--threads", type=int, default=None,
            help="Number of CPUs to use for image decoding/scanning")
    ap.add_argument("images", nargs="+", help="List of images")
    args = ap.parse_args()

    pool = mp.Pool(args.threads)

    print("Scanner", "Image", "Result", "Time", sep="\t")
    for image_results in tqdm(pool.imap(do_one, args.images), unit="images", total=len(args.images)):
        for result in image_results:
            barcodes = ";".join(sorted(result["result"]))
            print(result["what"], result["file"], barcodes, result["time"], sep="\t")


if __name__ == "__main__":
    main()
