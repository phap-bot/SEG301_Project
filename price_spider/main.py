import pandas as pd
import os

from crawler.shopee_search import search as shopee
from crawler.tiki_search import search as tiki
from crawler.lazada_search import search as lazada
from crawler.cellphone_search import search as cellphones
from crawler.dienmayxanh_search import search as dmx
from crawler.normalize import normalize

OUTPUT_FILE = "data/products.csv"

# Dùng để chống trùng
KEY_COLUMNS = ["source", "name_norm"]


import concurrent.futures

def crawl_all(keyword):
    products = []

    crawlers = [
        ("Shopee", shopee),
        ("Tiki", tiki),
        ("Lazada", lazada),
        ("Cellphone", cellphones),
        ("DienMayXanh", dmx),
    ]
    
    # Filter out dummy imports if they fail/empty (assuming robust imports in main, but let's be safe)
    # For now, just run what we have.

    param_list = []
    # Create a wrapper to capture name
    def run_crawler(name, func, kw):
        print(f"[INFO] 🚀 Start Crawling {name}...")
        try:
            return name, func(kw)
        except Exception as e:
            return name, e

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_crawler, name, func, keyword) for name, func in crawlers]
        
        for future in concurrent.futures.as_completed(futures):
            name, result = future.result()
            if isinstance(result, Exception):
                print(f"[ERROR] ❌ {name}: {result}")
            else:
                print(f"[OK] ✅ {name}: {len(result)} items")
                products.extend(result)

    return products


def save_to_csv(new_df: pd.DataFrame):
    if new_df.empty:
        print("⚠️ Không có dữ liệu mới")
        return

    # Nếu file đã tồn tại → append + dedup
    if os.path.exists(OUTPUT_FILE):
        old_df = pd.read_csv(OUTPUT_FILE)
        df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        df = new_df

    # Chuẩn hoá tên (entity resolution step 1)
    df["name_norm"] = df["name"].apply(normalize)

    # Xoá trùng
    df.drop_duplicates(subset=KEY_COLUMNS, inplace=True)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"💾 Saved {len(df)} rows → {OUTPUT_FILE}")


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

        df_new = pd.DataFrame(products)

        print("\n===== PREVIEW =====")
        print(df_new.head())
        print("NEW ITEMS:", len(df_new))

        save_to_csv(df_new)


if __name__ == "__main__":
    main()
