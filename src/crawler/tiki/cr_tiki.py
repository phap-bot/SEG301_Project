import asyncio
import aiohttp
import os
import json
import random

# ================== KEYWORDS (MASSIVE EXPANSION) ==================

KEYWORDS = [
    "điện thoại android",
    "điện thoại pin trâu",
    "điện thoại chơi game",
    "điện thoại chụp ảnh đẹp",
    "điện thoại giá rẻ dưới 5 triệu",
    "máy tính bảng học online",
    "tablet cho trẻ em",
    "tablet màn hình lớn",
    "máy tính bảng android",

    # --- Laptop & IT ---
    "laptop văn phòng",
    "laptop học sinh sinh viên",
    "laptop mỏng nhẹ",
    "laptop gaming",
    "màn hình máy tính",
    "bàn phím cơ",
    "chuột không dây",
    "ổ cứng ssd",
    "ổ cứng di động",
    "ram laptop",
    "router wifi",
    "hub usb type c",
    "webcam học online",
]

# ================== CONFIG ==================

SORTS = {"default": "", "newest": "newest", "price_desc": "price,desc"}
MAX_PAGE = 200
OUTPUT_FILE = r"C:\FPT\SEG301\tiki\tiki_products.jsonl"

CONCURRENT_REQUESTS = 40
CONCURRENT_KEYWORDS = 12

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://tiki.vn/",
    "X-Source-Id": "tiki-web",
}

SEM = asyncio.Semaphore(CONCURRENT_REQUESTS)
WRITE_QUEUE = asyncio.Queue(5000)

# ================== LOAD SEEN ==================

def load_seen_ids():
    ids = set()
    if not os.path.exists(OUTPUT_FILE):
        return ids
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ids.add(json.loads(line)["product_id"])
            except:
                pass
    return ids

# ================== FETCH ==================

async def fetch_page(session, keyword, page, sort):
    url = "https://tiki.vn/api/v2/products"
    params = {"limit": 100, "q": keyword, "page": page, "sort": sort}
    for _ in range(3):
        try:
            async with SEM:
                async with session.get(url, params=params, headers=HEADERS, timeout=15) as r:
                    if r.status == 200:
                        return (await r.json()).get("data", [])
                    if r.status == 403:
                        await asyncio.sleep(5)
        except:
            await asyncio.sleep(2)
    return []

# ================== CRAWL ==================

async def crawl_keyword(session, keyword, sort, seen, stats):
    empty, low_new = 0, 0
    for page in range(1, MAX_PAGE + 1):
        items = await fetch_page(session, keyword, page, sort)
        if not items:
            empty += 1
            if empty >= 2:
                break
            continue
        empty = 0
        new_cnt = 0

        for it in items:
            pid = str(it.get("id"))
            if not pid or pid in seen:
                continue
            seen.add(pid)
            new_cnt += 1
            stats["count"] += 1

            price = it.get("price", 0)
            ori = it.get("original_price", 0)
            discount = round((ori - price) / ori * 100, 2) if ori else 0

            record = {
                "platform": "Tiki",
                "product_id": pid,
                "product_name": it.get("name", "").strip(),
                "price": price,
                "original_price": ori,
                "discount_percent": discount,
                "product_url": "https://tiki.vn/" + (it.get("url_path") or ""),
                "image_url": it.get("thumbnail_url"),
                "rating": it.get("rating_average", 0),
                "review_count": it.get("review_count", 0),
                "category": keyword,
            }
            await WRITE_QUEUE.put(json.dumps(record, ensure_ascii=False))

        if new_cnt == 0:
            low_new += 1
            if page >= 15 and low_new >= 3:
                break
        else:
            low_new = 0

        print(f"{keyword[:20]:20} p{page:3} +{new_cnt:3} total {stats['count']}", end="\r")

# ================== WRITER ==================

async def writer():
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while True:
            line = await WRITE_QUEUE.get()
            if line is None:
                break
            f.write(line + "\n")
            WRITE_QUEUE.task_done()

# ================== MAIN ==================

async def crawl():
    seen = load_seen_ids()
    stats = {"count": len(seen)}
    print("Existing:", stats["count"])

    async with aiohttp.ClientSession() as session:
        w = asyncio.create_task(writer())
        combos = [(k, s) for k in KEYWORDS for s in SORTS.values()]
        random.shuffle(combos)

        for i in range(0, len(combos), CONCURRENT_KEYWORDS):
            chunk = combos[i:i + CONCURRENT_KEYWORDS]
            await asyncio.gather(*[
                crawl_keyword(session, k, s, seen, stats) for k, s in chunk
            ])
            print(f"\nChunk {i // CONCURRENT_KEYWORDS + 1} done")

        await WRITE_QUEUE.join()
        await WRITE_QUEUE.put(None)
        await w

    print("DONE:", stats["count"])

if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(crawl())
