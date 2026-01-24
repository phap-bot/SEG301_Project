import asyncio
import httpx
import json
import os
import aiofiles
import time

# Import from local modules
from utils import load_seen_ids, get_headers
from parser import parse_ad

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "chotot_realtime.jsonl")
LIMIT = 50
MAX_PAGE = 5000   
STOP_IF_NO_NEW = 20 
CONCURRENCY_LIMIT = 10  # Reduced to avoid HTTP 429

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
                # Quick check for ID before parsing to save effort
                ad_id = str(ad.get("list_id", "")).strip()
                if not ad_id or ad_id in seen_ids:
                    continue

                # Use parser to process the ad
                record = parse_ad(ad, cg_id)
                if not record:
                    continue

                seen_ids.add(ad_id)
                new_in_page += 1
                
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
        # We process pages sequentially for each subcategory
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
        await asyncio.sleep(0.5) 

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
    
    headers = get_headers()

    async with httpx.AsyncClient(headers=headers, timeout=20) as client:
        async with aiofiles.open(OUTPUT_FILE, mode="a", encoding="utf-8") as f:
            print(f"\n===== STARTING ASYNC CRAWLING =====")
            
            batch_size = 3 
            for i in range(0, len(tasks_meta), batch_size):
                batch = tasks_meta[i:i + batch_size]
                sub_tasks = []
                for cg_id, scg_id in batch:
                    sub_tasks.append(crawl_subcategory(client, cg_id, scg_id, seen_ids, f, semaphore, total_stats))
                
                await asyncio.gather(*sub_tasks)
                await f.flush()
                await asyncio.sleep(1) 

    print(f"\nDONE. Total new items collected: {total_stats['total_new']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
