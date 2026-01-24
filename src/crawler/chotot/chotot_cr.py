import asyncio
import httpx
import json
import re
import os
import aiofiles
import time

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "chotot_realtime.jsonl")
LIMIT = 50
MAX_PAGE = 5000   
STOP_IF_NO_NEW = 20 
CONCURRENCY_LIMIT = 10  # Reduced to avoid HTTP 429

# ================= CLEAN TEXT =================
def clean_text(text):
    if not text:
        return None
    text_str = str(text)
    text_clean = re.sub(r"\s+", " ", text_str).strip()
    return text_clean if text_clean else None

# ================= RESUME =================
def load_seen_ids(path):
    seen = set()
    if not os.path.exists(path):
        return seen
    print(f"Loading seen IDs from {path}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    data = json.loads(line)
                    if "product_id" in data:
                        seen.add(str(data["product_id"]))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error loading seen IDs: {e}")
    
    print(f"Resume loaded {len(seen)} IDs")
    return seen

# ================= HELPER =================
def parse_price(price):
    if price is None:
        return 0
    if isinstance(price, list):
        return "-".join(map(str, price))
    return price

# ================= ASYNC CRAWLER =================
async def fetch_page(client, cg_id, scg_id, page, seen_ids, f_handle, semaphore, total_stats):
    url = "https://gateway.chotot.com/v1/public/ad-listing"
    params = {
        "cg": cg_id,
        "limit": LIMIT,
        "page": page,
    }
    if scg_id:
        params["scg"] = scg_id

    async with semaphore:
        try:
            r = await client.get(url, params=params, timeout=15)
            if r.status_code != 200:
                print(f"  [HTTP {r.status_code}] CG:{cg_id} SCG:{scg_id} P:{page}")
                return 0

            data = r.json()
            ads = data.get("ads", [])
            if not ads:
                return -1 # Mark as no more ads

            new_in_page = 0
            for ad in ads:
                ad_id = str(ad.get("list_id", "")).strip()
                if not ad_id or ad_id in seen_ids:
                    continue

                product_name = clean_text(ad.get("subject"))
                if not product_name or product_name == "Chưa có tên":
                    continue

                seen_ids.add(ad_id)
                new_in_page += 1
                
                cat_name = clean_text(ad.get("category_name")) or str(cg_id)

                record = {
                    "platform": "Chotot",
                    "product_id": ad_id,
                    "product_name": product_name,
                    "price": parse_price(ad.get("price")),
                    "product_url": f"https://www.chotot.com/{ad_id}.htm",
                    "image_url": ad.get("image", ""),
                    "rating": ad.get("average_rating", 0.0),
                    "review_count": ad.get("total_rating", 0),
                    "category": cat_name,
                }
                
                await f_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            
            if new_in_page > 0:
                total_stats['total_new'] += new_in_page
                print(f"  [PAGE {page}] CG:{cg_id} SCG:{scg_id} | +{new_in_page} | Total: {total_stats['total_new']}")
            
            return new_in_page

        except Exception as e:
            print(f"  [ERROR] CG:{cg_id} SCG:{scg_id} P:{page} : {e}")
            return 0

async def crawl_subcategory(client, cg_id, scg_id, seen_ids, f_handle, semaphore, total_stats):
    no_new_count = 0
    for page in range(1, MAX_PAGE + 1):
        # We process pages sequentially for each subcategory to respect STOP_IF_NO_NEW
        # but the subcategories themselves can run in parallel if we wanted.
        # However, to avoid hitting Chotot too hard and to handle STOP_IF_NO_NEW correctly,
        # we'll use a mix of parallel subcategories but sequential pages within them.
        res = await fetch_page(client, cg_id, scg_id, page, seen_ids, f_handle, semaphore, total_stats)
        
        if res == -1: # No ads at all
            break
        if res == 0:
            no_new_count += 1
        else:
            no_new_count = 0
            
        if no_new_count >= STOP_IF_NO_NEW:
            print(f"  [STOP] No new items for {STOP_IF_NO_NEW} pages in SCG {scg_id}")
            break
        
        # Small delay between pages of the same subcategory
        await asyncio.sleep(0.5) # Increased sleep

async def main():
    # Load categories
    try:
        cat_path = os.path.join(BASE_DIR, "categories.json")
        with open(cat_path, "r", encoding="utf-8") as f:
            cat_data = json.load(f)
        
        tasks_meta = []
        for cat_id, cat_info in cat_data.items():
            sub_ids = []
            if "subCategories" in cat_info and "entities" in cat_info["subCategories"]:
                sub_ids = list(cat_info["subCategories"]["entities"].keys())
            
            if not sub_ids:
                tasks_meta.append((cat_id, None))
            else:
                for scid in sub_ids:
                    tasks_meta.append((cat_id, scid))
                    
        print(f"Loaded {len(cat_data)} categories, total {len(tasks_meta)} subcategories tasks.")
            
    except Exception as e:
        print(f"Error loading categories.json: {e}")
        return

    seen_ids = load_seen_ids(OUTPUT_FILE)
    total_stats = {'total_new': 0}
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.chotot.com/",
    }

    async with httpx.AsyncClient(headers=headers, timeout=20) as client:
        async with aiofiles.open(OUTPUT_FILE, mode="a", encoding="utf-8") as f:
            print(f"\n===== STARTING ASYNC CRAWLING =====")
            
            batch_size = 3 # Reduced batch size
            for i in range(0, len(tasks_meta), batch_size):
                batch = tasks_meta[i:i + batch_size]
                sub_tasks = []
                for cg_id, scg_id in batch:
                    sub_tasks.append(crawl_subcategory(client, cg_id, scg_id, seen_ids, f, semaphore, total_stats))
                
                await asyncio.gather(*sub_tasks)
                await f.flush()
                await asyncio.sleep(1) # Batch delay

    print(f"\nDONE. Total new items collected: {total_stats['total_new']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
