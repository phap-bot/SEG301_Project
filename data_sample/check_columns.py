"""
Script kiểm tra columns của bảng Supabase
"""
import requests
import json

SUPABASE_URL = "https://fnhxppusxvfrsxkcuppc.supabase.co"
SUPABASE_KEY = "sb_publishable_wE0zDPKBtqtC32E4sDJo0w_RTwV1ID1"
TABLE_NAME = "products"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

api_url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

# Lấy 1 record đầu tiên
params = {"limit": 1}
response = requests.get(api_url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    if data:
        print("✅ Cấu trúc bảng:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
        print("\n📋 Danh sách columns:")
        for col in data[0].keys():
            print(f"  - {col}")
    else:
        print("❌ Bảng rỗng")
else:
    print(f"❌ Lỗi: {response.status_code}")
    print(response.text)
