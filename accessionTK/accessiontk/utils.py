import csv

def load_csv(filename, *args, *kwargs):
    with open(filename) as fh:
        rdr = csv.DictReader(fh, *args, *kwargs)
        return list(rdr)
