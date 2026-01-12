import requests
import pandas as pd
import os
import time
import csv
import random
import sys

# Import normalize function from crawler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crawler.normalize import normalize

# ================== CẤU HÌNH
keyword = input("Nhập từ khóa tìm kiếm trên Tiki: ")
keyword_normalized = normalize(keyword)  # Normalize for matching
csv_name = r"C:\Users\letan\Downloads\SEG301\price_spider\tiki_test\crawl_tiki.csv"
MAX_PAGE = 40  # Số page thử nghiệm, có thể tăng

# ================== ĐỌC CSV CŨ (nếu có)
done_titles = set()
done_titles_normalized = set()  # Store normalized titles for matching
if os.path.exists(csv_name):
    df_existing = pd.read_csv(csv_name)
    if 'product_name' in df_existing.columns:
        done_titles = set(df_existing['product_name'].dropna())
        # Also normalize existing titles for better matching
        done_titles_normalized = set(normalize(title) for title in done_titles if title)

total_items = len(done_titles)
print(f"Đang crawl sản phẩm trên Tiki cho từ khóa: {keyword}")
print(f"Từ khóa normalize: {keyword_normalized}")

# Fake headers giống trình duyệt
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": f"https://tiki.vn/search?q={keyword_normalized}"
}

# Schema chuẩn 10 cột (bỏ location)
COLUMNS = [
    "platform",
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

for page in range(1, MAX_PAGE+1):
    url = f"https://tiki.vn/api/v2/products?limit=40&q={keyword_normalized}&page={page}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Page {page} | Lỗi status: {resp.status_code}")
            break

        data = resp.json()
        products = data.get('data', [])
        if not products:
            print("Hết sản phẩm hoặc không còn page mới.")
            break

        page_result = []

        for item in products:
            title = item.get('name', '').strip()
            if not title:
                continue
            
            # Normalize title for matching with existing data
            title_normalized = normalize(title)
            if title_normalized in done_titles_normalized:
                continue

            price = item.get('price', None)
            original_price = item.get('original_price', None)  # key mới
            discount_percent = round((original_price - price)/original_price*100) if original_price else 0
            product_url = "https://tiki.vn/" + item.get('url_path', '')  # key mới
            image_url = item.get('thumbnail_url', None)
            rating = item.get('rating_average', 0)  # key mới
            review_count = item.get('review_count', 0)
            category = item['categories'][0]['name'] if item.get('categories') else keyword

            page_result.append({
                "platform": "Tiki",
                "product_name": title,
                "price": price,
                "original_price": original_price,
                "discount_percent": discount_percent,
                "product_url": product_url,
                "image_url": image_url,
                "rating": rating,
                "review_count": review_count,
                "category": category
            })

            done_titles.add(title)
            done_titles_normalized.add(title_normalized)
            total_items += 1

            # Delay ngắn để tránh block
            time.sleep(random.uniform(0.2, 0.5))

        # Lưu CSV
        if page_result:
            df = pd.DataFrame(page_result, columns=COLUMNS)
            df.to_csv(
                csv_name,
                mode='a',
                header=not os.path.exists(csv_name),
                index=False,
                encoding="utf-8-sig",
                quoting=csv.QUOTE_ALL
            )
            print(f"Page {page} | Lưu {len(page_result)} sản phẩm | Tổng: {total_items}")
        else:
            print(f"Page {page} | Không có sản phẩm mới")

        # Delay giữa các page
        time.sleep(random.uniform(1, 2))

    except Exception as e:
        print(f"Page {page} | Lỗi: {e}")
        break

print(f"Hoàn tất crawl Tiki | Tổng sản phẩm: {total_items}")
