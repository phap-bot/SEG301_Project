
import sys
import os
import time

# Thêm src/ranking và src/indexer vào path để import
sys.path.append(os.path.join(os.getcwd(), 'src', 'ranking'))
sys.path.append(os.path.join(os.getcwd(), 'src', 'indexer'))

try:
    from bm25 import BM25Ranker
except ImportError as e:
    print(f"❌ Lỗi: Không tìm thấy module ranking. Hãy chắc chắn bạn đang ở thư mục gốc của dự án.")
    print(f"Chi tiết: {e}")
    sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("🚀 Đang khởi tạo hệ thống So sánh giá SEG301...")
    try:
        ranker = BM25Ranker(index_dir="index")
    except Exception as e:
        print(f"❌ Lỗi khi load index: {e}")
        print("Hãy đảm bảo bạn đã chạy 'python src/indexer/spimi.py' trước.")
        return

    while True:
        clear_screen()
        print("="*60)
        print("🔍 HỆ THỐNG SO SÁNH GIÁ SẢN PHẨM (MOCK-UP CLI)")
        print("="*60)
        query = input("\nNhập tên sản phẩm muốn tìm (hoặc 'q' để thoát): ").strip()
        
        if query.lower() == 'q':
            break
        
        if not query:
            continue

        print(f"\n🔎 Đang tìm kiếm '{query}' trên các nền tảng...")
        start_time = time.time()
        results = ranker.search(query, top_k=20)
        duration = time.time() - start_time

        if not results:
            print("\n❌ Không tìm thấy sản phẩm nào phù hợp.")
            input("\nNhấn Enter để tiếp tục...")
            continue

        print(f"✅ Tìm thấy {len(results)} kết quả trong {duration:.2f}s\n")
        
        # Gom nhóm theo platform
        platforms = {}
        for doc_id, score, _ in results:
            doc = ranker.get_doc_info(doc_id)
            p_name = doc.get('platform', 'Other')
            if p_name not in platforms:
                platforms[p_name] = []
            platforms[p_name].append(doc)

        # Hiển thị bảng so sánh giá
        print(f"{'Nền tảng':<15} | {'Giá thấp nhất':<15} | {'Sản phẩm tiêu biểu'}")
        print("-" * 80)
        
        all_sorted_docs = []
        for p_name, docs in platforms.items():
            # Tìm giá thấp nhất của nền tảng này trong top kết quả
            docs_with_price = [d for d in docs if isinstance(d.get('price'), (int, float)) and d.get('price') > 0]
            if not docs_with_price:
                continue
                
            min_price_doc = min(docs_with_price, key=lambda x: x['price'])
            print(f"{p_name:<15} | {min_price_doc['price']:>12,.0f}đ | {min_price_doc['product_name'][:40]}...")
            all_sorted_docs.extend(docs)

        print("\n" + "="*80)
        print("CHI TIẾT TOP KẾT QUẢ (Sắp xếp theo độ liên quan):")
        print("="*80)
        
        for i, (doc_id, score, _) in enumerate(results[:10], 1):
            doc = ranker.get_doc_info(doc_id)
            print(f"{i}. [{doc.get('platform').upper()}] {doc.get('product_name')}")
            print(f"   💰 Giá: {doc.get('price', 0):,.0f}đ | ⭐ {doc.get('rating', 0)} ({doc.get('review_count', 0)} đánh giá)")
            print(f"   🔗 Link: {doc.get('product_url', '#')}\n")

        input("\nNhấn Enter để thực hiện tìm kiếm mới...")

if __name__ == "__main__":
    main()
