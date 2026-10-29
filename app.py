import os
from flask import Flask, request, jsonify
from core import create_zip_from_request, require_api_key

app = Flask(__name__)

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "ZIP Generator API đang hoạt động bình thường.",
        "endpoints": {
            "POST /api/zip": "Tạo file ZIP từ danh sách file (yêu cầu X-API-Key)"
        }
    }), 200

@app.route("/api/zip", methods=["POST"])
@require_api_key
def zip_endpoint():
    return create_zip_from_request(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"=== ZIP Generator API đang chạy trên http://{host}:{port} ===")
    app.run(host=host, port=port, debug=False)
