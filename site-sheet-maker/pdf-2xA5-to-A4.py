#!/usr/bin/env python3
from PyPDF2 import PdfFileWriter, PdfFileReader
import sys
import math


def main():
    if (len(sys.argv) != 3):
        print("usage: python 2-up.py input_file output_file")
        sys.exit(1)
    print ("2-up input " + sys.argv[1])
    input1 = PdfFileReader(open(sys.argv[1], "rb"))
    output = PdfFileWriter()

    assert input1.getNumPages() % 2 == 0
    half = int(input1.getNumPages() /  2)
    for iter in range (0, half, 1):
        lhs = input1.getPage(iter)
        rhs = input1.getPage(iter+half)
        lhs.mergeTranslatedPage(rhs, lhs.mediaBox.getUpperRight_x(),0, True)
        output.addPage(lhs)
        print(str(iter) + " ", end="")
        sys.stdout.flush()
    print()

    print("writing " + sys.argv[2])
    outputStream = open(sys.argv[2], "wb")
    output.write(outputStream)
    outputStream.close()
    print("done.")

if __name__ == "__main__":
    main()
