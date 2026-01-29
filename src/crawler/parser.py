import json
import re
import os
from collections import Counter
from underthesea import word_tokenize

# ================= CONFIG =================
INPUT_FILE = r"F:\merge\data_1tr_raw.jsonl"
OUTPUT_FILE = r"F:\merge\data_1tr_clean_tokenized.jsonl"
LOG_FILE = r"F:\merge\logs\clean_tokenize.log"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

FIELDS = [
    "platform",
    "product_id",
    "product_name",
    "price",
    "original_price",
    "discount_percent",
    "product_url",
    "image_url",
    "rating",
    "review_count",
    "category"
]

UI_NOISE = re.compile(
    r"(opens in a new window or tab|opens in a new window|in a new window or tab)",
    flags=re.IGNORECASE
)

# ================= CLEAN FUNCTION =================
def clean_text(text):
    if not text:
        return ""

    text = str(text)

    # remove script & style
    text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # remove UI noise
    text = UI_NOISE.sub(" ", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text.lower()

# ================= COLLECT 11 SCHEMA =================
def collect_text_from_fields(obj, fields):
    parts = []

    for f in fields:
        val = obj.get(f)
        if val is None:
            continue

        if isinstance(val, list):
            val = " ".join(map(str, val))
        else:
            val = str(val)

        parts.append(val)

    return " ".join(parts)

# ================= MAIN =================
total = kept = deduped = empty = token_count = 0
seen_product_ids = set()
platform_counter = Counter()

with open(INPUT_FILE, "r", encoding="utf-8") as fin, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as fout, \
     open(LOG_FILE, "w", encoding="utf-8") as log:

    for line in fin:
        total += 1

        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        product_id = obj.get("product_id")
        if not product_id:
            continue

        # ===== DE-DUP THEO PRODUCT_ID =====
        if product_id in seen_product_ids:
            deduped += 1
            continue
        seen_product_ids.add(product_id)

        # ===== TEXT PIPELINE =====
        raw_text = collect_text_from_fields(obj, FIELDS)
        clean = clean_text(raw_text)

        if not clean:
            segmented_text = ""
            tokens = []
            empty += 1
        else:
            segmented_text = word_tokenize(clean, format="text")
            tokens = segmented_text.split()

        # ===== SAVE RESULT =====
        obj["segmented_text"] = segmented_text
        obj["tokens"] = tokens

        # JSONL: mỗi record đúng 1 dòng
        fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

        # Count platform
        platform = obj.get("platform")
        if platform:
            platform_counter[platform] += 1

        kept += 1
        token_count += len(tokens)

        if total % 100000 == 0:
            log.write(f"[Progress] {total} processed\n")

    # ===== SUMMARY =====
    log.write("\n===== CLEAN + TOKENIZE SUMMARY =====\n")
    log.write(f"Raw docs        : {total}\n")
    log.write(f"Kept docs       : {kept}\n")
    log.write(f"Total tokens    : {token_count}\n")
    log.write(f"Avg tokens/doc  : {token_count / max(kept,1):.2f}\n")

    # ===== PLATFORM DISTRIBUTION =====
    log.write(f"\n=== PLATFORM DISTRIBUTION ({kept:,} docs) ===\n\n")
    for platform, count in platform_counter.most_common():
        percent = (count / kept) * 100
        log.write(f"{platform:<15}: {count:>8} ({percent:5.2f}%)\n")

print("\n=== CLEAN + TOKENIZE FINISHED ===")
print(f"Raw docs        : {total}")
print(f"Kept docs       : {kept}")
print(f"Total tokens    : {token_count}")
print(f"Avg tokens/doc  : {token_count / max(kept,1):.2f}")
print(f"\nReport written to: {LOG_FILE}")
print(f"Output data at   : {OUTPUT_FILE}")
