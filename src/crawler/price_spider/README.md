# Price Spider Crawler

**Platform:** Python-based web crawler  
**Description:** Thu thập dữ liệu giá sản phẩm từ các e-commerce platforms

## Files
- `main.py` - Main entry point
- `requirements.txt` - Python dependencies
- `crawler/` - Crawler modules
  - `cellphone_search.py` - Cellphone search crawler
- `data/` - Output data (CSV files)

## Setup

### Install dependencies
```bash
cd src/crawler/price_spider
pip install -r requirements.txt
```

### Run
```bash
python main.py
```

## Output
Data được lưu vào folder `data/`:
- `crawl_lazada.csv`
- `crawl_tiki.csv`
- `products.csv`

## Note
Crawler này sử dụng Selenium với ChromeDriver.
`chromedriver.exe` đã được include trong folder.
