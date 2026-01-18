# AI Usage Log - SEG301 Project

> [!NOTE]
> This log tracks all AI tool usage across the team for transparency and academic integrity.

---

## 2026-01-12

### Phap - Lazada Bot Detection Fix
**Task:** Fix Lazada crawler bot detection - phát hiện trang "Tìm kiếm không có kết quả" và tự động chuyển browser mode  
**AI Tool:** Google Gemini Advanced  

**Prompts:**
1. "hey check xem sao code tôi nó hiển thị captcha mà ko báo cho tôi"
2. "Phát hiện trang 'Tìm kiếm không có kết quả' - bot detection"  
3. "Tự động chuyển browser từ headless sang visible khi phát hiện captcha"
4. "Giảm timeout từ 90s xuống 60s"

**Code Generated:**
- `src/crawler/lazada/src/crawlers/lazada.js` lines 286-407
  - Bot detection logic phát hiện "Tìm kiếm không có kết quả"
  - Auto-switch headless ↔ visible mode
  - Cookie save/load after CAPTCHA solved
  
**Review & Modifications:**
- ✅ Tested successfully với Lazada crawler
- ✅ Phát hiện được bot detection page (không chỉ CAPTCHA URL)
- ✅ Tự động mở browser visible để user giải CAPTCHA
- ✅ Lưu cookies và quay lại headless mode sau khi xác thực
- ✅ Giảm timeout từ 90s → 60s theo yêu cầu

**Impact:** **Critical**  
- Cho phép crawler bypass bot detection tự động
- Giảm thiểu manual intervention
- Tăng success rate từ ~30% lên ~85%

---

### Phap - GitHub Repository Structure Planning
**Task:** Tổ chức lại repository theo yêu cầu giáo viên SEG301  
**AI Tool:** Google Gemini Advanced

**Prompts:**
1. "Phân phối folder như nào cho phù hợp với yêu cầu giáo viên mà code không bị lộn xộn"
2. "Xử lý nhiều crawler từ nhiều thành viên khác nhau"
3. "Chọn cách 2: Direct Copy"

**Deliverables:**
- Implementation plan với 3 scenarios (Submodule, Direct Copy, Mix)
- README.md template với team credits table
- .gitignore chuẩn cho Python + Node.js project
- ai_log.md format template
- Folder structure theo template giáo viên

**Review & Modifications:**
-  User chọn Direct Copy approach
-  Created SEG301-Project-GroupX structure
-  Copied lazada_crawler vào src/crawler/lazada/

**Impact:** **High**  
- Đảm bảo code submission đúng format cho giáo viên
- Dễ dàng tích hợp code từ nhiều thành viên
- Clear attribution và credits

## 2026-01-13

### Hau – Tiki Crawling Troubleshooting
**Task:** Crawl dữ liệu sản phẩm từ sàn Tiki và xử lý các vấn đề liên quan đến dynamic content, API bảo vệ và rate limiting.  
**AI Tool:** ChatGPT (GPT-4 / GPT-4o)

**Prompts:**
1. "Viết code Python dùng thư viện requests để gọi API lấy danh sách sản phẩm Tiki thay vì parse HTML."
2. "Thêm các headers giả lập trình duyệt (User-Agent, Referer, x-guest-token) vào request để không bị block."
3. "Bổ sung vòng lặp phân trang (page, limit) và tự động sleep ngẫu nhiên để tránh lỗi HTTP 429."

**Code Generated:**
- `src/crawler/tiki/tiki_api_crawler.py`
  - Chuyển logic từ parse HTML sang gọi API JSON nội bộ
  - Thiết lập custom headers (User-Agent, x-guest-token) mô phỏng browser
  - Logic phân trang sử dụng tham số `page` và `limit`

**Review & Modifications:**
- Điều chỉnh lại bộ headers sau khi test thực tế để bypass filter
- Thêm cơ chế retry và backoff (tăng thời gian chờ) khi gặp lỗi HTTP 429
- Test thành công dữ liệu trả về trên nhiều category khác nhau

**Impact:** **High**  
- Crawl dữ liệu ổn định hơn so với Selenium, giảm nguy cơ bị bot detection
- Dữ liệu nhận về dạng JSON có cấu trúc, giảm chi phí xử lý hậu kỳ

---

### Hau – Chợ Tốt Crawling Troubleshooting
**Task:** Crawl dữ liệu tin đăng từ Chợ Tốt và xử lý các vấn đề liên quan đến API thay đổi, thiếu field và bot detection.  
**AI Tool:** ChatGPT (GPT-4 / GPT-4o)

**Prompts:**
1. "Viết script Python gọi trực tiếp endpoint API của Chợ Tốt để lấy danh sách tin đăng."
2. "Thêm logic random delay từ 2-5 giây và xoay vòng User-Agent để tránh bị phát hiện là bot."
3. "Xử lý dữ liệu JSON trả về, lọc bỏ các field bị null và lưu kết quả."

**Code Generated:**
- `src/crawler/chotot/chotot_api_crawler.py`
  - Logic crawl dữ liệu trực tiếp từ API endpoint đã reverse engineering
  - Tích hợp random delay và User-Agent rotation
  - Hàm validate schema response để xử lý các field bị null

**Review & Modifications:**
- Điều chỉnh params API riêng biệt cho từng category (Bất động sản, Xe cộ...)
- Loại bỏ các field không ổn định khỏi data schema
- Test chạy ổn định trong thời gian dài (long-running)

**Impact:** **High**  
- Tốc độ crawl nhanh và nhẹ hơn Selenium, giảm nguy cơ bị block IP
- Đảm bảo dữ liệu sạch và đồng nhất cho các bước xử lý tiếp theo

## Template cho log mới:

### [Tên] - [Task Title]
**Task:** [Mô tả ngắn gọn task]  
**AI Tool:** [ChatGPT/Gemini/Claude/Copilot/...]  

**Prompts:**
1. "[Prompt 1]"
2. "[Prompt 2]"

**Code Generated:**
- `[file path]` lines [X-Y]: [Mô tả ngắn gọn]

**Review & Modifications:**
- [ ] Code cần sửa gì (nếu có)
- [x] Đã test và hoạt động tốt

**Impact:** [Low / Medium / High / Critical]  
[Giải thích impact]

---

## Guidelines

**Khi nào cần log:**
- Sử dụng AI để generate/debug code
- Sử dụng AI để brainstorm ideas
- Sử dụng AI để research solutions

**Không cần log:**
- Google search thông thường
- Đọc documentation
- Code tự viết 100% không có AI assistance

**Format prompts:**
- Ghi chính xác prompts đã dùng (hoặc tóm tắt nếu quá dài)
- Có thể ghi bằng tiếng Việt hoặc tiếng Anh tùy prompt gốc
