# Lazada Crawler

**Author:** Phap  
**Platform:** Lazada Vietnam  
**Original Repo:** [phap-bot/SEG301_Project](https://github.com/phap-bot/SEG301_Project)

## Description
Node.js crawler for Lazada.vn với các tính năng:
- ✅ Anti-bot detection (auto-detect "Tìm kiếm không có kết quả" page)
- ✅ Auto-switch headless ↔ visible mode cho CAPTCHA
- ✅ Cookie persistence
- ✅ Web dashboard để monitor crawling progress
- ✅ SQLite database storage

## Setup

### Install dependencies
```bash
cd src/crawler/lazada
npm install
```

### Configure keywords
Edit `config.json`:
```json
{
  "keywords": [
    "Man hinh may tinh",
    "Laptop gaming"
  ]
}
```

## Run Crawler

### Command line
```bash
node index.js
```

### With web dashboard
```bash
npm run web
# Open http://localhost:3000
```

## Features

### Bot Detection
Tự động phát hiện:
- CAPTCHA pages (URL contains `punish` or `captcha`)
- "Tìm kiếm không có kết quả" page
- Tự động chuyển sang visible mode khi cần

### Cookie Management
- Lưu cookies sau mỗi request thành công
- Auto-load cookies khi khởi động
- Giúp giảm CAPTCHA rate

### Smart PDP Skip
Chỉ visit product detail page khi thiếu thông tin:
- Skip nếu có đủ: price, original_price, image, rating
- Visit PDP nếu thiếu data

## Database Schema
SQLite database: `products.db`

Table: `products`
- `platform`: "lazada"
- `site_product_id`: Product ID from Lazada
- `product_name`: Product name
- `price`: Current price
- `original_price`: Original price
- `discount_percent`: Discount percentage
- `product_url`: Product URL
- `image_url`: Product image
- `rating`: Product rating (0-5)
- `review_count`: Number of reviews
- `sold_count`: Sold count
- `location`: Seller location
- `category`: Product category

## Output
- **Database**: `products.db`
- **Debug Screenshot**: `debug_lazada_page.png` (when error occurs)
- **Cookies**: `.cookies/lazada_cookies.json`
- **Progress**: `progress.json`
