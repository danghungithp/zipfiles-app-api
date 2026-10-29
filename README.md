# API Nén File ZIP bằng Python Flask (Đã Triển Khai Lên Vercel)

Dự án cung cấp một REST API chuẩn Serverless trên Vercel để tạo file ZIP từ danh sách file (hỗ trợ cả văn bản thường và file nhị phân Base64), xử lý nén hoàn toàn trên RAM (In-Memory), tích hợp sẵn lớp bảo mật `X-API-Key` để kết nối trực tiếp với **Power Automate qua HTTP Request**.

---

## 1. Thông tin Production trên Vercel

- **Production Domain**: `https://zipfiles-app-api.vercel.app`
- **Tạo file ZIP (POST)**: `https://zipfiles-app-api.vercel.app/api/zip`
- **Kiểm tra trạng thái (GET)**: `https://zipfiles-app-api.vercel.app/health`
- **API Key bảo mật mặc định**: `my-super-secret-powerautomate-key-2026` *(đã cấu hình trong biến môi trường Vercel `API_KEY`)*

---

## 2. Cấu trúc dự án trên Vercel

```text
zipfilesAppApi/
├── api/
│   ├── zip.py          # Serverless Function: Xử lý POST /api/zip
│   ├── health.py       # Serverless Function: Xử lý GET /api/health
│   └── index.py        # Serverless Function: Xử lý GET / và /api
├── core.py             # Logic lõi: nén ZIP in-memory, xác thực X-API-Key, chống Zip Slip
├── app.py              # File chạy local test
├── vercel.json         # Cấu hình routing rewrites cho Vercel
├── requirements.txt    # Danh sách thư viện (Flask, python-dotenv)
├── test_client.py      # Test script tự động
└── run_tests.py        # Test runner
```

---

## 3. Cấu hình Power Automate HTTP Request

### Bước 1: Action HTTP trong Flow
- **Method**: `POST`
- **URI**: `https://zipfiles-app-api.vercel.app/api/zip`
- **Headers**:
  ```http
  Content-Type: application/json
  X-API-Key: my-super-secret-powerautomate-key-2026
  ```
- **Body**:
  ```json
  {
    "zip_name": "BoTaiLieu_@{utcNow()}.zip",
    "response_format": "binary",
    "files": [
      {
        "name": "TaiLieu.pdf",
        "content": "@{body('Get_file_content')?['$content']}",
        "is_base64": true
      },
      {
        "name": "GhiChu.txt",
        "content": "Nội dung ghi chú xuất từ Power Automate",
        "is_base64": false
      }
    ]
  }
  ```

### Bước 2: Action Lưu File ZIP (OneDrive / SharePoint)
- **Action**: *Create file* (OneDrive for Business hoặc SharePoint).
- **File Name**: `KetQua.zip`.
- **File Content**: Chọn giá trị động **Body** từ action **HTTP**.
*(Vì API trả về header `Content-Type: application/zip`, Power Automate sẽ nhận diện trực tiếp luồng Binary và tạo file ZIP hợp lệ mà không cần giải mã).*

---

## 4. Cách cập nhật hoặc deploy lại lên Vercel
Nếu bạn chỉnh sửa mã nguồn và muốn đẩy bản mới lên:
```bash
vercel --prod --yes
```

Nếu muốn đổi `API_KEY` trên Vercel:
```bash
vercel env add API_KEY production --value "khoa-bi-mat-moi-cua-ban" --force --yes
vercel --prod --yes
```
