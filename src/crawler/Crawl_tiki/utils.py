import os
import json

# ================== KEYWORDS ==================

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

# ================== LOAD SEEN ==================

def load_seen_ids():
    ids = set()
    if not os.path.exists(OUTPUT_FILE):
        return ids
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ids.add(json.loads(line)["product_id"])
                except:
                    pass
    except Exception as e:
        print(f"Error loading seen IDs: {e}")
    return ids
