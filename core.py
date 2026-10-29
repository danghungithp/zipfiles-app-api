import os
import io
import zipfile
import base64
import hmac
from functools import wraps
from flask import request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY", "my-super-secret-powerautomate-key-2026")


def require_api_key(f):
    """Decorator kiểm tra Header X-API-Key để xác thực yêu cầu."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        received_key = request.headers.get("X-API-Key")
        if not received_key:
            return jsonify({
                "status": "error",
                "message": "Không tìm thấy X-API-Key trong Request Header."
            }), 401

        if not hmac.compare_digest(received_key, API_KEY):
            return jsonify({
                "status": "error",
                "message": "API Key không hợp lệ."
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def sanitize_filename(filename: str) -> str:
    """Làm sạch tên file để tránh Zip Slip vulnerability."""
    clean = filename.replace("\\", "/")
    parts = [part for part in clean.split("/") if part and part != ".."]
    return "/".join(parts) if parts else "unnamed_file"


def create_zip_from_request(req):
    """Hàm xử lý tạo ZIP dùng chung cho cả Local lẫn Vercel Serverless."""
    data = req.get_json(silent=True)
    if not data or "files" not in data or not isinstance(data["files"], list):
        return jsonify({
            "status": "error",
            "message": "Trường 'files' là bắt buộc và phải là mảng danh sách file trong body JSON."
        }), 400

    files = data["files"]
    if len(files) == 0:
        return jsonify({
            "status": "error",
            "message": "Danh sách 'files' không được để trống."
        }), 400

    zip_name = data.get("zip_name", "archive.zip")
    if not zip_name.endswith(".zip"):
        zip_name += ".zip"

    response_format = data.get("response_format", "binary").lower()
    memory_zip = io.BytesIO()

    try:
        with zipfile.ZipFile(memory_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for index, item in enumerate(files):
                if not isinstance(item, dict):
                    return jsonify({
                        "status": "error",
                        "message": f"Phần tử thứ {index} không hợp lệ."
                    }), 400

                file_name = item.get("name", f"file_{index + 1}.txt")
                safe_name = sanitize_filename(file_name)
                content = item.get("content", "")
                is_base64 = item.get("is_base64", False)

                if is_base64:
                    try:
                        if isinstance(content, str) and "," in content and "base64" in content.split(",")[0]:
                            content = content.split(",", 1)[1]
                        file_bytes = base64.b64decode(content)
                    except Exception as b64_err:
                        return jsonify({
                            "status": "error",
                            "message": f"Không thể giải mã base64 cho '{safe_name}': {str(b64_err)}"
                        }), 400
                else:
                    if isinstance(content, str):
                        file_bytes = content.encode("utf-8")
                    elif isinstance(content, bytes):
                        file_bytes = content
                    else:
                        file_bytes = str(content).encode("utf-8")

                zf.writestr(safe_name, file_bytes)

        memory_zip.seek(0)

        if response_format == "base64":
            zip_b64 = base64.b64encode(memory_zip.getvalue()).decode("utf-8")
            return jsonify({
                "status": "success",
                "zip_name": zip_name,
                "content_base64": zip_b64,
                "size_bytes": len(memory_zip.getvalue()),
                "total_files": len(files)
            }), 200

        return Response(
            memory_zip.getvalue(),
            mimetype="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_name}"',
                "Content-Type": "application/zip"
            }
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi trong quá trình tạo file ZIP: {str(e)}"
        }), 500

