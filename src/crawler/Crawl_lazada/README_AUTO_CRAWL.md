# 📘 HƯỚNG DẪN SỬ DỤNG AUTO-CRAWL

## 🚀 Cách sử dụng

### Bước 1: Chỉnh sửa `config.json`

Mở file `config.json` và cấu hình theo nhu cầu:

```json
{
  "platform": "2",
  "delayBetweenKeywords": 10,
  "keywords": [
    "điện thoại",
    "laptop",
    "tai nghe bluetooth"
  ],
  "maxPages": 50
}
```

**Giải thích:**
- `platform`: `"1"` = Tiki, `"2"` = Lazada
- `delayBetweenKeywords`: Số giây nghỉ giữa các keyword (tránh bị phát hiện)
- `keywords`: Danh sách từ khóa muốn crawl
- `maxPages`: Số trang tối đa mỗi keyword (mặc định 50)

### Bước 2: Chạy crawler

```bash
node index.js
```

### Bước 3: Ngồi chờ kết quả 🍿

Code sẽ tự động:
- Crawl tất cả keywords trong list
- Tự dừng khi trang không còn sản phẩm
- Delay giữa các keyword để tránh bị phát hiện
- Tắt khi hoàn thành tất cả

---

## ✅ Tính năng mới

### 1. **Auto-Stop khi hết sản phẩm**
```
Trang 1: 40 sản phẩm ✅
Trang 2: 35 sản phẩm ✅
Trang 3: 0 sản phẩm ⚠️
→ Dừng crawl keyword này!
```

### 2. **Crawl nhiều keyword tự động**
```
[1/3] "điện thoại" → 50 trang
⏳ Đợi 10s...
[2/3] "laptop" → 50 trang
⏳ Đợi 10s...
[3/3] "tai nghe" → 50 trang
✅ Hoàn thành!
```

### 3. **Không cần nhập tay**
- Không còn readline prompts
- Tất cả config trong file JSON
- Chạy và quên đi!

---

## 🔧 Ví dụ config

### Crawl nhiều keywords với maxPages khác nhau

Nếu muốn mỗi keyword có số trang riêng, sửa lại structure:

```json
{
  "platform": "2",
  "delayBetweenKeywords": 10,
  "tasks": [
    { "keyword": "iphone 15 pro max", "maxPages": 30 },
    { "keyword": "samsung galaxy s24", "maxPages": 20 },
    { "keyword": "macbook m3", "maxPages": 15 }
  ]
}
```

*(Lưu ý: Cần sửa code một chút để support cấu trúc này)*

---

## 🎯 Tips

1. **Tránh bị ban:**
   - Đặt `delayBetweenKeywords` từ 10-30s
   - Không crawl quá nhiều trang liên tục

2. **Optimize:**
   - Kiểm tra keyword trước có bao nhiêu trang
   - Đặt `maxPages` vừa đủ, đừng quá cao

3. **Debug:**
   - Kiểm tra log để biết crawl đến đâu
   - Nếu lỗi, xem keyword nào bị fail
