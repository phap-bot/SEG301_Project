import asyncio
import aiohttp
import os
import json

# ================== CONFIG
KEYWORD = input("Nhập từ khóa tìm kiếm trên Tiki: ").strip()
MAX_PAGE = 50

OUTPUT_FILE = r"C:\FPT\SEG301\compare\tiki_products.jsonl"



def load_clean_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Loại bỏ các ký tự ngắt dòng lạ bằng cách replace
            clean_line = line.replace('\u2028', ' ').replace('\u2029', ' ')
            if clean_line.strip():
                data.append(json.loads(clean_line))
    return data
# ================== LOAD EXISTING IDS (JSONL)
def load_existing_ids():
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

# ================== ASYNC FETCH
SEM = asyncio.Semaphore(10)

async def fetch_page(session, page):
    url = f"https://tiki.vn/api/v2/products?limit=60&q={KEYWORD}&page={page}"
    try:
        async with SEM:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return page, []
                data = await resp.json()
                return page, data.get("data", [])
    except Exception:
        return page, []

# ================== MAIN CRAWLER
async def crawl():
    seen_ids = load_existing_ids()
    existing_count = len(seen_ids)

    new_saved = 0
    total_crawled = 0

    async with aiohttp.ClientSession() as session:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            tasks = [fetch_page(session, p) for p in range(1, MAX_PAGE + 1)]

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

                    discount_percent = (
                        round((original_price - price) / original_price * 100, 2)
                        if original_price else 0
                    )

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
                        "category": KEYWORD
                    }

                    # ✅ ghi JSONL
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()

                    print(
                        f"[PAGE {page}] "
                        f"🆕 Lưu mới: {new_saved} | "
                        f"📥 Crawl: {total_crawled} | "
                        f"📦 Tổng file: {existing_count + new_saved}",
                        end="\r"
                    )

    print(
        f"\n🎉 Hoàn tất!"
        f"\n- Lưu mới: {new_saved}"
        f"\n- Tổng crawl: {total_crawled}"
        f"\n- Tổng file: {existing_count + new_saved}"
    )

# ================== RUN
asyncio.run(crawl())
