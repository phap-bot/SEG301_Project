import os
import json
from typing import List, Dict
import concurrent.futures

from crawler.tiki_search import search as tiki
from crawler.lazada_search import search as lazada
from crawler.cellphone_search import search as cellphones
# DienMayXanh đã tách ra file riêng crawl_dienmayxanh.py
# Shopee đã tắt theo yêu cầu

# Cấu hình số trang crawl và số worker song song (có thể chỉnh qua env)
MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "50"))
MAX_WORKERS = int(os.getenv("CRAWL_MAX_WORKERS", "10"))  # Giảm để tránh quá tải

# Output files
JSONL_OUTPUT_FILE = r"C:\Users\letan\Downloads\SEG301\price_spider\data\products.jsonl"  # JSON Lines format

# Dùng để chống trùng (dựa trên platform và product_id)
seen_products = set()

def crawl_all(keyword):
    products = []

    crawlers = [
        ("Tiki", tiki),
        ("Lazada", lazada),
        ("Cellphone", cellphones),
        # Shopee đã tắt
        # DienMayXanh đã tách ra file riêng crawl_dienmayxanh.py
    ]
    
    # Create a wrapper to capture name
    def run_crawler(name, func, kw):
        print(f"[INFO] 🚀 Start Crawling {name}...")
        try:
            # Ưu tiên truyền max_pages nếu crawler hỗ trợ
            try:
                result = func(kw, max_pages=MAX_PAGES)
                # Kiểm tra kết quả
                if result is None:
                    print(f"[WARNING] ⚠️ {name}: Returned None")
                    return name, []
                if not isinstance(result, list):
                    print(f"[WARNING] ⚠️ {name}: Returned {type(result)}, expected list")
                    return name, []
                return name, result
            except TypeError as e:
                # Thử không có max_pages
                try:
                    result = func(kw)
                    if result is None:
                        return name, []
                    if not isinstance(result, list):
                        return name, []
                    return name, result
                except Exception as e2:
                    print(f"[ERROR] ❌ {name}: TypeError fallback failed: {e2}")
                    import traceback
                    traceback.print_exc()
                    return name, e2
        except Exception as e:
            print(f"[ERROR] ❌ {name}: Exception occurred")
            import traceback
            traceback.print_exc()
            return name, e

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_crawler, name, func, keyword) for name, func in crawlers]
        
        for future in concurrent.futures.as_completed(futures):
            name, result = future.result()
            if isinstance(result, Exception):
                print(f"[ERROR] ❌ {name}: {type(result).__name__}: {result}")
            elif isinstance(result, list):
                if len(result) > 0:
                    print(f"[OK] ✅ {name}: {len(result)} items")
                    products.extend(result)
                else:
                    print(f"[WARNING] ⚠️ {name}: No items found (returned empty list)")
            else:
                print(f"[ERROR] ❌ {name}: Unexpected result type: {type(result)}")

    return products


def deduplicate_products(products: List[Dict]) -> List[Dict]:
    """Remove duplicate products based on platform and product_id"""
    seen = set()
    unique_products = []
    
    for product in products:
        # Create unique key from platform and product_id
        key = (product.get("platform", ""), product.get("product_id", ""))
        if key not in seen and key[0] and key[1]:  # Both must be non-empty
            seen.add(key)
            unique_products.append(product)
    
    return unique_products


def save_to_jsonl(products: List[Dict], append: bool = False):
    """
    Save products to JSONL format - tối ưu tốc độ
    """
    if not products:
        print("⚠️ Không có dữ liệu để lưu")
        return
    
    # Deduplicate
    products = deduplicate_products(products)
    
    def load_jsonl(path: str) -> List[Dict]:
        """Load JSONL nhanh với buffering"""
        if not os.path.exists(path):
            return []
        data = []
        # Sử dụng buffering để đọc nhanh hơn
        with open(path, "r", encoding="utf-8", buffering=8192) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except:
                    continue
        return data
    
    # Load existing products if appending
    existing_products = load_jsonl(JSONL_OUTPUT_FILE) if append else []
    
    # Merge and deduplicate
    all_products = existing_products + products
    all_products = deduplicate_products(all_products)
    
    # Save as JSONL (JSON Lines format) - sử dụng buffering để ghi nhanh
    with open(JSONL_OUTPUT_FILE, "w", encoding="utf-8", buffering=8192) as f:
        for product in all_products:
            f.write(json.dumps(product, ensure_ascii=False) + "\n")
    
    print(f"💾 Saved {len(all_products)} products → {JSONL_OUTPUT_FILE}")


def main():
    print("===== E-COMMERCE PRICE SPIDER =====")

    while True:
        keyword = input("\n👉 Nhập từ khóa sản phẩm (Enter để thoát): ").strip()

        if not keyword:
            print("👋 Thoát chương trình")
            break

        products = crawl_all(keyword)

        if not products:
            print("⚠️ Không crawl được dữ liệu")
            continue

        print(f"\n===== PREVIEW (First 3 items) =====")
        for i, product in enumerate(products[:3], 1):
            print(f"\n{i}. {product.get('platform', 'N/A')} - {product.get('product_name', 'N/A')[:50]}")
            print(f"   Price: {product.get('price', 0):,.0f}₫")
            if product.get('original_price'):
                print(f"   Original: {product.get('original_price', 0):,.0f}₫")
            if product.get('rating'):
                print(f"   Rating: {product.get('rating')} ({product.get('review_count', 0)} reviews)")
        
        print(f"\nNEW ITEMS: {len(products)}")
        
        # Save to JSON/JSONL
        save_to_jsonl(products, append=True)


if __name__ == "__main__":
    main()
