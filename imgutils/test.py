#!/usr/bin/env python3
import os
import json
from shlex import quote
from sys import stdin, stdout, stderr, argv

ENFORCE_SAME_CAM=True

with open(argv[1]) as fh:
    dat = json.load(fh)

def qfn(f):
    return quote(f["filename"])

def dictdiff(a, b):
    keys = set(list(a.keys()) + list(b.keys()))
    for key in keys:
        A = a.get(key, "MISSING")
        B = b.get(key, "MISSING")
        if A != B:
            print(f"   a[{key}]={A}, b[{key}]={B}", file=stderr)

class DoubleBreak(Exception):
    pass

for key, files in dat.items():
    try:
        if len(files) > 1:
            other_files = []
            best_file = None
            files.sort(key = lambda x: (len(x["filename"]), x["filename"]))
            for file in files:
                if best_file is None:
                    best_file = file
                elif any(best_file[x] is not None and file[x] is not None and best_file[x] != file[x]
                         for x in ["datetime", "lat", "lon", "alt", "camera"]):
                    print(f"mismatch in metadata between files (key: {key}):", file=stderr)
                    dictdiff(best_file, file)
                    other_files.append(file)
                    seen_shas = set()
                    for file2 in files:
                        if file2["sha1"] in seen_shas:
                            continue
                        print(f"mkdir -p strange-clusters/{key}/; ln -s {qfn(file2)} strange-clusters/{key}/")
                        seen_shas.add(file2["sha1"])
                    raise DoubleBreak()
                elif (file["width"] > best_file["width"] or 
                      file["datetime"] is not None and best_file["datetime"] is None or
                      file["lat"] is not None and best_file["lat"] is None or
                      file["lon"] is not None and best_file["lon"] is None):
                    other_files.append(best_file)
                    best_file = file
                else:
                    other_files.append(file)
            print(f"mkdir -p simple-clusters/best-images/;  ln -s {qfn(best_file)} simple-clusters/best-images/")
            for file in other_files:
                print(f"mkdir -p simple-clusters/duplicate-images/{key}/; ln -s {qfn(file)} simple-clusters/duplicate-images/{key}/")
            #os.system("lximage-qt " + quote(best_file["filename"]) + " " + " ".join(quote(x["filename"]) for x in other_files))
        else:
            print(f"mkdir -p single-images/best-images/;  ln -s {qfn(files[0])} single-images/best-images/")
    except DoubleBreak:
        continue
