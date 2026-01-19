"""
Script chuyển đổi CSV sang JSONL
Author: Your Name
Description: Chuyển đổi file lazada_product.csv sang định dạng JSONL
"""

import csv
import json
import os

def csv_to_jsonl(csv_file_path, jsonl_file_path=None):
    """
    Chuyển đổi file CSV sang JSONL
    
    Args:
        csv_file_path: Đường dẫn đến file CSV
        jsonl_file_path: Đường dẫn file JSONL output (optional)
    
    Returns:
        str: Đường dẫn file JSONL đã tạo
    """
    # Nếu không có output path, tạo tên file tự động
    if jsonl_file_path is None:
        base_name = os.path.splitext(csv_file_path)[0]
        jsonl_file_path = f"{base_name}.jsonl"
    
    # Đọc CSV và ghi ra JSONL
    records_count = 0
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile, \
         open(jsonl_file_path, 'w', encoding='utf-8') as jsonlfile:
        
        # Đọc CSV với DictReader để tự động parse headers
        csv_reader = csv.DictReader(csvfile)
        
        # Ghi từng dòng thành JSON
        for row in csv_reader:
            # Chuyển đổi giá trị thành kiểu dữ liệu phù hợp
            processed_row = {}
            for key, value in row.items():
                # Xử lý giá trị rỗng
                if value == '' or value is None:
                    processed_row[key] = None
                # Xử lý số
                elif key in ['id', 'review_count']:
                    try:
                        processed_row[key] = int(value)
                    except (ValueError, TypeError):
                        processed_row[key] = value
                # Xử lý số thập phân
                elif key in ['price', 'original_price', 'discount_percent', 'rating']:
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = value
                else:
                    processed_row[key] = value
            
            # Ghi JSON line
            json_line = json.dumps(processed_row, ensure_ascii=False)
            jsonlfile.write(json_line + '\n')
            records_count += 1
    
    print(f"✅ Đã chuyển đổi {records_count} records từ CSV sang JSONL")
    print(f"📁 File output: {jsonl_file_path}")
    
    return jsonl_file_path


if __name__ == "__main__":
    # Tự động tìm file CSV trong thư mục hiện tại
    csv_file = "lazada_product.csv"
    
    # Kiểm tra file có tồn tại không
    if not os.path.exists(csv_file):
        print(f"❌ Không tìm thấy file: {csv_file}")
        print("💡 Vui lòng đảm bảo file CSV nằm cùng thư mục với script này")
    else:
        # Chuyển đổi
        output_file = csv_to_jsonl(csv_file)
        print(f"\n🎉 Hoàn thành! Kiểm tra file: {output_file}")
