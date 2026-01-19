"""
Script xuất dữ liệu từ Supabase sang JSONL
Author: Your Name
Description: Kết nối với Supabase database và xuất dữ liệu ra file JSONL
"""

import json
import os
from datetime import datetime


def supabase_to_jsonl_with_client(supabase_url, supabase_key, table_name, output_file, columns=None, column_mapping=None):
    """
    Xuất dữ liệu từ Supabase sang JSONL sử dụng Supabase Client
    
    Args:
        supabase_url: URL của Supabase project
        supabase_key: API key của Supabase
        table_name: Tên bảng cần xuất
        output_file: Đường dẫn file JSONL output
        columns: List các columns cần lấy (nếu None thì lấy tất cả)
        column_mapping: Dict để đổi tên columns {tên_cũ: tên_mới}
    
    Returns:
        int: Số lượng records đã xuất
    """
    try:
        from supabase import create_client
    except ImportError:
        print("❌ Chưa cài đặt thư viện supabase-py")
        print("💡 Cài đặt bằng lệnh: pip install supabase")
        return 0
    
    # Tạo client kết nối
    supabase = create_client(supabase_url, supabase_key)
    
    # Tạo select query
    select_query = "*" if columns is None else ",".join(columns)
    
    # Lấy tất cả dữ liệu từ bảng (có thể cần phân trang nếu dữ liệu nhiều)
    print(f"🔄 Đang lấy dữ liệu từ bảng '{table_name}'...")
    if columns:
        print(f"📋 Columns: {', '.join(columns)}")
    
    # Xuất dữ liệu (có thể cần pagination cho dữ liệu lớn)
    records_count = 0
    batch_size = 1000
    offset = 0
    
    with open(output_file, 'w', encoding='utf-8') as jsonlfile:
        while True:
            # Lấy dữ liệu theo batch
            response = supabase.table(table_name)\
                .select(select_query)\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            data = response.data
            
            if not data:
                break
            
            # Ghi từng record thành JSON line
            for record in data:
                # Rename columns nếu có mapping
                if column_mapping:
                    record = {column_mapping.get(k, k): v for k, v in record.items()}
                
                json_line = json.dumps(record, ensure_ascii=False, default=str)
                jsonlfile.write(json_line + '\n')
                records_count += 1
            
            print(f"  ⏳ Đã xuất {records_count} records...")
            
            # Nếu batch nhỏ hơn batch_size, đã hết dữ liệu
            if len(data) < batch_size:
                break
            
            offset += batch_size
    
    print(f"✅ Đã xuất {records_count} records từ Supabase")
    print(f"📁 File output: {output_file}")
    
    return records_count


