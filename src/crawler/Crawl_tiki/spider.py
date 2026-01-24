import asyncio
import aiohttp
import os
import json
import random
import utils
import parser

# ================== GLOBALS ==================

SEM = asyncio.Semaphore(utils.CONCURRENT_REQUESTS)
WRITE_QUEUE = asyncio.Queue(5000)

# ================== FETCH ==================

async def fetch_page(session, keyword, page, sort):
    url = "https://tiki.vn/api/v2/products"
    params = {"limit": 100, "q": keyword, "page": page, "sort": sort}
    for _ in range(3):
        try:
            async with SEM:
                async with session.get(url, params=params, headers=utils.HEADERS, timeout=15) as r:
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
    for page in range(1, utils.MAX_PAGE + 1):
        items = await fetch_page(session, keyword, page, sort)
        if not items:
            empty += 1
            if empty >= 2:
                break
            continue
        empty = 0
        new_cnt = 0

        for it in items:
            parsed_item = parser.parse_product(it, keyword)
            if not parsed_item:
                continue
            
            pid = parsed_item["product_id"]
            if pid in seen:
                continue
            seen.add(pid)
            new_cnt += 1
            stats["count"] += 1

            await WRITE_QUEUE.put(json.dumps(parsed_item, ensure_ascii=False))

        if new_cnt == 0:
            low_new += 1
            if page >= 15 and low_new >= 3:
                break
        else:
            low_new = 0

        print(f"{keyword[:20]:20} p{page:3} +{new_cnt:3} total {stats['count']}", end="\r")

# ================== WRITER ==================

async def writer():
    os.makedirs(os.path.dirname(utils.OUTPUT_FILE), exist_ok=True)
    with open(utils.OUTPUT_FILE, "a", encoding="utf-8") as f:
        while True:
            line = await WRITE_QUEUE.get()
            if line is None:
                break
            f.write(line + "\n")
            WRITE_QUEUE.task_done()

# ================== MAIN ==================

async def crawl():
    seen = utils.load_seen_ids()
    stats = {"count": len(seen)}
    print("Existing:", stats["count"])

    async with aiohttp.ClientSession() as session:
        w = asyncio.create_task(writer())
        combos = [(k, s) for k in utils.KEYWORDS for s in utils.SORTS.values()]
        random.shuffle(combos)

        for i in range(0, len(combos), utils.CONCURRENT_KEYWORDS):
            chunk = combos[i:i + utils.CONCURRENT_KEYWORDS]
            await asyncio.gather(*[
                crawl_keyword(session, k, s, seen, stats) for k, s in chunk
            ])
            print(f"\nChunk {i // utils.CONCURRENT_KEYWORDS + 1} done")

        await WRITE_QUEUE.join()
        await WRITE_QUEUE.put(None)
        await w

    print("DONE:", stats["count"])

if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(crawl())
