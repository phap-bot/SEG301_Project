import asyncio
import aiohttp
import os
import json

# ================== CONFIG ==================
keywords_input = input("Nhập từ khóa tìm kiếm trên Tiki (cách nhau bằng dấu phẩy): ").strip()
KEYWORDS = [k.strip() for k in keywords_input.split(",") if k.strip()]

MAX_PAGE = 50
OUTPUT_FILE = r"C:\FPT\SEG301\compare\tiki_products.jsonl"

# ================== LOAD CLEAN DATA ==================
def load_clean_data(file_path):
    """Load toàn bộ dữ liệu JSONL sạch, loại bỏ ký tự lạ"""
    data = []
    if not os.path.exists(file_path):
        return data

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            clean_line = line.replace('\u2028', ' ').replace('\u2029', ' ')
            if clean_line.strip():
                try:
                    data.append(json.loads(clean_line))
                except json.JSONDecodeError:
                    continue
    return data

# ================== LOAD EXISTING IDS ==================
def load_existing_ids():
    """Load product_id đã crawl để tránh duplicate"""
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

# ================== ASYNC FETCH ==================
SEM = asyncio.Semaphore(10)

async def fetch_page(session, keyword, page):
    url = f"https://tiki.vn/api/v2/products?limit=60&q={keyword}&page={page}"
    for attempt in range(5):  # retry 5 lần nếu lỗi
        try:
            async with SEM:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(2)
                        continue
                    data = await resp.json()
                    return page, data.get("data", [])
        except Exception:
            await asyncio.sleep(2)
    return page, []

# ================== MAIN CRAWLER ==================
async def crawl():
    seen_ids = load_existing_ids()
    existing_count = len(seen_ids)

    async with aiohttp.ClientSession() as session:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for keyword in KEYWORDS:
                print(f"\n🔍 Bắt đầu crawl keyword: {keyword}")
                new_saved = 0
                total_crawled = 0

                tasks = [fetch_page(session, keyword, p) for p in range(1, MAX_PAGE + 1)]

                for future in asyncio.as_completed(tasks):
                    page, products = await future

                    if not products:
                        continue

                    for item in products:
                        total_crawled += 1
                        product_id = item.get("id")
                        if not product_id or str(product_id) in seen_ids:
                            continue

                        seen_ids.add(str(product_id))
                        new_saved += 1

                        price = item.get("price", 0)
                        original_price = item.get("original_price", 0)
                        discount_percent = round((original_price - price) / original_price * 100, 2) if original_price else 0

                        record = {
                            "platform": "Tiki",
                            "product_id": str(product_id),
                            "product_name": item.get("name", "").strip(),
                            "price": price,
                            "original_price": original_price,
                            "discount_percent": discount_percent,
                            "product_url": "https://tiki.vn/" + item.get("url_path", ""),
                            "image_url": item.get("thumbnail_url"),
                            "rating": item.get("rating_average", 0),
                            "review_count": item.get("review_count", 0),
                            "category": keyword
                        }

                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        f.flush()

                        print(
                            f"[{keyword} - PAGE {page}] 🆕 Lưu mới: {new_saved} | 📥 Crawl: {total_crawled} | 📦 Tổng file: {existing_count + new_saved}",
                            end="\r"
                        )

                print(f"\n✅ Hoàn tất crawl keyword: {keyword} | Lưu mới: {new_saved}, Tổng crawl: {total_crawled}")

    print(
        f"\n🎉 Hoàn tất tất cả keyword!"
        f"\nTổng sản phẩm trong file: {len(seen_ids)}"
    )

# ================== RUN ==================
asyncio.run(crawl())
