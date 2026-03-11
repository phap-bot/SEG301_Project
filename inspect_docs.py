import json
import os

def find_samples():
    data_file = 'data_1tr_clean_tokenized.jsonl'
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found")
        return
        
    with open(data_file, 'r', encoding='utf-8') as f:
        count = 0
        for line in f:
            try:
                doc = json.loads(line)
            except:
                continue
            name = doc.get('product_name', '').lower()
            if 'xiaomi' in name and ('14' in name or 'redmi' in name):
                print(f"PHONE: {doc.get('product_name')}")
                print(f"TOKENS: {doc.get('tokens', [])[:30]}")
                print("-" * 20)
                count += 1
            elif 'xiaomi' in name and 'watch' in name:
                print(f"WATCH: {doc.get('product_name')}")
                print(f"TOKENS: {doc.get('tokens', [])[:30]}")
                print("-" * 20)
                count += 1
            if count > 10:
                break

if __name__ == "__main__":
    find_samples()
