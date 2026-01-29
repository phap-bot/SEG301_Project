# MILESTONE 1 REPORT: DATA ACQUISITION
**Course:** SEG301 - SEARCH ENGINES & INFORMATION RETRIEVAL
**Project:** E-Commerce Vertical Search Engine
**Team:** phap-bot/SEG301_Project
**Completion Date:** 2026-01-25
**Status:** COMPLETED
**Version:** 1.0

---

## 1. EXECUTIVE SUMMARY
Mục tiêu của Milestone 1 là xây dựng nền tảng dữ liệu cho máy tìm kiếm chuyên biệt với hơn 1.000.000 sản phẩm từ 7 nền tảng thương mại điện tử lớn. Chúng tôi đã hoàn thành việc thiết lập hệ thống Crawler đa luồng, xử lý dữ liệu sạch và chuẩn hóa schema.

**Key Achievements:**
- **1,028,126 documents** đã được thu thập và làm sạch (vượt mục tiêu 2.8%).
- **7 nền tảng thương mại điện tử:** Tiki, eBay, Chợ Tốt, Lazada, CellphoneS, Điện Máy Xanh, FPTShop.
- **99.39% data quality:** Chỉ 0.61% dữ liệu bị loại bỏ trong quá trình cleaning (6,340 docs removed).
- **24.4M tokens** được trích xuất với trung bình **23.76 tokens/document**.
- **Kỹ thuật nâng cao:** Triển khai Async/Multi-threading và cơ chế tự động xử lý Anti-bot.

---

## 2. THÀNH VIÊN NHÓM VÀ CÔNG VIỆC

| Họ tên | MSSV | Vai trò | Công việc thực hiện |
| :--- | :--- | :--- | :--- |
| **Nguyễn Lê Tấn Pháp** | QE190155 | Nhóm trưởng | Viết code crawl cho Lazada, Điện Máy Xanh, FPTShop |
| **Tô Thanh Hậu** | QE190039 | Thành viên | Viết code crawl cho Tiki, Chợ Tốt, eBay |
| **Nguyễn Hải Nam** | QE190027 | Thành viên | Viết code crawl cho Lazada, CellphoneS |

---

## 3. THỐNG KÊ DỮ LIỆU

### 3.1. Overall Metrics
- **Raw Documents Crawled:** 1,034,466
- **Cleaned Documents:** 1,028,126
- **Total Tokens Extracted:** 24,429,834
- **Average Tokens/Doc:** 23.76

### 3.2. Platform Distribution (1,028,126 docs)

| Platform | Số lượng | Tỉ lệ % |
| :--- | ---: | ---: |
| **Tiki** | 389,699 | 37.90% |
| **eBay** | 302,083 | 29.38% |
| **Chợ Tốt** | 249,146 | 24.23% |
| **Lazada** | 34,719 | 3.38% |
| **CellphoneS** | 31,059 | 3.02% |
| **Điện Máy Xanh** | 12,140 | 1.18% |
| **FPTShop** | 9,280 | 0.90% |

---

## 4. CÁCH THỨC THỰC HIỆN (KỸ THUẬT)

### 4.1. Công nghệ sử dụng

**Ngôn ngữ & Runtime:**
- **Python 3.8+**: Xử lý logic crawler, API integration, data cleaning
- **Node.js 18+**: Chạy Playwright cho các sàn phức tạp (Lazada, Điện Máy Xanh)

**Thư viện Crawling:**
- `aiohttp` & `asyncio`: Crawl bất đồng bộ cho Tiki, Chợ Tốt (tối ưu tốc độ)
- `Playwright` & `Selenium`: Giả lập trình duyệt, xử lý Javascript rendering
- `httpx`: HTTP client hiện đại với async support cho eBay
- `Requests`: API requests đơn giản cho FPTShop
- `BeautifulSoup4` & `lxml`: Parse HTML structure

**NLP & Text Processing:**
- `Underthesea`: Word segmentation cho tiếng Việt (tách từ chính xác)
- `Regex`: Loại bỏ HTML tags, emoji, ký tự đặc biệt
- **Text Cleaning Pipeline**: 
  - Remove HTML tags (`<script>`, `<style>`, etc.)
  - Remove UI noise texts ("opens in a new window", etc.)
  - Normalize whitespace và lowercase
  - Word segmentation với `underthesea`

**Data Storage & Tools:**
- `JSONL (JSON Lines)`: Format lưu trữ scalable, process được hàng triệu dòng
- `Git & GitHub`: Version control và collaboration
- **Concurrent Processing**: Semaphore, AsyncIO để tối ưu tốc độ

