# Copyright 2021-2022  Kevin Murray, MPI Biologie Tübingen
# Copyright 2021-2022  Gekkonid Consulting
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from flask import Flask, request, abort, jsonify, send_from_directory, current_app, redirect, send_file

from .scanimages import ImgData, dataURI_to_file
from . import labelmaker
from io import BytesIO
import re

app = Flask("qrmagic")

app.config.from_prefixed_env("QRMAGIC_")
if app.config.get("USE_WHITENOISE", False):
    from whitenoise import WhiteNoise
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')
from whitenoise import WhiteNoise
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

@app.route("/")
def redir_index():
    return redirect("/index.html", 301)


@app.route("/api/scan-image", methods=["POST"])
def scan_image():
    jsondat = json.loads(request.data)
    img = ImgData(filename = jsondat.get("filename"), data = dataURI_to_file(jsondat.get("content")))
    return jsonify(img.as_response_json()), 201


@app.route("/api/labeltypes.json", methods=["GET"])
def labeltypes():
    return jsonify(labelmaker.labeltype_json), 201


@app.route("/api/labels_pdf", methods=["POST"])
def labels_pdf():
    jsondat = json.loads(request.data)
    if jsondat.get("ids_txt"):
        ids = [x.strip() for x in re.split(r"[\t\n]+", jsondat.get("ids_txt").rstrip())]
    else:
        ids = [jsondat["id_format"].format(i) for i in range(int(jsondat.get("id_start", 1)), int(jsondat.get("id_end", 100))+1)]

    labelclass = labelmaker.label_types[jsondat.get("label_type", "L3666")]

    sht = labelmaker.generate_labels(labelclass(layout=jsondat.get("layout"), line_delim=","), ids, copies=jsondat.get("copies", 1), border=jsondat.get("border", False))
    pdf = BytesIO()
    sht.save(pdf)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name="labels.pdf", max_age=0.1)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
