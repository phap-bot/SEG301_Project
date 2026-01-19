import json

with open('products_20260113_180508.jsonl', 'r', encoding='utf-8') as f:
    line = f.readline()
    data = json.loads(line)
    
    print('✅ Columns trong file:', list(data.keys()))
    print('\n📊 Tổng số columns:', len(data.keys()))
    print('\n📋 Sample record:')
    for k, v in data.items():
        print(f'  • {k}: {str(v)[:60]}...' if len(str(v)) > 60 else f'  • {k}: {v}')
