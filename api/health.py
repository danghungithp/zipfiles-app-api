import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", defaults={"path": ""}, methods=["GET"])
@app.route("/<path:path>", methods=["GET"])
def handle_health(path):
    return jsonify({
        "status": "success",
        "message": "ZIP Generator API đang hoạt động bình thường trên Vercel.",
        "endpoints": {
            "POST /api/zip": "Tạo file ZIP từ danh sách file (yêu cầu X-API-Key)"
        }
    }), 200

if __name__ == "__main__":
    app.run(port=5000)

