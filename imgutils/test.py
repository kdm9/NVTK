#!/usr/bin/env python3
import os
import json
from shlex import quote

with open("test.json") as fh:
    dat = json.load(fh)

def qfn(f):
    return quote(f["filename"])

for key, files in dat.items():
    if len(files) > 1:
        other_files = []
        best_file = None
        files.sort(key = lambda x: (len(x["filename"]), x["filename"]))
        for file in files:
            if best_file is None:
                best_file = file
            elif (file["datetime"] is not None and best_file["datetime"] is None or
                 file["lat"] is not None and best_file["lat"] is None or
                 file["lon"] is not None and best_file["lon"] is None):
                other_files.append(best_file)
                best_file = file
            else:
                other_files.append(file)
        print(f"mkdir -p best-images/;  ln -s {qfn(best_file)} best-images/")
        for file in other_files:
            print(f"mkdir -p duplicate-images/{key}/; ln -s {qfn(file)} duplicate-images/{key}/")
        #os.system("lximage-qt " + quote(best_file["filename"]) + " " + " ".join(quote(x["filename"]) for x in other_files))
    else:
        print(f"mkdir -p best-images/;  ln -s {qfn(files[0])} best-images/")
