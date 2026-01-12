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
- ✅ User chọn Direct Copy approach
- ✅ Created SEG301-Project-GroupX structure
- ✅ Copied lazada_crawler vào src/crawler/lazada/

**Impact:** **High**  
- Đảm bảo code submission đúng format cho giáo viên
- Dễ dàng tích hợp code từ nhiều thành viên
- Clear attribution và credits

---

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
