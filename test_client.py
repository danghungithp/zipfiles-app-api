import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import io
import zipfile
import base64
import requests
import time
import subprocess
import os

API_URL = "http://127.0.0.1:5000"
API_KEY = "my-super-secret-powerautomate-key-2026"


def test_api():
    print(">>> 1. Kiểm tra Health Check...")
    r = requests.get(f"{API_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print("   [OK] Health check thành công:", r.json().get("message"))

    print("\n>>> 2. Kiểm tra chặn truy cập khi thiếu API Key...")
    r = requests.post(f"{API_URL}/api/zip", json={"files": []})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print("   [OK] Bị chặn đúng 401 khi không có X-API-Key:", r.json())

    print("\n>>> 3. Kiểm tra chặn truy cập khi API Key sai...")
    r = requests.post(
        f"{API_URL}/api/zip",
        headers={"X-API-Key": "wrong-key"},
        json={"files": []}
    )
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print("   [OK] Bị chặn đúng 403 khi sai X-API-Key:", r.json())

    print("\n>>> 4. Kiểm tra tạo ZIP trả về dạng Binary (mặc định)...")
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    # Chuẩn bị một file text và một file nhị phân (giả lập ảnh PNG 1x1 base64)
    sample_text = "Xin chào, đây là tài liệu từ Power Automate!"
    tiny_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    payload_binary = {
        "zip_name": "test_output.zip",
        "response_format": "binary",
        "files": [
            {
                "name": "documents/readme.txt",
                "content": sample_text,
                "is_base64": False
            },
            {
                "name": "images/pixel.png",
                "content": tiny_png_base64,
                "is_base64": True
            }
        ]
    }

    r = requests.post(f"{API_URL}/api/zip", headers=headers, json=payload_binary)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.headers.get("Content-Type") == "application/zip", f"Content-Type: {r.headers.get('Content-Type')}"

    # Đọc và giải nén zip từ r.content để kiểm tra
    zip_bytes = io.BytesIO(r.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        namelist = zf.namelist()
        print("   Danh sách file trong ZIP:", namelist)
        assert "documents/readme.txt" in namelist
        assert "images/pixel.png" in namelist

        txt_content = zf.read("documents/readme.txt").decode("utf-8")
        assert txt_content == sample_text
        print("   [OK] Nội dung file text giải nén chính xác:", txt_content)

    print("\n>>> 5. Kiểm tra tạo ZIP trả về dạng Base64 JSON...")
    payload_base64 = {
        "zip_name": "bundle_b64.zip",
        "response_format": "base64",
        "files": [
            {
                "name": "note.txt",
                "content": "Power Automate Base64 test",
                "is_base64": False
            }
        ]
    }
    r = requests.post(f"{API_URL}/api/zip", headers=headers, json=payload_base64)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    resp_data = r.json()
    assert resp_data["status"] == "success"
    assert "content_base64" in resp_data

    # Giải mã base64 và kiểm tra nội dung zip
    decoded_zip = base64.b64decode(resp_data["content_base64"])
    with zipfile.ZipFile(io.BytesIO(decoded_zip), "r") as zf:
        assert "note.txt" in zf.namelist()
        assert zf.read("note.txt").decode("utf-8") == "Power Automate Base64 test"
        print("   [OK] Base64 ZIP giải mã thành công! Kích thước:", resp_data["size_bytes"], "bytes")

    print("\n==========================================")
    print(" TOÀN BỘ CÁC BƯỚC TEST ĐỀU THÀNH CÔNG RỰC RỠ! ")
    print("==========================================")


if __name__ == "__main__":
    test_api()
