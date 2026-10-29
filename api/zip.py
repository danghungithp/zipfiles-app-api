import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask, request
from core import create_zip_from_request, require_api_key

app = Flask(__name__)

@app.route("/", defaults={"path": ""}, methods=["POST"])
@app.route("/<path:path>", methods=["POST"])
@require_api_key
def handle_zip(path):
    return create_zip_from_request(request)

if __name__ == "__main__":
    app.run(port=5000)

