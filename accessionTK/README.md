# accessiontk

Tools to manage lists of accessions.


## webmap

Creates nice web maps using leaflet.js and vue.js. 

Usage:

1. Create a csv/tsv with the following columns (colnames flexible):

```csv
accession,location,datetime,lat,long,location_description
A1,L1,2022-01-01,48.4,2.2,"somebody's field"
```

2. Collect image data into a structure like


```bash
$ tree images/
images
├── A1
│   ├── 20220324120033.jpg
│   ├── 20220324120034.jpg
│   ├── 20220324120035.jpg
├── A2             
│   ├── 20220324120384.jpg
│   ├── 20220324120485.jpg
│   ├── 20220324120480.jpg
│   └── 20220324120539.jpg
└── L1
    ├── 20220324120871.jpg
    ├── 20220324120880.jpg
    ├── 20220324120821.jpg
    └── 20220324120857.jpg
```


3. Run `accessiontk-webmap`. Set the `--*-colname` arguments to match your metadata table, give `-i`, `-o`, and `-t`, and then run it. See `accessiontk-webmap --help` for info
