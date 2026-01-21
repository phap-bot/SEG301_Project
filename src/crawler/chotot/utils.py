# utils.py
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "chotot_realtime.jsonl")

LIMIT = 50
MAX_PAGE = 1000
SLEEP_TIME = 0.3
STOP_IF_NO_NEW = 20

def load_seen_ids(path=OUTPUT_FILE):
    seen = set()
    if not os.path.exists(path):
        return seen

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if "product_id" in data:
                    seen.add(str(data["product_id"]))
            except:
                pass
    return seen

def load_categories():
    cat_path = os.path.join(BASE_DIR, "categories.json")
    with open(cat_path, "r", encoding="utf-8") as f:
        cat_data = json.load(f)

    categories = {}
    for cat_id, cat_info in cat_data.items():
        subs = list(
            cat_info.get("subCategories", {})
            .get("entities", {})
            .keys()
        )
        categories[cat_id] = subs or [None]

    return categories
