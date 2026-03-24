# Hướng Dẫn Chạy Backend Server - Price Comparison API

Tài liệu này hướng dẫn chi tiết cách thiết lập, cấu hình cơ sở dữ liệu và khởi chạy hệ thống backend server (FastAPI).

## 1. Yêu cầu hệ thống (Prerequisites)
- **Python:** Phiên bản 3.9 trở lên
- **MongoDB:** Đã cài đặt và đang chạy ở môi trường local hoặc có chuỗi kết nối (URI) tới Cluster (VD: MongoDB Atlas).

## 2. Cài đặt thư viện (Dependencies)

Nên sử dụng môi trường ảo (Virtual Environment) để tránh xung đột thư viện với hệ thống.

```bash
# Di chuyển vào thư mục backend hoặc thư mục gốc của project (SEG301_Project)
cd d:\Antigravity\SEG301\SEG301_Project

# Tạo môi trường ảo (tuỳ chọn)
python -m venv venv

# Kích hoạt môi trường ảo
# Trên Windows:
venv\Scripts\activate
# Trên Linux/macOS:
source venv/bin/activate

# Cài đặt các requirements
pip install -r src/ui/backend/requirements.txt
# (Hoặc sử dụng requirements.txt ở thư mục gốc của dự án nếu cần đầy đủ các thư viện khác)
```

## 3. Cấu hình Cơ sở dữ liệu và Môi trường (Configuration)

Hệ thống backend tự động định vị file `.env` ở **thư mục gốc của project** (ví dụ: `SEG301_Project/.env`). Hãy đảm bảo bạn đã tạo file này và cấu hình đúng.

Mở file `.env` (ở thư mục gốc) và cấu hình lại các thông số sau cho phù hợp:

```env
# --- CẤU HÌNH DATABASE (MONGODB) ---
# Trỏ đến MongoDB local (mặc định)
MONGODB_URI=mongodb://localhost:27017
# Tên Database
MONGODB_DB=seg301
# Tên Collection chứa thông tin sản phẩm
COLLECTION_PRODUCTS=products

# --- CẤU HÌNH LIÊN KẾT NGOÀI (SUPABASE) ---
SUPABASE_URL=https://[ID].supabase.co
SUPABASE_KEY=[Your_Supabase_Key_Here]
```

### **Danh sách các collection MongoDB sử dụng:**
Khi kết nối thành công, hệ thống backend sẽ tự động trỏ đến các collection bên trong Database `seg301`:
1. `products`: Chứa thông tin sản phẩm.
2. `vouchers`: Chứa mã giảm giá.
3. `search_logs`: Lưu log tìm kiếm của người dùng.
4. `profile_user_info`: Lưu thông tin hồ sơ tài khoản.
5. `user_tracking`: Lưu các hành vi tracking của người dùng (lịch sử xem, tương tác).

### **Cấu hình thuật toán xếp hạng (Ranking Index):**
Backend cần load thuật toán tìm kiếm (`BM25` và `Vector`). 
Hãy chắc chắn rằng bạn có sẵn thư mục `index/` đặt tại **thư mục gốc của project** (`SEG301_Project/index/`), bên trong chứa các file chỉ mục (indexes) được tạo ra từ trước.

## 4. Chạy Server (Running the server)

**Lưu ý quan trọng**: Lệnh khởi chạy server (uvicorn) phải được gọi từ **thư mục gốc của project** (tức là `SEG301_Project`), để code bên trong có thể đọc đúng các module Python (`src.ranking...`) và các file đường dẫn thiết lập (ví dụ tìm `.env` và `index/` ở thư mục hiện tại).

```bash
# Bước 1: Mở terminal, trỏ vị trí về thư mục gốc của project:
cd d:\Antigravity\SEG301\SEG301_Project

# Bước 2: Bật MongoDB (nếu bạn sử dụng local DB)
# - Trên Windows: Đảm bảo service MongoDB đang chạy (mở app "Services" -> tìm "MongoDB Server" -> Start)
# - Hoặc nếu dùng file thực thi: mongod --dbpath "D:\path\to\your\db_data"

# Bước 3: Chạy ứng dụng FastAPI bằng Uvicorn
uvicorn src.ui.backend.main:app --reload
```
(*Cờ `--reload` giúp server tự động load lại khi file source code có sự thay đổi, chỉ dùng trong môi trường dev.*)

## 5. Kiểm tra hệ thống (Testing the APIs)

Sau khi báo log thành công với những dòng tương tự:
```
INFO:     MongoDB connected successfully.
INFO:     Loading BM25 Index from ...
INFO:     Started server process [1234]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Bạn có thể truy cập qua trình duyệt:

- **Swagger UI (Danh sách các API tương tác trực tiếp):**
  [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc (Tài liệu API chi tiết dạng tĩnh):**
  [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 6. Lỗi thường gặp:

- **`ModuleNotFoundError: No module named 'src.ranking.bm25'`** hoặc tương tự:
  - Lỗi này xuất hiện nếu bạn chạy `uvicorn main:app` khi đang đứng trực tiếp trong thư mục `src/ui/backend`. Hãy lùi đường dẫn terminal lại thư mục gốc (`SEG301_Project`) và dùng lệnh `uvicorn src.ui.backend.main:app`.
- **`pymongo.errors.ServerSelectionTimeoutError`**:
  - Backend không thể kết nối đến MongoDB. Hãy kiểm tra lại `MONGODB_URI` trong file `.env` hoặc xem service MongoDB đã được khởi động chưa.
- **`Failed to load BM25 engine / Vector engine`**:
  - Hệ thống không thể truy xuất folder `index/`. Vui lòng rà soát xem folder `index/` có chứa file trọng số cũ hay không ở thư mục gốc.
