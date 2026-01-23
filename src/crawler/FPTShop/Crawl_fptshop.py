"""
Crawler độc lập cho FPTShop (Playwright Version)
"""
import os
import json
import asyncio
from typing import List, Dict

from crawler.fptshop_search import FPTShopSpider

# CONFIG
# CONFIG
OUTPUT_FILE = r"C:\Users\letan\Downloads\SEG301\price_spider\data\fptshop.jsonl"

# User provided category list
# Flattened categories from user request
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

def generate_dedup_key(platform, name, url):
    # Simple composite key
    return f"{platform}|{url}"

def load_existing_keys(path: str) -> set:
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

def save_item(item: Dict, keys_set: set):
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

def main():
    print("===== FPTSHOP CRAWLER (API) =====")
    
    print("\n📋 Danh mục có sẵn:")
    for cat_id, cat_info in sorted(CATEGORIES.items(), key=lambda x: int(x[0])):
        print(f"  {cat_id}. {cat_info['name']}")
        
    print("\n👉 Nhập ID (1,2...), từ khóa, URL hoặc 'ALL': ")
    user_input = input("   Nhập: ").strip()
    
    if not user_input:
        print("❌ Vui lòng nhập thông tin.")
        return

    selected_cats = []
    
    # Pre-process inputs
    raw_inputs = []
    if user_input.upper() == "ALL":
         raw_inputs = list(CATEGORIES.keys())
    else:
         raw_inputs = [x.strip() for x in user_input.split(',') if x.strip()]

    from urllib.parse import quote_plus

    for inp in raw_inputs:
        cat_data = {}
        if inp in CATEGORIES:
            cat_data = CATEGORIES[inp].copy()
        elif inp.startswith("http"):
             cat_data = {"name": "Custom URL", "url": inp}
        else:
             # Search param
             cat_data = {
                 "name": f"Search: {inp}",
                 "url": f"https://fptshop.com.vn/tim-kiem/tat-ca?key={quote_plus(inp)}"
             }
        selected_cats.append(cat_data)

    # Load keys
    existing_keys = load_existing_keys(OUTPUT_FILE)
    total_new = 0
    
    for i, cat in enumerate(selected_cats):
        print(f"\n[{i+1}/{len(selected_cats)}] 🚀 Starting Crawl: {cat['name']}")
        
        spider = FPTShopSpider(headless=True)
        try:
            # Sync wrapper around async call
            items = asyncio.run(spider.scrape_category(cat['url'], max_pages=30))
            
            new_count = 0
            for item in items:
                # Add category info if not present or generic
                if not item.get("category"):
                    item["category"] = cat["name"]
                    
                if save_item(item, existing_keys):
                    new_count += 1
            
            total_new += new_count
            print(f"✅ Finished {cat['name']}. Saved {new_count} NEW items.")
            
        except Exception as e:
            print(f"⚠️ Error crawling {cat['name']}: {e}")
            import traceback
            traceback.print_exc()
        
    print(f"\n🏁 Complete. Total New: {total_new}")
    
if __name__ == "__main__":
    main()
