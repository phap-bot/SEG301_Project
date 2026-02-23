# Giải Thích Cơ Chế Xếp Hạng Tìm Kiếm (Ranking)

Hệ thống sử dụng sự kết hợp giữa thuật toán tìm kiếm văn bản cổ điển (**BM25**) và các quy tắc nghiệp vụ (**Re-ranking**) để đảm bảo kết quả chính xác nhất.

## 1. Thuật toán Gốc: BM25 (Best Matching 25)
Đây là "trái tim" của hệ thống, được sử dụng để lấy ra 200 ứng cử viên đầu tiên:
- **TF (Term Frequency)**: Từ khóa xuất hiện càng nhiều lần trong tên sản phẩm thì điểm càng cao.
- **IDF (Inverse Document Frequency)**: Những từ khóa mang tính định danh (ví dụ: `16`, `Pro`, `Max`) có giá trị cao hơn những từ chung chung (ví dụ: `điện_thoại`).
- **Document Length**: Ưu tiên những tên sản phẩm ngắn gọn chứa từ khóa (độ tập trung cao).

## 2. Cơ chế Re-ranking (Tái sắp xếp thông minh)
Sau khi có top 200 từ BM25, hệ thống áp dụng các "bộ lọc" để tinh chỉnh thứ tự:

### A. Khớp Cụm Từ (Exact Phrase Match) - **Boost x3.0**
- Nếu người dùng tìm `iPhone 16`, những sản phẩm có đúng cụm `iPhone 16` đứng cạnh nhau sẽ được nhân 3 lần điểm.
- Giúp phân biệt rõ giữa máy máy chính chủ và các tin đăng rao vặt lung tung.

### B. Nhận diện Ý Định (Intent Recognition)
- **Phân biệt Model vs Dung lượng**: Hệ thống nhận diện các đơn vị (`GB`, `TB`).
    - Nếu query là `16` (số đơn thuần) -> Coi là Model máy.
    - Nếu kết quả trả về `16GB` -> Bị coi là nhầm lẫn và bị **giảm 60% điểm**.
- **Lọc Phụ Kiện (Accessory Filter)**: Tự động phát hiện các từ `ốp`, `sạc`, `pin`, `cáp`...
    - Nếu query không có từ phụ kiện -> Các sản phẩm này bị **giảm 95% điểm** (biến mất khỏi Top 10).

### C. Ưu tiên Vị trí & Độ phủ (Position & Coverage)
- **Vị trí đầu**: Từ khóa xuất hiện ở ngay đầu tên sản phẩm được **Boost x1.5**.
- **Độ phủ quan trọng**: Đếm số lượng từ khóa "hiếm" xuất hiện trong tên. Càng nhiều từ khóa đặc trưng thì điểm càng cao.

## 3. Ví dụ Minh họa
Khi bạn tìm: `điện thoại iphone 16`
1. **Tiềm năng**: Lấy ra iPhone 16, iPhone 16 Pro, Ốp iPhone 16, iPhone 6s 16GB.
2. **Xử lý**:
    - `iPhone 16 Pro`: Khớp cụm `iphone 16` -> **Đứng đầu**.
    - `Ốp iPhone 16`: Chứa từ `ốp` -> **Bị loại xuống cuối**.
    - `iPhone 6s 16GB`: `16` đi kèm `GB` -> **Bị trừ điểm nặng**, nhường chỗ cho model 16 thật sự.
