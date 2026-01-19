"""
Crawler độc lập cho Điện Máy Xanh
Chạy riêng để crawl dữ liệu từ DienMayXanh
"""
import os
import json
import asyncio
from typing import List, Dict

from crawler.dienmayxanh_search import DienMayXanhSpider

# Cấu hình
OUTPUT_FILE = r"C:\Users\letan\Downloads\SEG301\price_spider\data\dienmayxanh_products.jsonl"
from crawler.utils import generate_dedup_key

CATEGORIES = {
    "1": {"name": "Điện thoại", "url": "https://www.dienmayxanh.com/dien-thoai"},
    "2": {"name": "Laptop", "url": "https://www.dienmayxanh.com/laptop"},
    "3": {"name": "Tivi", "url": "https://www.dienmayxanh.com/tivi"},
    "4": {"name": "Máy giặt", "url": "https://www.dienmayxanh.com/may-giat"},
    "5": {"name": "Tủ lạnh", "url": "https://www.dienmayxanh.com/tu-lanh"}
}

def load_existing_keys(path: str) -> set:
    """Load existing deduplication keys from JSONL"""
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
                    # Generate key from existing data to check against new data
                    # Use provided fields or defaults
                    p_id = product.get("product_id", "")
                    platform = product.get("platform", "DienMayXanh")
                    name = product.get("product_name", "")
                    url = product.get("product_url", "")
                    
                    # Create key using the same logic as new items
                    key = generate_dedup_key(platform, name, url)
                    keys.add(key)
                except: continue
    except Exception as e:
        print(f"⚠️ Error loading existing keys: {e}")
        
    print(f"✅ Loaded {len(keys)} unique items.")
    return keys

def save_item(item: Dict, keys_set: set):
    """Save single item to JSONL if not duplicate"""
    # 1. Generate Key
    p_id = item.get("product_id", "")
    name = item.get("product_name", "")
    url = item.get("product_url", "")
    platform = item.get("platform", "DienMayXanh")
    
    dedup_key = generate_dedup_key(platform, name, url)
    
    # 2. Check Deduplication
    if dedup_key in keys_set:
        return False
    
    # 3. Write to File (Append)
    try:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        keys_set.add(dedup_key)
        return True
    except Exception as e:
        print(f"❌ Write error: {e}")
        return False

def main():
    print("===== DIENMAYXANH CRAWLER =====")
    
    user_input = input("\n👉 Nhập tại đây: ").strip()
    
    if not user_input:
        print("❌ Vui lòng nhập thông tin")
        return

    # Build category list from comma-separated input
    raw_inputs = [x.strip() for x in user_input.split(',') if x.strip()]
    selected_cats = []
    
    for inp in raw_inputs:
        cat_data = {}
        if inp.startswith("http"):
            cat_data["url"] = inp
            cat_data["name"] = "Custom-URL"
            # Try to guess category name
            for key, val in CATEGORIES.items():
                if val["url"] in inp:
                    cat_data["name"] = val["name"]
                    break
        else:
            # Construct Search URL
            import urllib.parse
            encoded_key = urllib.parse.quote(inp)
            cat_data["url"] = f"https://www.dienmayxanh.com/tim-kiem?key={encoded_key}"
            cat_data["name"] = f"Search: {inp}"
            
        selected_cats.append(cat_data)

    # Load existing keys once
    existing_keys = load_existing_keys(OUTPUT_FILE)
    
    # Process each category sequentially
    total_new_items = 0
    
    for i, cat in enumerate(selected_cats):
        print(f"\n🚀 [{i+1}/{len(selected_cats)}] Starting Crawl: {cat['name']}")
        
        # Instantiate spider fresh for each category to ensure clean browser state
        spider = DienMayXanhSpider(headless=True)
        
        items = []
        new_count = 0
        try:
            # Inline callback for incremental saving
            def on_batch_save(batch_items):
                nonlocal new_count
                count_batch = 0
                for item in batch_items:
                    if not item.get("category"): item["category"] = cat["name"]
                    if save_item(item, existing_keys): count_batch += 1
                new_count += count_batch
                # Optional: print(f"  + Saved {count} new items...")

            items = asyncio.run(spider.scrape_category(cat['url'], max_pages=100, on_items_crawled=on_batch_save))
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user. Stopping all remaining tasks.")
            break # Stop the entire batch
        except Exception as e:
            print(f"⚠️ Error crawling {cat['name']}: {e}")
            
        if items:
            # Final safety deduction (most items likely already saved via callback)
            count_final = 0
            try:
                for item in items:
                    if not item.get("category"):
                        item["category"] = cat["name"]
                        
                    if save_item(item, existing_keys):
                        count_final += 1
            except KeyboardInterrupt:
                 print("\n⚠️ Saving interrupted!")
            
            new_count += count_final
            total_new_items += new_count
            print(f"✅ Finished {cat['name']}. Saved {new_count} NEW items.")
        else:
            print(f"⚠️ No items found for {cat['name']}")
            
    print(f"\n🏁 Crawl Session Completed. Total New Items: {total_new_items}")
            
    print("\n🏁 Crawl Session Completed.")


if __name__ == "__main__":
    main()

