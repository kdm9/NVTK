# QR Magic

Some magical semi-automated tools to better handle sample tracking during fieldwork.

To install:

```
python3 -m pip install qrmagic
```

Or, to get the development version:
```
python3 -m pip install -e git+https://github.com/kdm9/NVTK.git
```

## QR Code Label Printing

Make a PDF of labels for each sample ID. There are a few hard-coded "Avery" label
types commonly used in the Weigel group, and it's super easy to add others
(please create a github issue if you need help doing so, or want me to build a
new label type into the code).


```bash
$ python3 -m qrmagic.labelmaker --help
usage: labelmaker.py [-h] [--demo DIR] [--list-label-types] [--label-type TYPE] [--copies N]
                     [--output FILE] [--id-file FILE] [--id-format FORMAT] [--id-start N] [--id-end N]

optional arguments:
  -h, --help            show this help message and exit
  --demo DIR            Write a demo (10 labels, four reps per label) for each label type to DIR.
  --list-label-types    Write a list of label types.
  --label-type TYPE     Label type.
  --copies N            Create N copies of each label.
  --output FILE         Output PDF file.
  --id-file FILE        File of IDs, one per line.
  --id-format FORMAT    Python-style format string governing ID format e.g. WGL{:04d} gives WGL0001..WGL9999
  --id-start N          First ID number (default 1)
  --id-end N            Last ID number (default 100)
```

To see what label types are available, do:

```bash
$ python3 -m qrmagic.labelmaker --list-label-types
L7636:  Mid-sized rounded rectangular labels (45x22mm) in sheets of 4x12
L3667:  Mid-sized rectangular labels (48x17mm) in sheets of 4x16
L7658:  Small labels (25x10mm) in sheets of 7x27
CryoLabel:  Cryo Labels for screw-cap eppies. White on left half, clear on right.
```

One can also create a demonstration PDF for each label type with the command:

```bash
$ python3 -m qrmagic.labelmaker --demo output_dir/
```

## QR Code-based Image organisation

So, we took all these photos in the field, now what do we do with them? The first step is to organise them by sample. To do so manually is cumbersome, so here are some tools to help.

### Step 1: scan images on your machine

This CLI tool will scan your images, doing its best to decode all the QRcodes
they contain. For each image it also reports the location and time the image
was taken, and various other bits of metadata.

NB: for silly javascript reasons, you need to have all images be in a single
directory. If you have your images organised in directories (e.g. by date, or
by camera), please run this process once per directory, or move or symlink all
images into a single directory.

```
qrmagic-detect -o my-images.json my-images/*.JPG
```


### Step 2: curation

Now, go to <https://qrmagic.kdmurray.id.au/imagesort.html>. Here, you should
upload the JSON file created above, and up will pop a table of images. You can
then try automatically filling missing barcodes based on the adjacent codes
(always do a bit of manual curation here), or manually type in QR codes that
are not detectable. When you are finished, you can download a Bash script which
contains commands to rename all your files by sample ID (or whatever your
barcodes denote).


### Step 3: rename images

Once downloaded, the renamer script should be run in the same directory your
images are all in:

```
cd /path/to/my-images
bash -x ~/Downloads/rename.sh
```
