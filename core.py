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
    """Hàm xử lý tạo ZIP linh hoạt, tự động tương thích với các định dạng output từ Power Automate."""
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

                # 1. Tìm tên file (chấp nhận cả name, Name, filename, fileName, FileLeafRef, {FilenameWithExtension})
                file_name = None
                for name_key in ["name", "Name", "filename", "fileName", "FileName", "FileLeafRef", "{FilenameWithExtension}", "DisplayName"]:
                    val = item.get(name_key)
                    if val and str(val).strip():
                        file_name = str(val).strip()
                        break
                
                if not file_name:
                    file_name = f"file_{index + 1}.txt"

                safe_name = sanitize_filename(file_name)

                # 2. Tìm nội dung file (chấp nhận content, Content, fileContent, body, $content)
                raw_content = None
                for content_key in ["content", "Content", "fileContent", "FileContent", "body", "Body", "$content"]:
                    if content_key in item and item[content_key] is not None:
                        raw_content = item[content_key]
                        break

                # Nếu Power Automate truyền nguyên body('Get_file_content') dạng object: {"$content-type": "...", "$content": "..."}
                if isinstance(raw_content, dict):
                    raw_content = raw_content.get("$content") or raw_content.get("content") or ""

                if raw_content is None:
                    raw_content = ""

                # 3. Nhận diện is_base64 linh hoạt (boolean true, hoặc string "true", "True")
                is_b64_raw = None
                for b64_key in ["is_base64", "isBase64", "Is_base64", "IsBase64"]:
                    if b64_key in item:
                        is_b64_raw = item[b64_key]
                        break

                is_base64 = False
                if isinstance(is_b64_raw, bool):
                    is_base64 = is_b64_raw
                elif isinstance(is_b64_raw, str):
                    is_base64 = is_b64_raw.strip().lower() in ["true", "1", "yes"]
                elif is_b64_raw is None:
                    # Tự động phỏng đoán nếu là chuỗi base64 dài
                    if isinstance(raw_content, str) and len(raw_content) > 100 and not raw_content.startswith("<"):
                        is_base64 = True

                # Chuyển đổi dữ liệu thành bytes
                if is_base64:
                    try:
                        clean_b64 = raw_content
                        if isinstance(clean_b64, str) and "," in clean_b64 and "base64" in clean_b64.split(",")[0]:
                            clean_b64 = clean_b64.split(",", 1)[1]
                        file_bytes = base64.b64decode(clean_b64)
                    except Exception:
                        file_bytes = raw_content.encode("utf-8") if isinstance(raw_content, str) else bytes(raw_content)
                else:
                    if isinstance(raw_content, str):
                        file_bytes = raw_content.encode("utf-8")
                    elif isinstance(raw_content, bytes):
                        file_bytes = raw_content
                    else:
                        file_bytes = str(raw_content).encode("utf-8")

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
