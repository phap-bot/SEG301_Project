import requests
import json
import re
import time
import os

# ================= CONFIG =================
OUTPUT_FILE = "chotot_realtime.jsonl"
LIMIT = 50
MAX_PAGE = 50
SLEEP_TIME = 0.3
STOP_IF_NO_NEW = 3

# ================= CLEAN TEXT =================
def clean_text(text):
    if not text:
        return "Chưa có tên"
    text = re.sub(r"[^\w\s\d\.,\-\/:()]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else "Chưa có tên"

# ================= RESUME =================
def load_seen_ids(path):
    seen = set()
    if not os.path.exists(path):
        return seen
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                seen.add(json.loads(line)["product_id"])
            except:
                pass
    print(f"Resume loaded {len(seen)} IDs")
    return seen

# ================= MAIN =================
def crawl_chotot():
    url = "https://gateway.chotot.com/v1/public/ad-listing"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Referer": "https://www.chotot.com/",
        "Origin": "https://www.chotot.com",
    }

    regions = {
        "13000": "HCM"
    }

    categories = {
    "12000": ["12010", "12020", "12030"],                  # Thể thao – Du lịch
    "13000": ["13010", "13020", "13030", "13040"],         # Dịch vụ
    "15000": ["15010", "15020", "15030"],                  # Sách – Văn phòng phẩm
    "16000": ["16010", "16020"],                           # Giải trí – Sở thích
    "17000": ["17010", "17020", "17030"],                  # Nông nghiệp – Thực phẩm
    "18000": ["18010", "18020"],                           # Thiết bị công nghiệp
    "19000": ["19010", "19020"],   
}


    seen_ids = load_seen_ids(OUTPUT_FILE)
    total_new = 0

    # 🔥 mở file 1 lần, ghi liên tục
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:

        for region_id in regions:
            print(f"\n===== REGION {region_id} =====")

            for cg_id, scg_list in categories.items():
                for scg_id in scg_list:
                    print(f"Category {cg_id} - Sub {scg_id}")

                    no_new_count = 0

                    for page in range(1, MAX_PAGE + 1):
                        params = {
                            "region_v2": region_id,
                            "cg": cg_id,
                            "scg": scg_id,
                            "limit": LIMIT,
                            "page": page,
                            "o": (page - 1) * LIMIT
                        }

                        try:
                            r = requests.get(url, headers=headers, params=params, timeout=10)
                            if r.status_code != 200:
                                print("  HTTP error, stop")
                                break

                            ads = r.json().get("ads", [])
                            if not ads:
                                print("  No ads, stop")
                                break

                        except Exception as e:
                            print("  Request error:", e)
                            break

                        new_in_page = 0

                        for ad in ads:
                            ad_id = str(ad.get("list_id", "")).strip()
                            if not ad_id or ad_id in seen_ids:
                                continue

                            seen_ids.add(ad_id)
                            new_in_page += 1
                            total_new += 1

                            price = ad.get("price", 0)
                            if isinstance(price, list):
                                price = "-".join(map(str, price))

                            record = {
                                "platform": "Chotot",
                                "product_id": ad_id,
                                "product_name": clean_text(ad.get("subject")),
                                "price": price,
                                "product_url": f"https://www.chotot.com/{ad_id}.htm",
                                "image_url": ad.get("image"),
                                "rating": ad.get("average_rating", 0),
                                "review_count": ad.get("total_rating", 0),
                                "category": clean_text(ad.get("category_name")),
                            }

                            # ✅ GHI NGAY
                            f.write(json.dumps(record, ensure_ascii=False) + "\n")
                            f.flush()
                            # os.fsync(f.fileno())

                        if new_in_page == 0:
                            no_new_count += 1
                        else:
                            no_new_count = 0

                        print(f"  Page {page}: +{new_in_page} | total = {total_new}")

                        if no_new_count >= STOP_IF_NO_NEW:
                            print("  No new items → stop sub-category")
                            break

                        time.sleep(SLEEP_TIME)

    print(f"\nDONE. Total unique items = {total_new}")

# ================= RUN =================
if __name__ == "__main__":
    crawl_chotot()
