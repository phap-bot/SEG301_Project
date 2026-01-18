import json
import hashlib
import os

OUTPUT_FILE = r"C:\Users\letan\Downloads\SEG301\price_spider\data\dienmayxanh_products.jsonl"

def normalize_product_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(name.lower().split())

def generate_dedup_key(platform: str, product_name: str, product_url: str) -> str:
    # Logic matches crawler/utils.py
    raw_key = f"{platform}|{normalize_product_name(product_name)}|{product_url}"
    return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

def verify_data():
    if not os.path.exists(OUTPUT_FILE):
        print(f"❌ File not found: {OUTPUT_FILE}")
        return

    print(f"📂 Analyzing: {OUTPUT_FILE}")
    
    total_lines = 0
    unique_keys = set()
    duplicates = 0
    valid_items = []
    
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip(): continue
            total_lines += 1
            
            try:
                item = json.loads(line)
                p_id = item.get("product_id", "")
                platform = item.get("platform", "DienMayXanh")
                name = item.get("product_name", "")
                url = item.get("product_url", "")
                
                key = generate_dedup_key(platform, name, url)
                
                if key in unique_keys:
                    duplicates += 1
                    # print(f"  Example Dupe: {name}") 
                else:
                    unique_keys.add(key)
                    valid_items.append(item)
                    
            except Exception as e:
                print(f"⚠️ Error parsing line {i+1}: {e}")

    print("\n📊 Verification Report:")
    print(f"  - Total Lines: {total_lines}")
    print(f"  - Unique Items: {len(unique_keys)}")
    print(f"  - Duplicates Found: {duplicates}")
    
    if duplicates > 0:
        print(f"\n⚠️ File contains {duplicates} duplicates.")
        # Optional: Rewrite file logic could go here if requested
    else:
        print("\n✅ Data is clean. No duplicates found.")

if __name__ == "__main__":
    verify_data()
