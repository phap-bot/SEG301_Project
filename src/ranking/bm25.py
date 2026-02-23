"""
BM25 Ranking Algorithm Implementation
Code tay hoàn toàn - KHÔNG dùng thư viện rank() có sẵn
"""

import pickle
import json
import math
from collections import Counter
from typing import Dict, List, Tuple
import sys
import os

# Thêm đường dẫn để import tokenizer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'indexer'))
from vietnamese_tokenizer import tokenize


class BM25Ranker:
    """
    BM25 Ranker - Tính relevance score cho documents dựa trên BM25 algorithm
    
    BM25 Formula:
    score(D, Q) = Σ [IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))]
    
    Trong đó:
    - D: Document
    - Q: Query (tập các terms)
    - qi: Term thứ i trong query
    - f(qi, D): Term frequency của qi trong document D
    - |D|: Document length (số tokens)
    - avgdl: Average document length
    - k1: Term frequency saturation parameter (thường = 1.5)
    - b: Length normalization parameter (thường = 0.75)
    - IDF(qi): Inverse Document Frequency
    """
    
    def __init__(self, index_dir: str = "index", k1: float = 2.0, b: float = 0.8):
        """
        Args:
            index_dir: Thư mục chứa index files
            k1: BM25 parameter - điều chỉnh ảnh hưởng của term frequency
            b: BM25 parameter - điều chỉnh length normalization
        """
        self.index_dir = index_dir
        self.k1 = k1
        self.b = b
        
        # Load index và metadata
        self.inverted_index = None
        self.doc_lengths = None
        self.stats = None
        self.avg_doc_length = 0
        self.total_docs = 0
        
        self.load_index()
    
    def load_index(self):
        """Load inverted index, document metadata và statistics"""
        print("📚 Loading index...")
        
        # Load inverted index
        index_file = f"{self.index_dir}/inverted_index.pkl"
        with open(index_file, 'rb') as f:
            self.inverted_index = pickle.load(f)
        print(f"  ✓ Loaded inverted index: {len(self.inverted_index):,} terms")
        
        # Load document metadata
        metadata_file = f"{self.index_dir}/doc_metadata.pkl"
        with open(metadata_file, 'rb') as f:
            self.doc_lengths = pickle.load(f)
        print(f"  ✓ Loaded doc metadata: {len(self.doc_lengths):,} documents")
        
        # Load statistics
        stats_file = f"{self.index_dir}/index_stats.json"
        with open(stats_file, 'r', encoding='utf-8') as f:
            self.stats = json.load(f)
        
        self.total_docs = self.stats['total_documents']
        self.avg_doc_length = self.stats['average_doc_length']
        
        # Load doc offsets
        offsets_file = f"{self.index_dir}/doc_offsets.pkl"
        try:
            with open(offsets_file, 'rb') as f:
                self.doc_offsets = pickle.load(f)
            print(f"  ✓ Loaded doc offsets: {len(self.doc_offsets):,} documents")
        except FileNotFoundError:
            print("  ⚠️ Warning: doc_offsets.pkl not found. Search results retrieval will be slow.")
            self.doc_offsets = {}

        print(f"  ✓ Total docs: {self.total_docs:,}")
        print(f"  ✓ Avg doc length: {self.avg_doc_length:.2f}")
        print()
    
    def calculate_idf(self, term: str) -> float:
        """
        Tính IDF (Inverse Document Frequency) cho một term
        
        Formula: IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
        
        Giải thích:
        - N: Tổng số documents
        - df(t): Document frequency - số documents chứa term t
        - +0.5: Smoothing để tránh division by zero
        - +1: Đảm bảo IDF không âm
        
        Terms xuất hiện ở nhiều docs → df cao → IDF thấp (common terms)
        Terms xuất hiện ở ít docs → df thấp → IDF cao (rare terms)
        
        Args:
            term: Search term
            
        Returns:
            idf_score: IDF value (càng cao = term càng quan trọng)
        """
        # Lấy document frequency
        if term not in self.inverted_index:
            # Term không có trong index → df = 0
            # IDF sẽ rất cao nhưng không match document nào
            return 0.0
        
        df = len(self.inverted_index[term])  # Số documents chứa term
        
        # Tính IDF theo công thức BM25
        idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
        
        return idf
    
    def calculate_tf(self, term: str, doc_id: int, doc_tokens: List[str]) -> int:
        """
        Tính TF (Term Frequency) - số lần term xuất hiện trong document
        
        Args:
            term: Search term
            doc_id: Document ID
            doc_tokens: List of tokens trong document
            
        Returns:
            term_frequency: Số lần term xuất hiện
        """
        # Đếm số lần xuất hiện của term trong doc_tokens
        tf = doc_tokens.count(term)
        return tf
    
    def calculate_bm25_score(self, query_terms: List[str], doc_id: int, 
                            doc_tokens: List[str]) -> float:
        """
        Tính BM25 score cho một document với query
        
        BM25 Formula (chi tiết):
        score = Σ [IDF(qi) * (TF(qi) * (k1 + 1)) / (TF(qi) + k1 * (1 - b + b * doc_len / avg_doc_len))]
        
        Giải thích các thành phần:
        1. IDF(qi): Trọng số của term (rare terms có trọng số cao hơn)
        2. TF(qi) * (k1 + 1): Numerator - tăng theo term frequency
        3. TF(qi) + k1 * (...): Denominator - saturation effect
        4. (1 - b + b * doc_len / avg_doc_len): Length normalization
           - Doc dài hơn avg → penalty (giảm score)
           - Doc ngắn hơn avg → boost (tăng score)
        
        Args:
            query_terms: List of search terms
            doc_id: Document ID
            doc_tokens: Tokens của document
            
        Returns:
            bm25_score: Relevance score (càng cao càng relevant)
        """
        # Document length
        doc_len = len(doc_tokens)
        
        # BM25 score = tổng của từng term trong query
        score = 0.0
        
        for term in query_terms:
            # Tính IDF
            idf = self.calculate_idf(term)
            
            # Nếu term không có trong index, bỏ qua
            if idf == 0.0:
                continue
            
            # Tính TF
            tf = self.calculate_tf(term, doc_id, doc_tokens)
            
            # Nếu term không có trong doc, bỏ qua
            if tf == 0:
                continue
            
            # Tính BM25 component cho term này
            # Numerator: tf * (k1 + 1)
            numerator = tf * (self.k1 + 1)
            
            # Denominator: tf + k1 * (1 - b + b * doc_len / avg_doc_len)
            length_norm = 1 - self.b + self.b * (doc_len / self.avg_doc_length)
            denominator = tf + self.k1 * length_norm
            
            # BM25 component = IDF * (numerator / denominator)
            term_score = idf * (numerator / denominator)
            
            score += term_score
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float, str]]:
        """
        Search thông minh nâng cao: BM25 + Intent Recognition + Smart Reranking
        """
        query_terms = tokenize(query)
        if not query_terms:
            return []
            
        print(f"🔍 Searching: '{query}'")
        
        # 1. Intent Recognition: Nhận diện ý định
        units = {'gb', 'tb', 'mb', 'ram', 'ssd', 'hdd'}
        accessory_keywords = {'ốp', 'sạc', 'pin', 'cáp', 'vỏ', 'bao', 'dán', 'kính', 'cường_lực', 'thay', 'sửa', 'xác', 'dây_đeo'}
        
        query_has_unit = any(t in units or any(u in t for u in units if len(t) > 2) for t in query_terms)
        query_has_accessory = any(t in accessory_keywords for t in query_terms)
        
        # 2. Thu thập ứng cử viên từ BM25 (lấy top 200)
        doc_scores = {}
        for term in query_terms:
            if term not in self.inverted_index:
                continue
            
            df = len(self.inverted_index[term])
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
            
            for doc_id, tf in self.inverted_index[term].items():
                doc_len = self.doc_lengths.get(doc_id, self.avg_doc_length)
                numerator = tf * (self.k1 + 1)
                length_norm = 1 - self.b + self.b * (doc_len / self.avg_doc_length)
                denominator = tf + self.k1 * length_norm
                
                score = idf * (numerator / denominator)
                # Phạt từ khóa quá phổ biến (nhưng không phạt nếu query ngắn)
                if len(query_terms) > 1 and df > self.total_docs * 0.05: score *= 0.3
                
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + score
        
        if not doc_scores:
            return []
            
        raw_top = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:200]
        print(f"   Smart Reranking top {len(raw_top)} results...")
        
        final_results = []
        important_query_terms = [t for t in query_terms if t not in ['điện_thoại', 'máy', 'bán'] and len(self.inverted_index.get(t, [])) < self.total_docs * 0.2]

        for doc_id, base_score in raw_top:
            doc = self.get_doc_info(doc_id)
            name = doc.get('product_name', '').lower()
            name_tokens = [t.replace('_', ' ') for t in doc.get('tokens', [])]
            name_str = " ".join(name_tokens)
            
            boost = 1.0
            
            # --- CHIẾN LƯỢC 1: EXACT PHRASE MATCH ---
            query_clean = " ".join(query_terms).replace('_', ' ')
            if query_clean in name_str:
                boost *= 3.0 # Ưu tiên tuyệt đối nếu khớp nguyên cụm
            
            # --- CHIẾN LƯỢC 2: PHÂN BIỆT MODEL & SPEC (VD: 16 vs 16GB) ---
            # Nếu query có số (vd: 16) nhưng không có đơn vị kèm theo (gb)
            # Mà trong tên sản phẩm số đó lại đi kèm đơn vị (16gb), thì giảm ưu tiên
            if not query_has_unit:
                for t_query in query_terms:
                    if t_query.isdigit():
                        # Kiểm tra xem trong tên, con số này có bị dán nhãn đơn vị không
                        pos = name_str.find(t_query)
                        if pos != -1:
                            after_text = name_str[pos + len(t_query):pos + len(t_query)+5].strip()
                            if any(after_text.startswith(u) for u in units):
                                boost *= 0.4 # Phạt vì tìm model mà ra dung lượng
            
            # --- CHIẾN LƯỢC 3: ƯU TIÊN VỊ TRÍ ĐẦU ---
            if query_terms and name_tokens and query_terms[0] == name_tokens[0]:
                boost *= 1.5
            
            # --- CHIẾN LƯỢC 4: LỌC PHỤ KIỆN ---
            if not query_has_accessory:
                # Nếu không tìm phụ kiện mà tên có phụ kiện ở ngay đầu, phạt cực nặng
                if any(t in accessory_keywords for t in name_tokens[:3]):
                    boost *= 0.05
                elif any(t in accessory_keywords for t in name_tokens):
                    boost *= 0.2
            
            # --- CHIẾN LƯỢC 5: ĐỘ PHỦ TỪ KHÓA QUAN TRỌNG ---
            match_count = sum(1 for t in important_query_terms if t in name_tokens)
            if len(important_query_terms) > 0:
                boost *= (1 + (match_count / len(important_query_terms)))

            final_results.append((doc_id, base_score * boost, query))
            
        final_results.sort(key=lambda x: x[1], reverse=True)
        return final_results[:top_k]
    
    def get_doc_info(self, doc_id: int, data_file: str = "data_1tr_clean_tokenized.jsonl") -> Dict:
        """
        Truy xuất thông tin document cực nhanh bằng f.seek() với byte offsets
        """
        if doc_id not in self.doc_offsets:
            with open(data_file, 'r', encoding='utf-8') as f:
                for current_id, line in enumerate(f):
                    if current_id == doc_id:
                        return json.loads(line.strip())
            return {}
            
        try:
            with open(data_file, 'rb') as f:
                f.seek(self.doc_offsets[doc_id])
                line = f.readline()
                return json.loads(line.decode('utf-8').strip())
        except Exception as e:
            print(f"Error retrieving doc {doc_id}: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    ranker = BM25Ranker(index_dir="index")
    
    # Test search
    results = ranker.search("airtag", top_k=10)
    
    print("="*80)
    print("TOP 10 RESULTS:")
    print("="*80)
    for rank, (doc_id, score, query_text) in enumerate(results, 1):
        doc = ranker.get_doc_info(doc_id)
        print(f"{rank}. [Score: {score:.4f}] {doc.get('product_name', 'N/A')}")
        print(f"   Platform: {doc.get('platform', 'N/A')} | Price: {doc.get('price', 'N/A'):,}đ")
        print(f"   Link: {doc.get('product_url', 'N/A')}")
        print()
