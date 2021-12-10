from accessiontk.utils import load_csv
import jinja2

j2env = jinja2.Environment(
        loader = jinja2.PackageLoader("accessiontk.htmlmap")
)


config = {
    "title": "Omnidopsis",
    "variable_map": {
        "id": "oa_id",
        "lat": "latitude",
        "lng": "longitude",
        "species": "species",
    },
}


def output(basedir, config, sampledata):





