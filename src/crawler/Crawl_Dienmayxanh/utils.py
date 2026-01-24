import os
import json
import hashlib
import asyncio
from typing import Dict, Set

# ================= CONSTANTS =================
DMX_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.dienmayxanh.com/",
    "Origin": "https://www.dienmayxanh.com",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1"
}

DMX_COOKIES = []

# ================= HELPER FUNCTIONS =================

def generate_dedup_key(platform, name, url):
    """Generate a unique key for deduplication"""
    raw = f"{platform}|{name}|{url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def clean_text(text):
    """Clean whitespace from text"""
    if not text:
        return None
    return " ".join(text.split())

def load_existing_keys(path: str) -> Set[str]:
    """Load existing deduplication keys from JSONL"""
    keys = set()
    if not os.path.exists(path):
        return keys
    
    print(f"📂 Loading existing data from {path}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    product = json.loads(line)
                    name = product.get("product_name", "")
                    url = product.get("product_url", "")
                    platform = product.get("platform", "DienMayXanh")
                    
                    key = generate_dedup_key(platform, name, url)
                    keys.add(key)
                except: continue
    except Exception as e:
        print(f"⚠️ Error loading existing keys: {e}")
        
    print(f"✅ Loaded {len(keys)} unique items.")
    return keys

def save_item(item: Dict, keys_set: Set[str], output_file: str):
    """Save single item to JSONL if not duplicate"""
    name = item.get("product_name", "")
    url = item.get("product_url", "")
    platform = item.get("platform", "DienMayXanh")
    
    dedup_key = generate_dedup_key(platform, name, url)
    
    if dedup_key in keys_set:
        return False
    
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        keys_set.add(dedup_key)
        return True
    except Exception as e:
        print(f"❌ Write error: {e}")
        return False

async def navigate_with_retry(page, url, retries=3):
    """Navigate to URL with retries"""
    for i in range(retries):
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            return True
        except Exception as e:
            if i == retries - 1:
                print(f"❌ Navigation failed: {url} | Error: {e}")
                return False
            await asyncio.sleep(2)
