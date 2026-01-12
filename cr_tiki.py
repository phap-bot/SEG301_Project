import asyncio
import aiohttp
import csv
import os
import re
from underthesea import word_tokenize

# ================== CONFIG
KEYWORD = input("Nhập từ khóa tìm kiếm trên Tiki: ").strip()
MAX_PAGE = 100
OUTPUT_FILE = r"C:\FPT\SEG301\compare\crawl_tiki.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

FIELDS = [
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

# ================== CLEAN TEXT
def normalize(text):
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()

def clean_and_tokenize(text):
    return word_tokenize(normalize(text), format="text")

# ================== LOAD EXISTING CSV
def load_existing_titles():
    titles = set()
    if not os.path.exists(OUTPUT_FILE):
        return titles

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            titles.add(normalize(row["product_name"]))
    return titles

# ================== ASYNC FETCH
async def fetch_page(session, page):
    url = f"https://tiki.vn/api/v2/products?limit=40&q={KEYWORD}&page={page}"
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as resp:
            if resp.status != 200:
                return page, []
            data = await resp.json()
            return page, data.get("data", [])
    except Exception:
        return page, []

# ================== MAIN CRAWLER
async def crawl():
    seen_titles = load_existing_titles()
    existing_count = len(seen_titles)

    new_saved = 0
    total_crawled = 0

    file_exists = os.path.exists(OUTPUT_FILE)

    async with aiohttp.ClientSession() as session:
        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)

            if not file_exists:
                writer.writeheader()

            tasks = [fetch_page(session, p) for p in range(1, MAX_PAGE + 1)]

            for future in asyncio.as_completed(tasks):
                page, products = await future

                for item in products:
                    total_crawled += 1

                    title = item.get("name", "")
                    title_norm = normalize(title)

                    if not title or title_norm in seen_titles:
                        continue

                    seen_titles.add(title_norm)
                    new_saved += 1

                    price = item.get("price", 0)
                    original_price = item.get("original_price", 0)

                    discount_percent = (
                        round((original_price - price) / original_price * 100, 2)
                        if original_price else 0
                    )

                    writer.writerow({
                        "platform": "Tiki",
                        "product_name": clean_and_tokenize(title),
                        "price": price,
                        "original_price": original_price,
                        "discount_percent": discount_percent,
                        "product_url": "https://tiki.vn/" + item.get("url_path", ""),
                        "image_url": item.get("thumbnail_url"),
                        "rating": item.get("rating_average", 0),
                        "review_count": item.get("review_count", 0),
                        "category": item.get("categories", [{}])[0].get("name", KEYWORD)
                    })

                    f.flush()

                    print(
                        f"[PAGE {page}] "
                        f"🆕 Lưu mới: {new_saved} | "
                        f"📥 Crawl: {total_crawled} | "
                        f"📦 Tổng file: {existing_count + new_saved}",
                        end="\r"
                    )

    print(
        f"\n🎉 Hoàn tất! "
        f"Lưu mới: {new_saved} | "
        f"Tổng crawl: {total_crawled} | "
        f"Tổng file: {existing_count + new_saved}"
    )

# ================== RUN
asyncio.run(crawl())
