import json
import re
import os
from underthesea import word_tokenize

# ================= CONFIG =================
INPUT_FILE = r"F:\SEG301\merge\data_1tr_raw.jsonl"
OUTPUT_FILE = r"F:\SEG301\merge\data_1tr_clean_tokenized.jsonl"
LOG_FILE = r"F:\SEG301\merge\logs\clean_tokenize.log"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# ================= REGEX =================
EMOJI_PATTERN = re.compile(
    "[" 
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE
)

UI_NOISE = re.compile(
    r"(opens in a new window or tab|opens in a new window|in a new window or tab)",
    flags=re.IGNORECASE
)

# ================= CLEAN FUNCTION =================
def clean_text(text):
    if not text:
        return None

    text = str(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = UI_NOISE.sub(" ", text)
    text = EMOJI_PATTERN.sub(" ", text)
    text = text.replace("\uFFFD", "")
    text = re.sub(r"\s+", " ", text).strip()

    if len(text.split()) < 3:
        return None

    return text

# ================= MAIN =================
total = kept = removed = 0
total_tokens = empty_text = 0

with open(INPUT_FILE, "r", encoding="utf-8") as fin, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as fout, \
     open(LOG_FILE, "w", encoding="utf-8") as log:

    for line in fin:
        total += 1

        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            removed += 1
            continue

        raw_text = obj.get("product_name") or obj.get("text")

        clean = clean_text(raw_text)
        if not clean:
            removed += 1
            continue

        tokens = word_tokenize(clean, format="text").split()

        if not tokens:
            empty_text += 1

        obj["clean_text"] = clean
        obj["tokens"] = tokens

        fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

        kept += 1
        total_tokens += len(tokens)

        if total % 100000 == 0:
            log.write(f"[Progress] {total} processed\n")

    # ===== SUMMARY =====
    log.write("\n===== CLEAN + TOKENIZE SUMMARY =====\n")
    log.write(f"Raw docs        : {total}\n")
    log.write(f"Kept docs       : {kept}\n")
    log.write(f"Removed docs    : {removed}\n")
    log.write(f"Empty token doc : {empty_text}\n")
    log.write(f"Total tokens    : {total_tokens}\n")
    log.write(f"Avg tokens/doc  : {total_tokens / max(kept,1):.2f}\n")

print("=== CLEAN + TOKENIZE FINISHED ===")
print(f"Raw docs       : {total}")
print(f"Kept docs      : {kept}")
print(f"Removed docs   : {removed}")
print(f"Total tokens   : {total_tokens}")
print(f"Avg tokens/doc : {total_tokens / max(kept,1):.2f}")
print(f"Output -> {OUTPUT_FILE}")
