import os
import json
import asyncio

# ================= CONFIG =================
KEYWORDS = [
    # Electronics & Computers (30 keywords)
    "laptop", "gaming laptop", "macbook", "chromebook", "tablet", "ipad", "kindle",
    "desktop computer", "gaming pc", "mini pc", "all in one pc",
    "graphics card", "cpu processor", "motherboard", "ram memory", "ssd hard drive",
    "power supply", "pc case", "cpu cooler", "gaming monitor", "4k monitor",
    "wireless mouse", "mechanical keyboard", "gaming headset", "webcam", "usb hub",
    "external hard drive", "portable ssd", "network switch", "wifi router",
]

MAX_PAGE = 20 
SLEEP_RANGE = (2.0, 5.0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "ebay_products.jsonl")
CHECKPOINT_FILE = os.path.join(BASE_DIR, "checkpoint.json")

# Thread-safe locks replaced with asyncio locks
file_lock = asyncio.Lock()
seen_lock = asyncio.Lock()
checkpoint_lock = asyncio.Lock()
# Note: total_saved logic requires global sharing, we'll keep it simple here
total_saved = 0

# ================= CHECKPOINT MANAGEMENT =================
def load_checkpoint():
    """Load checkpoint data from file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

async def save_checkpoint(checkpoint_data):
    """Save checkpoint data to file"""
    async with checkpoint_lock:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

# ================= LOAD SEEN IDS =================
def load_seen_ids():
    seen = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "product_id" in data:
                        seen.add(data["product_id"])
                except:
                    pass
    print(f"Loaded seen_ids: {len(seen)}")
    global total_saved
    total_saved = len(seen)
    return seen

# ================= SAVE =================
async def save_item(item):
    """Save item to output file"""
    async with file_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
