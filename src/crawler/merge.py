import json

files = [
    r"F:\SEG301\merge\tiki.jsonl",
    r"F:\SEG301\merge\lazada.jsonl",
    r"F:\SEG301\merge\cellphones.jsonl",
    r"F:\SEG301\merge\ebay.jsonl",
    r"F:\SEG301\merge\chotot.jsonl",
    r"F:\SEG301\merge\dienmayxanh.jsonl",
    r"F:\SEG301\merge\fptshop.jsonl",
]

FIELDS = [
    "platform",
    "product_id",
    "product_name",
    "price",
    "original_price",
    "discount_percent",
    "product_url",
    "image_url",
    "rating",
    "review_count",
    "category"
]

seen_keys = set()   # (platform, product_id)
output = []

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                item = json.loads(line)

                platform = item.get("platform", 0)
                product_id = item.get("product_id", 0)

                # bỏ dòng không có id
                if not product_id:
                    continue

                key = (platform, product_id)
                if key in seen_keys:
                    continue

                seen_keys.add(key)

                # Chuẩn hóa schema: thừa bỏ, thiếu = 0
                clean_item = {}
                for field in FIELDS:
                    value = item.get(field, 0)
                    clean_item[field] = value if value not in (None, "") else 0

                output.append(clean_item)

            except json.JSONDecodeError:
                continue

with open(r"F:\SEG301\merge\data_1tr_raw.jsonl", "w", encoding="utf-8") as f:
    for item in output:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("✅ Merge xong:", len(output))
