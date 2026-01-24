import os
import re
import json

# ================= HELPER FUNCTIONS =================

def clean_text(text):
    """
    Cleans text by removing extra whitespace.
    """
    if not text:
        return None
    text_str = str(text)
    text_clean = re.sub(r"\s+", " ", text_str).strip()
    return text_clean if text_clean else None

def load_seen_ids(path):
    """
    Loads existing product IDs from the output file to avoid duplicates.
    """
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

def get_headers():
    """
    Returns the headers for HTTP requests.
    """
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.chotot.com/",
    }
