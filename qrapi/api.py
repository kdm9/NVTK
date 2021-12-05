import json
from flask import Flask, request, abort, jsonify, send_from_directory, current_app

from .scanimage import ImgData, dataURI_to_file

app = Flask("imgsorter")

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory('static', path)

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
