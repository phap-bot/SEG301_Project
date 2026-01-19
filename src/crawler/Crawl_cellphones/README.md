# CellphoneS GraphQL API Crawler

Crawler sản phẩm từ **CellphoneS.com.vn** sử dụng GraphQL API công khai.

## ⚡ Features

- **Fast**: Sử dụng GraphQL API trực tiếp (không cần Playwright/Selenium)
- **Efficient**: Nhẹ, chỉ cần Node.js và node-fetch
- **Flexible**: Crawl theo keyword hoặc category
- **Deduplication**: Tự động loại bỏ sản phẩm trùng lặp (theo `product_id`)
- **Single File Output**: Tất cả keywords gộp vào 1 file JSONL duy nhất
- **JSONL Format**: Lưu dữ liệu theo format JSONL chuẩn

## 📦 Installation

```bash
npm install
```

## 🚀 Usage

### Run crawler với config mặc định:

```bash
npm start
```

### Hoặc:

```bash
node crawl_cellphones.js
```

### Config

Mở file `crawl_cellphones.js` và chỉnh sửa:

```javascript
const config = {
  keywords: ['điện thoại', 'laptop', 'tai nghe'],  // Danh sách keywords
  maxPages: 5,                                       // Giới hạn số pages (hoặc Infinity)
  delayMs: 1000,                                    // Delay giữa requests (ms)
  province: 30                                       // 30=HCM, 1=Hanoi
};
```

## 📁 Output

Dữ liệu được lưu trong folder `output/` với format:

```
cellphones_dien_thoai_2026-01-13T20-45-00.jsonl
cellphones_laptop_2026-01-13T20-45-30.jsonl
```

### JSONL Format

Mỗi dòng là một JSON object:

```json
{"platform":"cellphones","product_id":"123456","product_name":"iPhone 16 Pro Max","price":32990000.0,"original_price":34990000.0,"discount_percent":6,"product_url":"https://cellphones.com.vn/iphone-16-pro-max.html","image_url":"https://cdn.cellphones.com.vn/...","rating":4.8,"review_count":152,"category":"điện thoại"}
```

## 🔧 API Details

- **Endpoint**: `https://api.cellphones.com.vn/graphql-search/v2/graphql/query`
- **Method**: POST
- **Type**: GraphQL
- **Authentication**: Public (không cần token)

## 📊 Performance

- **Speed**: ~0.5-1s per page (so với 5-10s của Playwright)
- **Resource**: Rất nhẹ (~50MB RAM)
- **Rate Limit**: 1s delay giữa các requests (có thể điều chỉnh)

## 🛠️ Troubleshooting

### Lỗi "Cannot find module 'node-fetch'"

```bash
npm install
```

### API trả về error 403

Tăng delay giữa các requests trong config:

```javascript
delayMs: 2000  // 2 seconds
```

## 📝 Notes

- Crawler sử dụng ES6 modules (`type: "module"` trong package.json)
- Output files được tự động đặt tên với timestamp
- Mỗi keyword được crawl riêng và lưu vào file riêng

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