### 4.2. Data Processing Pipeline

```
┌─────────────────┐
│  7 Crawlers     │  → Raw JSONL files (1,034,466 docs)
│  (Individual)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  merge.py       │  → Merge + Deduplicate + Schema Standardization
│                 │     • Remove duplicates by (platform, product_id)
│                 │     • Standardize 11 fields schema
│                 │     • Handle missing values (null → 0)
└────────┬────────┘
         │
         ▼ data_1tr_raw.jsonl (1,034,466 docs)
         │
┌─────────────────┐
│  parser.py      │  → Clean + Tokenize + Platform Stats
│  (tokenizer.py) │     • Clean text (remove HTML, noise, emoji)
│                 │     • Word segmentation (underthesea)
│                 │     • Deduplicate by product_id
│                 │     • Platform distribution statistics
└────────┬────────┘
         │
         ▼ data_1tr_clean_tokenized.jsonl (1,028,126 docs)
```

**Key Steps:**

1. **Crawling Phase (Individual):**
   - Mỗi crawler thu thập dữ liệu từ platform tương ứng
   - Output: Raw JSONL files với schema đa dạng

2. **Merging Phase (`merge.py`):**
   - Gộp 7 files vào 1 file duy nhất
   - Loại bỏ duplicates theo `(platform, product_id)`
   - Chuẩn hóa schema thống nhất 11 trường
   - Xử lý missing values (null/empty → 0)

3. **Cleaning & Tokenization (`parser.py`):**
   - **Text Cleaning:**
     - Remove `<script>` và `<style>` tags
     - Remove UI noise ("opens in a new window or tab", etc.)
     - Normalize spaces và lowercase
   - **Word Segmentation:**
     - Sử dụng `underthesea` để tách từ tiếng Việt
     - Output: `segmented_text` và `tokens` array
   - **Deduplication:**
     - Loại bỏ duplicates dựa trên `product_id`
   - **Statistics:**
     - Log platform distribution
     - Track token count và average

### 4.3. Cách vượt qua các rào cản trên 7 nền tảng (Chi tiết trong ai_log.md)
Trong quá trình thực hiện, nhóm đã đối mặt với nhiều rào cản kỹ thuật khác nhau trên từng sàn và đã trực tiếp xử lý (đối chiếu nhật ký tại `ai_log.md`):

- **Lazada :** Xử lý bot detection cực gắt bằng cách viết logic phát hiện trang "Tìm kiếm không có kết quả". Khi gặp CAPTCHA, code tự động chuyển từ `headless` sang `visible` để giải mã, sau đó lưu Cookie và quay lại chạy ẩn.
- **Tiki :** Khắc phục lỗi 403 bằng cách khai thác hệ thống **API v2** nội bộ thay vì parse HTML. Nhóm đã xử lý việc lấy **x-guest-token** động và triển khai **Exponential Backoff** (đợi lâu dần khi bị chặn) để duy trì kết nối.
- **Chợ Tốt :** Xử lý lỗi 429 (Too Many Requests) bằng cách xoay vòng User-Agent và thêm **Jitter sleep** (nghỉ ngẫu nhiên). Nhóm cũng giải quyết vấn đề tin đăng bị trôi trang khi phân trang bằng cơ chế kiểm tra tỉ lệ trùng ID.
- **eBay :** Tối ưu bộ nhớ khi crawl hàng trăm nghìn item bằng cách quản lý `seen_ids` thông minh. Xử lý việc eBay đổi giao diện (A/B testing) làm mất Rating bằng các bộ Selector dự phòng (Fallback selectors).
- **Điện Máy Xanh :** Triển khai kiến trúc **Concurrent Deep Crawl**. Thay vì chỉ lấy dữ liệu ở trang danh sách, code sẽ mở song song nhiều tab để vào từng trang chi tiết lấy số lượng đánh giá chuẩn xác nhất.
- **FPTShop :** Nâng cấp từ crawl trình duyệt sang **Direct API request** giúp tốc độ tăng gấp nhiều lần và dữ liệu chính xác hơn, tránh được các lỗi render giao diện.
- **CellphoneS :** Khắc phục lỗi lấy thiếu ảnh và giá do cơ chế **Lazy Loading**. Code được tinh chỉnh để tìm link ảnh thật trong các thuộc tính ẩn như `data-src` hoặc `data-ks-lazyload`.

---

## 5. DATA SCHEMA