def supabase_to_jsonl_with_requests(supabase_url, supabase_key, table_name, output_file, columns=None, column_mapping=None):
    """
    Xuất dữ liệu từ Supabase sang JSONL sử dụng REST API
    (Không cần cài đặt thư viện supabase-py)
    
    Args:
        supabase_url: URL của Supabase project
        supabase_key: API key của Supabase
        table_name: Tên bảng cần xuất
        output_file: Đường dẫn file JSONL output
        columns: List các columns cần lấy (nếu None thì lấy tất cả)
        column_mapping: Dict để đổi tên columns {tên_cũ: tên_mới}
    
    Returns:
        int: Số lượng records đã xuất
    """
    try:
        import requests
    except ImportError:
        print("❌ Chưa cài đặt thư viện requests")
        print("💡 Cài đặt bằng lệnh: pip install requests")
        return 0
    
    # Chuẩn bị headers
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # API endpoint
    api_url = f"{supabase_url}/rest/v1/{table_name}"
    
    # Tạo select query
    select_query = "*" if columns is None else ",".join(columns)
    
    print(f"🔄 Đang lấy dữ liệu từ bảng '{table_name}'...")
    if columns:
        print(f"📋 Columns: {', '.join(columns)}")
    
    records_count = 0
    batch_size = 1000
    offset = 0
    
    with open(output_file, 'w', encoding='utf-8') as jsonlfile:
        while True:
            # Tạo query parameters cho pagination
            params = {
                "select": select_query,
                "offset": offset,
                "limit": batch_size
            }
            
            # Gọi API
            response = requests.get(api_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Lỗi API: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            if not data:
                break
            
            # Ghi từng record thành JSON line
            for record in data:
                # Rename columns nếu có mapping
                if column_mapping:
                    record = {column_mapping.get(k, k): v for k, v in record.items()}
                
                json_line = json.dumps(record, ensure_ascii=False, default=str)
                jsonlfile.write(json_line + '\n')
                records_count += 1
            
            print(f"  ⏳ Đã xuất {records_count} records...")
            
            # Nếu batch nhỏ hơn batch_size, đã hết dữ liệu
            if len(data) < batch_size:
                break
            
            offset += batch_size
    
    print(f"✅ Đã xuất {records_count} records từ Supabase")
    print(f"📁 File output: {output_file}")
    
    return records_count


if __name__ == "__main__":
    # ========== CẤU HÌNH SUPABASE ==========
    # Thay đổi các giá trị này theo project của bạn
    SUPABASE_URL = "https://fnhxppusxvfrsxkcuppc.supabase.co"  # VD: https://abcdefgh.supabase.co
    SUPABASE_KEY = "sb_publishable_wE0zDPKBtqtC32E4sDJo0w_RTwV1ID1"  # Anon/Public key từ Supabase Dashboard
    TABLE_NAME = "products"  # Tên bảng cần xuất
    
    # Columns cần lấy (để None nếu muốn lấy tất cả)
    COLUMNS = [
        "platform",
        "site_product_id",  # Tên thực tế trong database
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
    
    # Mapping để đổi tên columns (tên_cũ_trong_db: tên_mới_trong_output)
    COLUMN_MAPPING = {
        "site_product_id": "product_id"  # Đổi site_product_id thành product_id
    }
    
    # File output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{TABLE_NAME}_{timestamp}.jsonl"
    
    # ========== HƯỚNG DẪN SỬ DỤNG ==========
    print("=" * 60)
    print("📊 SUPABASE TO JSONL EXPORTER")
    print("=" * 60)
    print("\n💡 HƯỚNG DẪN:")
    print("1. Mở Supabase Dashboard (https://app.supabase.com)")
    print("2. Chọn project của bạn")
    print("3. Vào Settings > API")
    print("4. Copy 'Project URL' và 'anon/public key'")
    print("5. Cập nhật SUPABASE_URL và SUPABASE_KEY ở trên")
    print("6. Cập nhật TABLE_NAME là tên bảng cần xuất")
    print("\n" + "=" * 60)
    
    # Kiểm tra cấu hình
    if SUPABASE_URL == "https://your-project.supabase.co" or \
       SUPABASE_KEY == "your-anon-key-here":
        print("\n⚠️  VUI LÒNG CẬP NHẬT CẤU HÌNH!")
        print("    Sửa các giá trị SUPABASE_URL, SUPABASE_KEY, TABLE_NAME")
        print("    trong file này trước khi chạy.")
    else:
        # Chọn phương thức
        print("\nChọn phương thức xuất dữ liệu:")
        print("1. Sử dụng Supabase Client (cần: pip install supabase)")
        print("2. Sử dụng REST API (cần: pip install requests)")
        
        choice = input("\nNhập lựa chọn (1 hoặc 2): ").strip()
        
        if choice == "1":
            count = supabase_to_jsonl_with_client(
                SUPABASE_URL, 
                SUPABASE_KEY, 
                TABLE_NAME, 
                output_file,
                COLUMNS,
                COLUMN_MAPPING
            )
        elif choice == "2":
            count = supabase_to_jsonl_with_requests(
                SUPABASE_URL, 
                SUPABASE_KEY, 
                TABLE_NAME, 
                output_file,
                COLUMNS,
                COLUMN_MAPPING
            )
        else:
            print("❌ Lựa chọn không hợp lệ!")
            count = 0
        
        if count > 0:
            print(f"\n🎉 Hoàn thành! Kiểm tra file: {output_file}")
