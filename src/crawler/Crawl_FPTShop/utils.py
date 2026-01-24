import os
import json
from typing import Dict, Set

# ================= CONFIG =================
OUTPUT_FILE = r"C:\Users\letan\Downloads\SEG301\price_spider\data\fptshop.jsonl"

RAW_CATEGORIES = {
  "cong-nghe": [
    "dien-thoai", "may-tinh-xach-tay", "may-tinh-bang", "may-tinh-de-ban", 
    "man-hinh", "smartwatch", "may-in", "linh-kien"
  ],
  "phu-kien": [
    "tai-nghe", "loa", "sac-cap", "pin-du-phong", "chuot", "ban-phim", 
    "op-lung", "phu-kien-khac"
  ],
  "dien-may": [
    "tivi", "tu-lanh", "may-giat", "may-lanh-dieu-hoa", "robot-hut-bui", 
    "may-loc-nuoc", "may-loc-khong-khi", "gia-dung"
  ],
  "thiet-bi-bep": [
    "noi-chien-khong-dau", "bep-dien-bep-tu", "lo-vi-song", 
    "may-xay-may-ep", "thiet-bi-bep-khac"
  ],
  "sim-dich-vu": [
    "sim-fpt", "sim-so-dep", "sim-du-lich"
  ],
  "may-cu-doi-tra": [
    "dien-thoai-cu", "laptop-cu", "tablet-cu", "thiet-bi-cu-khac"
  ]
}

CATEGORIES = {}
_idx = 1
for group, slugs in RAW_CATEGORIES.items():
    for slug in slugs:
        CATEGORIES[str(_idx)] = {
            "name": slug.replace("-", " ").title(),
            "url": f"https://fptshop.com.vn/{slug}"
        }
        _idx += 1

# ================= HELPER FUNCTIONS =================

def generate_dedup_key(platform, name, url):
    """Simple composite key"""
    return f"{platform}|{url}"

def load_existing_keys(path: str) -> Set[str]:
    """Load existing keys to avoid duplicates"""
    keys = set()
    if not os.path.exists(path):
        return keys
    
    print(f"📂 Loading existing data from {path}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    product = json.loads(line)
                    platform = product.get("platform", "FPTShop")
                    name = product.get("product_name", "")
                    url = product.get("product_url", "")
                    key = generate_dedup_key(platform, name, url)
                    keys.add(key)
                except: continue
    except Exception as e:
        print(f"⚠️ Error loading existing keys: {e}")
        
    print(f"✅ Loaded {len(keys)} unique items.")
    return keys

def save_item(item: Dict, keys_set: Set[str]):
    """Save item to JSONL if unique"""
    p_id = item.get("product_id", "")
    name = item.get("product_name", "")
    url = item.get("product_url", "")
    platform = item.get("platform", "FPTShop")
    
    dedup_key = generate_dedup_key(platform, name, url)
    
    if dedup_key in keys_set:
        return False
    
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        keys_set.add(dedup_key)
        return True
    except Exception as e:
        print(f"❌ Write error: {e}")
        return False
