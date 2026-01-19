# 📖 HƯỚNG DẪN SỬ DỤNG NHANH

## 🚀 Cách 1: Chạy Bằng Double-Click (Đơn Giản Nhất)

1. **Double-click vào file** [`run_crawler.bat`](file:///c:/Nam%20dep%20trai/CODE/SEG/SUPER%20SEG/Crawl_cellphones/run_crawler.bat)
2. Chờ crawler chạy xong
3. Xem kết quả trong folder `output/`

✅ Xong! Không cần gõ lệnh gì cả.

---

## ⚙️ Cách 2: Thêm/Sửa Keywords

### Bước 1: Mở file config

Mở file [`crawl_cellphones.js`](file:///c:/Nam%20dep%20trai/CODE/SEG/SUPER%20SEG/Crawl_cellphones/crawl_cellphones.js)

### Bước 2: Tìm phần config (dòng ~18)

```javascript
const config = {
  keywords: [
    'iphone',       // ⬅️ THÊM/XÓA KEYWORDS TẠI ĐÂY
    'samsung',
    'laptop',
    'tai nghe'
  ],
  maxPages: 5,     // Số pages cho mỗi keyword
  delayMs: 1000,   // Delay giữa requests (ms)
  province: 30     // 30=HCM, 1=Hanoi
};
```

### Bước 3: Thêm keywords mới

**Ví dụ:**
```javascript
keywords: [
  'iphone',
  'samsung galaxy',
  'macbook',
  'ipad pro',
  'airpods'
],
```

### Bước 4: Lưu file và chạy lại

Double-click `run_crawler.bat` hoặc:
```bash
npm start
```

---

## 📁 Kết Quả Output

Sau khi chạy, file JSONL sẽ được lưu tại:

```
output/
├── cellphones_iphone_2026-01-13T13-50-05.jsonl
├── cellphones_samsung_2026-01-13T13-52-30.jsonl
└── cellphones_laptop_2026-01-13T13-55-12.jsonl
```

### Format JSONL

Mỗi dòng là một sản phẩm:

```json
{"platform":"cellphones","product_id":"112588","product_name":"iPhone 16 Pro Max","price":37690000.0,"original_price":37990000.0,"discount_percent":1,"product_url":"https://cellphones.com.vn/iphone-16-pro-max.html","image_url":"https://...","rating":0,"review_count":0,"category":"iphone"}
```

---

## 🎛️ Tùy Chỉnh Nâng Cao

### Thay đổi số pages crawl

```javascript
maxPages: 10,        // Crawl 10 pages
// hoặc
maxPages: Infinity,  // Crawl HẾT tất cả pages
```

### Thay đổi tốc độ crawl

```javascript
delayMs: 500,   // Nhanh hơn (0.5s)
delayMs: 2000,  // Chậm hơn (2s) - ít bị block hơn
```

### Đổi địa điểm

```javascript
province: 1,   // Hanoi
province: 30,  // HCM
```

---

## ❓ Troubleshooting

### Lỗi "Cannot find module 'node-fetch'"

**Giải pháp:**
```bash
npm install
```

### Crawler chạy quá nhanh bị block

**Giải pháp:** Tăng `delayMs`:
```javascript
delayMs: 2000,  // 2 giây
```

### Muốn crawl nhiều hơn

**Giải pháp:** Tăng `maxPages`:
```javascript
maxPages: 20,  // hoặc Infinity
```

---

## 💡 Tips

- ✅ Test với `maxPages: 1` trước khi crawl hết
- ✅ Dùng keyword cụ thể: `'iphone 15'` thay vì `'điện thoại'`
- ✅ Kiểm tra file output trước khi crawl số lượng lớn
- ✅ Backup data định kỳ (file JSONL)

---

## 📞 Support

Gặp vấn đề? Check:
1. [`README.md`](file:///c:/Nam%20dep%20trai/CODE/SEG/SUPER%20SEG/Crawl_cellphones/README.md) - Documentation đầy đủ
2. File output trong `output/` folder
3. Log trên terminal/command prompt
