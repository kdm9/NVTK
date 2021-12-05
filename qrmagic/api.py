import json
from flask import Flask, request, abort, jsonify, send_from_directory, current_app
from whitenoise import WhiteNoise

from .scanimages import ImgData, dataURI_to_file
from .labelmaker import *

app = Flask("qrmagic")

app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

@app.route("/api/scan-image", methods=["POST"])
def scan_image():
    jsondat = json.loads(request.data)
    img = ImgData(dataURI_to_file(jsondat.get("content")))
    resp = {
        "filename": jsondat.get("filename"),
        "camera": img.camera,
        "datetime": img.datetime.isoformat(),
        "lat": img.lat,
        "lng": img.lon,
        "alt": img.alt,
        "midsize": img.midsize,
        "qrcodes": img.qrcode,
    }
    return jsonify(resp), 201

if __name__ == "__main__":
    app.run(debug=True, port=8000)
