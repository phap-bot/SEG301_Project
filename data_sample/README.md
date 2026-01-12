# Data Sample

This folder contains sample data for testing purposes only.

## Files
- `lazada_sample.jsonl`: 100 sample products from Lazada

## Full Dataset
The complete dataset (~1M products, 500MB) is available on Google Drive:
📥 [Download Full Dataset](https://drive.google.com/...)

## Format
Each line is a JSON object with the following structure:
```json
{
  "platform": "lazada",
  "product_id": "123456",
  "name": "Product Name",
  "price": 1000000,
  "original_price": 1500000,
  "discount": 33,
  "url": "https://lazada.vn/...",
  "rating": 4.5,
  "reviews": 120
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
