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
        # thêm region nếu muốn scale
    }

    categories = {
    "2000": ["2010","2020","2030","2040","2050"],          # Bất động sản
    "3000": ["3010","3020","3030"],                        # Việc làm
    "4000": ["4010","4020","4030"],                        # Xe cộ
    "5000": ["5010","5020","5030","5040"],                 # Đồ điện tử
    "7000": ["7010","7020","7030","7040"],                 # Thời trang
    "8000": ["8010","8020","8030"],                        # Đồ gia dụng
    "9000": ["9010","9020","9030"],                        # Nội thất
    "10000":["10010","10020","10030"],                     # Mẹ & bé
    "11000":["11010","11020","11030"],                     # Thú cưng
    "14000":["14010","14020","14030","14040"],             # Dịch vụ
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
