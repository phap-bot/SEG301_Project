<img width="1376" height="770" alt="image" src="https://github.com/user-attachments/assets/55245c45-6eb9-48ed-ba95-af53fe74674e" />
<img width="860" height="2002" alt="image" src="https://github.com/user-attachments/assets/d7c687b2-8927-4429-b5fd-94e9473c380d" />

# Báo cáo kết quả Milestone 3: Hệ thống Tìm kiếm Hybrid (Hybrid Search System)

Báo cáo này trình bày chi tiết về kết quả phát triển hệ thống tìm kiếm cho Milestone 3. Tất cả các nội dung dưới đây đều phản ánh chính xác 100% các logic, thuật toán, và cấu trúc luồng dữ liệu đã được **code và áp dụng trực tiếp vào dự án**. Không có khái niệm hay tính năng nào được liệt kê nếu chưa có trên source code thật.

---

## 1. Tổng quan kiến trúc hệ thống tìm kiếm
- **Kiến trúc API:** Hệ thống sử dụng FastAPI làm backend kết nối trực tiếp với Database MongoDB (Collection `products`, `vouchers`, `search_logs`).
- **Phân loại tìm kiếm:** Hệ thống chia làm 3 chức năng chính được hỗ trợ thông qua query parameter `search_type`:
  - `bm25`: Tìm kiếm theo từ khóa (Lexical Search).
  - `vector`: Tìm kiếm theo ngữ nghĩa (Semantic Search).
  - `hybrid`: Tìm kiếm kết hợp (Kết hợp cả hai phương pháp).

---

## 2. Chi tiết các thành phần tìm kiếm đã code và triển khai

### 2.1. Cỗ máy tìm kiếm theo từ khóa cơ bản (BM25 Engine)
- **Tệp mã nguồn:** `src/ranking/bm25.py`
- **Tính năng và Thuật toán thực tế:**
  - **Công thức tính điểm cơ bản:** Tự triển khai bằng code thuần công thức BM25 (với tham số $k_1 = 2.0$ và $b = 0.8$) kết hợp với TF-IDF.
  - **Tách từ (Tokenization) cho Tiếng Việt:** Kéo thư viện `underthesea` (hàm `word_tokenize`) để phân tích cú pháp truy vấn tiếng Việt. Code tích hợp thêm phương pháp quy hoạch động (dynamic programming) trong hàm `_split_stuck_word_dynamic()` để rã các cụm từ bị dính liền/không dấu.
  - **Xử lý ngôn ngữ (Normalization):** Tất cả truy vấn được chuẩn hóa dạng Unicode NFC/NFD, lower-case, bỏ dấu câu và giữ nguyên cấu trúc từ ghép (underscore `_`).
  - **Bảng băm Inverted Index:** Tại thời điểm chạy, thuật toán load dữ liệu Inverted Index được lưu cứng ở dạng Dictionary của python (đọc từ file `inverted_index.pkl` để tối ưu tốc độ hoặc json dự phòng).
  - **Thuật toán Smart Reranking (Xếp hạng lại thông minh):** Sau khi tính điểm cơ bản lấy 200 doc cao điểm nhất (`raw_top`), thuật toán tự cộng/trừ điểm (boost score) nếu từ khóa xuất hiện nguyên vẹn trong tên sản phẩm `product_name`, ưu tiên vị trí từ khóa xuất hiện ở đầu câu, và phạt (penalty) nếu các từ này bị spam quá nhiều trong tiêu đề. 

### 2.2. Cỗ máy tìm kiếm Semantic (Vector Engine)
- **Tệp mã nguồn:** `src/ranking/vector.py`
- **Tính năng và Thuật toán thực tế:**
  - **Mô hình Embedding:** Máy chiếu vector sử dụng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Biến đổi mọi string thành vector tĩnh n-chiều.
  - **Tìm kiếm không gian:** Dùng thư viện `faiss` của Facebook. Khởi chạy load trực tiếp khối dữ liệu `vector_index.faiss` lên RAM để query.
  - **Đo lường điểm số (Score Mapping):** Do FAISS đo theo khoảng cách L2 (càng nhỏ càng tốt), trong khi BM25 đo tỉ lệ tương đồng (càng lớn càng tốt). Ở đây code map ngược L2 distance thành tỷ lệ Similarity thuận qua công thức: `score = 1.0 / (1.0 + dist)` để quy chuẩn hóa. Sau đó map ngược với `vector_doc_mapping.pkl` để lấy ID tương ứng.

### 2.3. Cỗ máy tìm kiếm kết hợp (Hybrid Ranker)
- **Tệp mã nguồn:** `src/ranking/hybrid.py`
- **Tính năng và Thuật toán thực tế:**
  - **Phương pháp Reciprocal Rank Fusion (RRF):** Vì hệ tham chiếu điểm số của BM25 và Vector là khác biệt, không thể cộng trực tiếp. Thuật toán xử lý bằng cách lấy 2 List top doc từ hai engine trên, sau đó xếp hạng dựa trên vị trí ưu tiên thay vì điểm số.
  - Công thức RRF trong hàm `search()`: `RRF Score = 1 / (60 + rank)` (với `rank` là thứ hạng của sản phẩm trong BM25 hoặc Vector). Sau đó gộp mảng và cộng điểm RRF cho các sản phẩm xuất hiện trong cả hai tập kết quả để ra dãy kết quả đồng bộ chung.

---

## 3. Quy trình Mapping, Lọc dữ liệu và tích hợp API
- **Tệp mã nguồn:** `src/ui/backend/routers/search_v1.py` và `main.py`
- **Tối ưu RAM (Lifespan):** Khi Server FastAPI start (tại `lifespan`), Index của BM25 và Faiss Vector được Load đè trực tiếp lên RAM 1 lần duy nhất, giải quyết vấn đề nghẽn cổ chai IO. 
- **Quy trình kết nối qua API (`/api/v1/search`):**
  1. API nhận Query kèm Pagination, filter về Giá (`min_price`, `max_price`), nền tảng (`platforms`), và loại tìm kiếm.
  2. Truy vấn Query xuống Ranker tương ứng và fetch giới hạn về chính xác **top 200 ID tiềm năng nhất**.
  3. Lọc ID Map dưới CSDL (Mongodb Queries): Build truy vấn `$in` lấy document JSON cho đúng các ID đó trong Database `products`. Kèm theo các điều kiện truy vấn `$gte`, `$lte` filter giá cả nếu Frontend có truyền vào.
  4. Sắp xếp tái cấu trúc: Vì dữ liệu Query ra từ MongoDB không đảm bảo được thứ hạng giống Ranker trả về. Code thiết lập `relevance_map` để lưu chỉ mục gốc, dùng hàm `sorted()` của Python sắp xếp lại các Doc lấy từ DB về đúng vị trí từ Ranker, tiếp theo mới cắt list array (pagination) và trả object Response về cho Frontend render ra bảng kết quả cuối.

## 4. Ghi chú log tìm kiếm (Search Logging)
- **Tính năng mở rộng tại API:** Mỗi lần truy vấn gửi tới `/api/v1/search`, sau khi phản hồi trả về thành công, một Background Task bất đồng bộ (Async Background Tasks) sẽ gom toàn bộ Top 10 ID được tìm thấy bởi cả BM25, Vector và Hybrid, đẩy ngược và insert xuống MongoDB ở collection `search_logs` cùng query text và user ID để lưu trữ đánh giá thuật toán sau này.
