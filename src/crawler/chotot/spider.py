# spider.py
import requests
import json
import time

from utils import (
    OUTPUT_FILE, LIMIT, MAX_PAGE, SLEEP_TIME,
    STOP_IF_NO_NEW, load_seen_ids, load_categories
)
from parser import parse_chotot_ad

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.chotot.com/",
    "Origin": "https://www.chotot.com",
}

API_URL = "https://gateway.chotot.com/v1/public/ad-listing"

def crawl_chotot():
    categories = load_categories()
    seen_ids = load_seen_ids()
    total_new = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for cg_id, scg_list in categories.items():
            for scg_id in scg_list:
                print(f"\nCategory {cg_id} - Sub {scg_id}")
                no_new_count = 0

                for page in range(1, MAX_PAGE + 1):
                    params = {"cg": cg_id, "limit": LIMIT, "page": page}
                    if scg_id:
                        params["scg"] = scg_id

                    try:
                        r = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
                        if r.status_code != 200:
                            time.sleep(1)
                            continue
                        ads = r.json().get("ads", [])
                        if not ads:
                            break
                    except Exception as e:
                        print("Request error:", e)
                        time.sleep(2)
                        continue

                    new_in_page = 0
                    for ad in ads:
                        record = parse_chotot_ad(ad, str(cg_id))
                        if not record:
                            continue

                        pid = record["product_id"]
                        if pid in seen_ids:
                            continue

                        seen_ids.add(pid)
                        new_in_page += 1
                        total_new += 1
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")

                    f.flush()
                    print(f"Page {page}: +{new_in_page} | total = {total_new}")

                    no_new_count = no_new_count + 1 if new_in_page == 0 else 0
                    if no_new_count >= STOP_IF_NO_NEW:
                        print("Stop sub-category (no new items)")
                        break

                    time.sleep(SLEEP_TIME)

    print(f"\nDONE. Total unique items = {total_new}")

if __name__ == "__main__":
    crawl_chotot()
