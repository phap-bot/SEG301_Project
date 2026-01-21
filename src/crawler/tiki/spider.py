# spider.py
import asyncio
import aiohttp
import json
import random
import os

from utils import KEYWORDS, MAX_PAGE, OUTPUT_FILE, SORTS, load_existing_ids
from parser import parse_tiki_product

SEM = asyncio.Semaphore(100)

async def fetch_page(session, keyword, page, sort):
    url = f"https://tiki.vn/api/v2/products?limit=100&q={keyword}&page={page}&sort={sort}"
    for _ in range(5):
        try:
            async with SEM:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(2)
                        continue
                    data = await resp.json()
                    return keyword, data.get("data", [])
        except:
            await asyncio.sleep(2)
    return keyword, []

async def crawl():
    seen_ids = load_existing_ids()
    print(f"📦 Existing products: {len(seen_ids)}")

    async with aiohttp.ClientSession() as session:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            tasks = []
            for kw in KEYWORDS:
                for s in SORTS.values():
                    for p in range(1, MAX_PAGE + 1):
                        tasks.append((kw, p, s))

            random.shuffle(tasks)

            for i in range(0, len(tasks), 500):
                chunk = tasks[i:i+500]
                futures = [fetch_page(session, kw, p, s) for kw, p, s in chunk]

                for future in asyncio.as_completed(futures):
                    keyword, products = await future
                    for item in products:
                        record = parse_tiki_product(item, keyword)
                        if not record:
                            continue

                        pid = record["product_id"]
                        if pid in seen_ids:
                            continue

                        seen_ids.add(pid)
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")

                f.flush()
                print(f"🚀 Crawled: {len(seen_ids)}", end="\r")

    print("\n🎉 Crawl Tiki hoàn tất!")

if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(crawl())
