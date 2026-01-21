# utils.py
import os
import json

# ================== CONFIG ==================
KEYWORDS = [
    "iPhone 16", "Samsung Galaxy S24 Ultra", "MacBook Air M3",
    # (giữ nguyên danh sách của bạn)
]

MAX_PAGE = 500
OUTPUT_FILE = r"C:\FPT\SEG301\tiki\tiki_products.jsonl"

SORTS = {
    "default": "",
    "newest": "newest",
    "price_asc": "price,asc",
    "price_desc": "price,desc"
}

# ================== LOAD EXISTING IDS ==================
def load_existing_ids():
    ids = set()
    if not os.path.exists(OUTPUT_FILE):
        return ids

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "product_id" in obj:
                    ids.add(str(obj["product_id"]))
            except:
                pass
    return ids
