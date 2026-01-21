# Data Sample

This folder contains sample data for testing purposes only.

## Files
- `tiki_sample.jsonl`: 300 sample products from Lazada

## Format
Each line is a JSON object with the following structure:
```json
{
  "platform": "tiki",
  "product_id": "123456",
  "name": "Product Name",
  "price": 1000000,
  "original_price": 1500000,
  "discount": 33,
  "url": "https://lazada.vn/...",
  "image_url": "https://salt.tikicdn.com/cache/280x280/ts/product/f0/78/28/d9ea6dbfdd58e0ca1c3d75476aab47c8.jpg,
  "rating": 4.5,
  "reviews": 120
  "category": "Máy lọc không khí"
}
```

## Usage
```python
import json

# Read sample data
with open('data_sample/lazada_sample.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        product = json.loads(line)
        print(product['name'], product['price'])
```