### 5.1. Unified JSON Structure
```json
{
  "platform": "tiki",
  "product_id": "123456789",
  "product_name": "iPhone 15 Pro Max 256GB",
  "price": 29990000,
  "original_price": 34990000,
  "discount_percent": 14,
  "product_url": "https://tiki.vn/...",
  "image_url": "https://img.tiki.vn/...",
  "rating": 4.8,
  "review_count": 1234,
  "category": "Điện thoại",
}
```

### 5.2. Field Descriptions
| Field | Type | Description | Nullable |
| :--- | :--- | :--- | :--- |
| `platform` | String | Tên nền tảng (tiki, lazada, eBay, Chotot, cellphones, DienMayXanh, FPTShop) | No |
| `product_id` | String | ID duy nhất của sản phẩm trên platform | No |
| `product_name`| String | Tên sản phẩm | No |
| `price` | Float | Giá hiện tại (VND) | No |
| `original_price`| Float | Giá gốc trước khi giảm | Yes |
| `discount_percent`| Integer| % giảm giá (0-100) | Yes |
| `product_url` | String | Link trực tiếp sản phẩm | No |
| `image_url` | String | Link ảnh sản phẩm | No |
| `rating` | Float | Đánh giá trung bình (0-5) | No |
| `review_count`| Integer | Số lượng đánh giá | No |
| `category` | String | Danh mục sản phẩm | No |
| `segmented_text` | String | Text đã tách từ tiếng Việt | No |
| `tokens` | Array | Danh sách tokens sau khi word segmentation | No |

---

## 6. NHỮNG KHÓ KHĂN VÀ GIẢI PHÁP CHI TIẾT
Trong 4 tuần thực hiện, nhóm đã vượt qua 5 khó khăn lớn nhất:

- **Khó khăn 1: Chặn truy cập (Rate Limit/403/429):**
  - *Vấn đề:* Tiki và Chợ Tốt khóa IP sau vài trăm request.
  - *Giải pháp:* Nhóm đã cài đặt `Semaphore` để giới hạn số luồng chạy đồng thời (vừa đủ nhanh vừa không bị khóa). Kết hợp với việc lấy Token khách (`X-Guest-Token`) để "giả" là người dùng thật đang xem web.
- **Khó khăn 2: Tràn bộ nhớ RAM:**
  - *Vấn đề:* Khi gộp 1 triệu sản phẩm, nếu nạp tất cả vào RAM máy sẽ bị treo ngay lập tức.
  - *Giải pháp:* Nhóm sử dụng định dạng `JSONL` và cơ chế đọc file theo từng dòng (`generator`). Chỉ nạp ID sản phẩm vào `set()` để kiểm tra trùng, giúp tiết kiệm RAM tối đa.
- **Khó khăn 3: Dữ liệu "ảo" & Sai lệch giá:**
  - *Vấn đề:* Lazada thường hiển thị khoảng giá (30k - 100k) hoặc giá ảo.
  - *Giải pháp:* Nhóm đã nâng cấp crawler thành "Deep Crawl" - đi sâu vào trang chi tiết để lấy chính xác giá cuối cùng người dùng phải trả và số lượng đánh giá thực tế.
- **Khó khăn 4: Ảnh sản phẩm bị lỗi (Lazy Loading):**
  - *Vấn đề:* Nhiều ảnh sản phẩm khi crawl về chỉ là file rác (`base64` hoặc ảnh trống) do web chưa kịp load.
  - *Giải pháp:* Viết thêm đoạn code chờ (`wait_until`) và lấy link ảnh từ các thuộc tính chứa link thật như `data-src` thay vì thuộc tính `src` thông thường.
- **Khó khăn 5: Token tiếng Việt không chuẩn:**
  - *Vấn đề:* Các tên sản phẩm có nhiều Teencode hoặc từ tiếng Anh đan xen (ví dụ: "iPhone 15 pro max").
  - *Giải pháp:* Tinh chỉnh cấu hình của `Underthesea` và thêm các bộ lọc loại bỏ Teencode trước khi tách từ, giúp dữ liệu sạch và chuyên nghiệp hơn.

---

## 7. KẾT LUẬN

Milestone 1 đã hoàn thành xuất sắc với **1,028,126 documents** từ 7 nền tảng thương mại điện tử. 

**Highlights:**
- ✅ Vượt mục tiêu 1 triệu documents (102.8%)
- ✅ Data quality cao (99.39% retention rate)
- ✅ 24.4M tokens với avg 23.76 tokens/doc
- ✅ Schema chuẩn hóa hoàn chỉnh

---

**Người viết báo cáo:** Nhóm phap-bot/SEG301_Project  
**Ngày hoàn thành:** 29/01/2026  
