"""
SPIMI (Single-Pass In-Memory Indexing) Implementation
Xây dựng inverted index từ 1 triệu documents mà không tràn RAM
"""

import json
import json
import os
import time
from collections import defaultdict
from typing import Dict, List, Tuple
import heapq
import unicodedata
from underthesea import word_tokenize

def strip_accents(s):
   """Loại bỏ dấu tiếng Việt mạnh mẽ (bao gồm cả đ -> d) và đồng bộ dấu gạch dưới"""
   if not s: return ""
   s = s.lower()
   # Xử lý đ -> d thủ công vì NFD không tách được đ
   s = s.replace('đ', 'd')
   # Loại bỏ các dấu sắc, huyền, hỏi, ngã, nặng
   s = "".join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
   # Đồng bộ: thay gạch dưới bằng khoảng trắng rồi split để lấy từ đơn
   # Điều này giúp Index và Search đều làm việc trên 'từ đơn', tăng khả năng khớp
   return s.replace('_', ' ')

class SPIMIIndexer:
    """
    SPIMI Indexer - Xử lý large-scale indexing với memory constraint
    
    Thuật toán:
    1. Chia documents thành các blocks nhỏ
    2. Xây dựng inverted index cho mỗi block trong RAM
    3. Ghi mỗi block ra đĩa
    4. Merge tất cả blocks thành final index
    """
    
    def __init__(self, block_size: int = 10000, output_dir: str = "index"):
        """
        Args:
            block_size: Số documents xử lý mỗi block (default: 10,000)
            output_dir: Thư mục lưu index files
        """
        self.block_size = block_size
        self.output_dir = output_dir
        self.block_count = 0
        
        # Tạo thư mục output nếu chưa có
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "blocks"), exist_ok=True)
        
        # Statistics
        self.total_docs = 0
        self.total_terms = 0
        self.total_tokens = 0   # tổng số token (kể cả trùng lặp)
        self.doc_lengths = {}  # {doc_id: length}
        
    def process_block(self, documents: List[Dict]) -> Dict[str, Dict[int, int]]:
        """
        Xây dựng inverted index cho một block documents trong RAM
        
        Index structure: {term: {doc_id: term_frequency}}
        Lưu TF để tránh phải scan file khi search
        
        Args:
            documents: List of documents, mỗi doc có 'tokens' và metadata
            
        Returns:
            inverted_index: {term: {doc_id: tf, ...}}
        """
        inverted_index = defaultdict(lambda: defaultdict(int))
        
        for doc in documents:
            doc_id = self.total_docs
            tokens = doc.get('tokens')
            
            # Nếu chưa có tokens (input là file raw), thực hiện tách từ on-the-fly
            if tokens is None or not tokens:
                product_name = doc.get('product_name', '')
                if product_name:
                    # Tách từ tiếng Việt chuyên sâu
                    segmented = word_tokenize(product_name, format="text")
                    tokens = segmented.split()
                else:
                    tokens = []
            
            # Lưu document length cho BM25
            self.doc_lengths[doc_id] = len(tokens)
            self.total_tokens += len(tokens)  # đếm tổng token
            
            # Build inverted index với TF: term -> {doc_id: frequency}
            for token in tokens:
                # Chuẩn hóa và tách thành các từ đơn (flatten)
                # Vd: "điện_thoại" -> "điện thoại" -> ["dien", "thoai"]
                sub_tokens = strip_accents(token).split()
                for sub_t in sub_tokens:
                    # Chỉ index các terms hữu ích
                    if self._is_valid_term(sub_t):
                        inverted_index[sub_t][doc_id] += 1  # Increment TF
            
            self.total_docs += 1
        
        # Convert defaultdict to regular dict
        result = {term: dict(doc_freqs) for term, doc_freqs in inverted_index.items()}
        
        time.sleep(1)
        
        return result
    
    def _is_valid_term(self, term: str) -> bool:
        """
        Kiểm tra term có hợp lệ để index không
        
        Bỏ qua:
        - URLs (chứa http://, https://)
        - Số thuần túy (giá, số lượng)
        - Ký tự đặc biệt đơn lẻ
        """
        if not term or len(term) < 2:
            return False
        if term.startswith('http://') or term.startswith('https://'):
            return False
        if term.replace('.', '').replace('_', '').isdigit():
            # Chỉ bỏ qua nếu số quá lớn (giá tiền) hoặc quá nhỏ (số lượng đơn thuần)
            # Giữ lại các số như 13, 14, 15, 16 (model iPhone)
            try:
                val = float(term.replace('_', '')) if '_' in term else float(term)
                if val > 5000: # Ví dụ: giá tiền thường > 5000
                    return False
                if val < 1:
                    return False
            except ValueError:
                # Nếu không convert được (vd: 538.21.350), cứ giữ lại làm term để search
                return True
                
        if term in [':', '/', '.', ',', '-', '+', '(', ')', '[', ']', 'với', 'cho', 'của', 'và']:
            return False
        return True
    
    def write_block_to_disk(self, inverted_index: Dict[str, List[int]], block_id: int):
        """
        Ghi block index ra đĩa dưới dạng sorted dictionary
        
        File format: JSON của {term: [doc_ids]}
        Sorted by term để dễ merge sau này
        """
        block_file = os.path.join(self.output_dir, "blocks", f"block_{block_id:03d}.json")
        
        # Sort terms alphabetically trước khi ghi
        sorted_index = dict(sorted(inverted_index.items()))
        
        with open(block_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_index, f, ensure_ascii=False)
        
        print(f"  ✓ Wrote block {block_id}: {len(sorted_index)} unique terms")
    
    def merge_blocks(self) -> Dict[str, Dict[int, int]]:
        """
        Merge tất cả block files thành final inverted index sử dụng K-way merge
        Dùng heapq để duy trì bộ nhớ thấp (chỉ giữ 1 term từ mỗi block trong RAM)
        """
        print(f"\n🔗 Merging {self.block_count} blocks using K-way merge...")
        
        # Mở tất cả block files và tạo iterators
        block_files = []
        iterators = []
        
        for i in range(self.block_count):
            path = os.path.join(self.output_dir, "blocks", f"block_{i:03d}.json")
            f = open(path, 'r', encoding='utf-8')
            block_files.append(f)
            # Load toàn bộ block data để tạo iterator
            block_data = json.load(f)
            iterators.append(iter(sorted(block_data.items())))
        
        # Priority Queue lưu (term, block_index, doc_tfs)
        heap = []
        for i, it in enumerate(iterators):
            try:
                term, doc_tfs = next(it)
                heapq.heappush(heap, (term, i, doc_tfs))
            except StopIteration:
                pass
        
        final_index = {}
        
        while heap:
            term, block_idx, doc_tfs = heapq.heappop(heap)
            
            if term not in final_index:
                final_index[term] = {}
            
            # Merge dictionary doc_id -> tf
            final_index[term].update(doc_tfs)
            
            # Lấy term tiếp theo từ block vừa pop
            try:
                next_term, next_doc_tfs = next(iterators[block_idx])
                heapq.heappush(heap, (next_term, block_idx, next_doc_tfs))
            except StopIteration:
                pass
        
        # Đóng các file
        for f in block_files:
            f.close()
            
        print(f"  ✓ Merged into {len(final_index)} unique terms")
        return final_index
    
    def build_index(self, input_file: str) -> dict:
        """
        Main pipeline: Build index từ input JSONL file.
        Returns timing dict với thời gian (giây) từng phase.
        """
        print(f"🚀 Starting SPIMI Indexing")
        print(f"   Input: {input_file}")
        print(f"   Block size: {self.block_size:,} documents")
        print()

        timing = {}

        # Tracking byte offsets cho O(1) retrieval
        doc_offsets = {}

        # ── Phase 1: Block Processing ──────────────────────────────────────────
        print("📦 Phase 1: Processing blocks...")
        current_block = []
        t1_start = time.time()

        # Mở file mode binary để lấy offset chính xác
        with open(input_file, 'rb') as f:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break

                doc = json.loads(line.decode('utf-8').strip())
                doc_id = self.total_docs + len(current_block)
                doc_offsets[doc_id] = offset
                current_block.append(doc)

                if len(current_block) >= self.block_size:
                    print(f"  Processing block {self.block_count} (docs {self.total_docs:,} - {self.total_docs + len(current_block):,})...")
                    inverted_index = self.process_block(current_block)
                    self.write_block_to_disk(inverted_index, self.block_count)
                    self.block_count += 1
                    current_block = []

        if current_block:
            print(f"  Processing block {self.block_count} (docs {self.total_docs:,} - {self.total_docs + len(current_block):,})...")
            inverted_index = self.process_block(current_block)
            self.write_block_to_disk(inverted_index, self.block_count)
            self.block_count += 1

        timing["phase1_block"] = time.time() - t1_start
        print(f"  ⏱  Phase 1 done in {timing['phase1_block']:.2f}s")

        t2_start = time.time()
        final_index = self.merge_blocks()

        timing["phase2_merge"] = time.time() - t2_start
        print(f"  ⏱  Phase 2 done in {timing['phase2_merge']:.2f}s")

        # ── Phase 3: Save ──────────────────────────────────────────────────────
        print("\n💾 Phase 3: Saving final files...")
        t3_start = time.time()

        # Inverted Index
        with open(os.path.join(self.output_dir, "inverted_index.json"), 'w', encoding='utf-8') as f:
            json.dump(final_index, f, ensure_ascii=False)

        # Doc Metadata (lengths)
        with open(os.path.join(self.output_dir, "doc_metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(self.doc_lengths, f, ensure_ascii=False)

        # Doc Offsets (vị trí trong file jsonl)
        with open(os.path.join(self.output_dir, "doc_offsets.json"), 'w', encoding='utf-8') as f:
            json.dump(doc_offsets, f, ensure_ascii=False)

        # Stats
        avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths) if self.doc_lengths else 0
        stats = {
            "total_documents": self.total_docs,
            "vocabulary_size": len(final_index),
            "average_doc_length": avg_doc_length,
            "total_tokens": self.total_tokens,
            "total_blocks": self.block_count
        }
        with open(os.path.join(self.output_dir, "index_stats.json"), 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        timing["phase3_save"] = time.time() - t3_start
        print(f"  ⏱  Phase 3 done in {timing['phase3_save']:.2f}s")

        print("\n✅ INDEXING COMPLETE!")
        print(f"Total documents: {self.total_docs:,}")
        print(f"Total tokens   : {self.total_tokens:,}")
        print(f"Vocabulary     : {len(final_index):,} terms")

        return timing


if __name__ == "__main__":
    # Example usage
    indexer = SPIMIIndexer(block_size=10000, output_dir="index")
    indexer.build_index("data_1tr_clean_tokenized.jsonl")
