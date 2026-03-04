"""
BM25 Ranking Algorithm Implementation
Code tay hoàn toàn - KHÔNG dùng thư viện rank() có sẵn
"""

import json
import math
from collections import Counter
from typing import Dict, List, Tuple
import sys
import os

import unicodedata


def normalize_text(text: str, remove_accents: bool = False) -> str:
    if not text:
        return ""
    # 1. Lowercase
    text = text.lower()
    # 2. Chuẩn hóa Unicode NFC
    text = unicodedata.normalize('NFC', text)
    if remove_accents:
        # 3. Remove accent (nếu muốn search không dấu)
        # Xử lý đ -> d thủ công vì NFD không tách được đ
        text = text.replace('đ', 'd')
        # NFD separates accents from base characters
        text = unicodedata.normalize('NFD', text)
        text = "".join([ch for ch in text if unicodedata.category(ch) != 'Mn'])
        text = unicodedata.normalize('NFC', text)
        # Đồng bộ dấu gạch dưới thành khoảng trắng
        text = text.replace('_', ' ')
    return text

def strip_accents(s):
   """Loại bỏ dấu tiếng Việt mạnh mẽ (bao gồm cả đ -> d) và đồng bộ dấu gạch dưới"""
   return normalize_text(s, remove_accents=True)


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
        index_file = f"{self.index_dir}/inverted_index.json"
        with open(index_file, 'r', encoding='utf-8') as f:
            raw_index = json.load(f)
        
        # Chuyển đổi inner keys từ string sang int (doc_id)
        self.inverted_index = {}
        for term, doc_freqs in raw_index.items():
            self.inverted_index[term] = {int(doc_id): tf for doc_id, tf in doc_freqs.items()}
            
        print(f"  ✓ Loaded inverted index: {len(self.inverted_index):,} terms")
        
        # Load document metadata
        metadata_file = f"{self.index_dir}/doc_metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            raw_lengths = json.load(f)
        self.doc_lengths = {int(k): v for k, v in raw_lengths.items()}
        print(f"  ✓ Loaded doc metadata: {len(self.doc_lengths):,} documents")
        
        # Load statistics
        stats_file = f"{self.index_dir}/index_stats.json"
        with open(stats_file, 'r', encoding='utf-8') as f:
            self.stats = json.load(f)
        
        self.total_docs = self.stats['total_documents']
        self.avg_doc_length = self.stats['average_doc_length']
        
        # Load doc offsets
        offsets_file = f"{self.index_dir}/doc_offsets.json"
        try:
            with open(offsets_file, 'r', encoding='utf-8') as f:
                raw_offsets = json.load(f)
            self.doc_offsets = {int(k): v for k, v in raw_offsets.items()}
            print(f"  ✓ Loaded doc offsets: {len(self.doc_offsets):,} documents")
        except FileNotFoundError:
            print("  ⚠️ Warning: doc_offsets.json not found. Search results retrieval will be slow.")
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
        Search thông minh: BM25 + Intent Recognition + Smart Reranking
        """
        raw_query_terms = query.lower().split()
        if not raw_query_terms:
            return []
            
        # Chuẩn hóa query không dấu và TÁCH rời các từ ghép để khớp index tốt nhất
        # Vd: ['dien_thoai'] -> ['dien', 'thoai']
        query_terms = []
        for t in raw_query_terms:
            norm_t = strip_accents(t).replace('_', ' ')
            query_terms.extend(norm_t.split())
        
        # Bỏ trùng lặp
        query_terms = list(dict.fromkeys(query_terms))
        
        print(f"🔍 Searching: '{query}' (Terms: {query_terms})")
        # DEBUG:
        # print(f"DEBUG: Index keys sample: {list(self.inverted_index.keys())[:10]}")
        
        # 1. Intent Recognition: Nhận diện ý định (Sử dụng bộ NOISE_WORDS toàn diện)
        NOISE_WORDS = {
            'xac', 'vo', 'op', 'man', 'kinh', 'cuong', 'dan', 'mieng', 'tam', 
            'sac', 'cap', 'day', 'dock', 'hub', 'adapter', 'tai', 'nguyen',
            'phu', 'lop', 'vanh', 'gioang', 'loi', 'may', 'dong', 'nhot', 'dau', 'giam',
            'pin', 'ram', 'ssd', 'hdd', 'ban', 'phim', 'quat', 'led', 'tui', 'balo',
            'tinh', 'lot', 'giay', 'tham', 'nap', 'khoa', 'bong', 'cuc', 'chi', 'vai',
            'hu', 'hong', 'be', 'vo', 'nat', 'chai', 'cu', 'second', 'used', 'thao', 'doi'
        }
        units = {'gb', 'tb', 'mb', 'ram', 'ssd', 'hdd'}
        
        query_has_unit = any(t in units for t in query_terms)
        # Nếu query có bất kỳ từ nào thuộc NOISE_WORDS -> User đang CHỦ ĐỘNG tìm phụ kiện
        query_has_accessory = any(t in NOISE_WORDS for t in query_terms)
        
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
        
        # Stopwords KHÔNG DẤU (vì cả index lẫn query đã được chuẩn hóa)
        stopwords = {'cai', 'chiec', 'con', 'bo', 'ra', 'voi', 'va', 'cho', 'moi', 'gia', 're', 'ban', 'thanh', 'ly', 'dich', 'vu'}
        
        # Query đã là list từ không dấu, tính coordination factor
        important_q_terms = [t for t in query_terms if t not in stopwords and len(t) > 1]
        if not important_q_terms: important_q_terms = query_terms[:]
        
        total_q_terms = len(important_q_terms)
        query_phrase = " ".join(query_terms)  # Cụm query không dấu

        for doc_id, base_score in raw_top:
            doc = self.get_doc_info(doc_id)
            if not doc:
                continue
            
            # Doc tokens đã được chuẩn hóa không dấu trong file data
            doc_tokens = doc.get('tokens', [])
            # Chuẩn hóa thêm cho chắc (phòng trường hợp token cũ còn dấu)
            norm_tokens = []
            for t in doc_tokens:
                norm_tokens.extend(strip_accents(t).split())
            
            # Tên sản phẩm gốc -> chuẩn hóa không dấu để so sánh
            name_norm = strip_accents(doc.get('product_name', ''))
            
            boost = 1.0
            
            # --- CHIẾN LƯỢC 1: COORDINATION FACTOR ---
            unique_matches = sum(1 for q in important_q_terms if q in name_norm)
            if total_q_terms > 0:
                match_ratio = unique_matches / total_q_terms
                boost *= (match_ratio ** 2)
            
            # --- CHIẾN LƯỢC 2: PHRASE MATCH BOOST ---
            if query_phrase in name_norm:
                boost *= 2.5
            
            # --- CHIẾN LƯỢC 3: ƯU TIÊN VỊ TRÍ ĐẦU ---
            if query_terms and norm_tokens:
                first_q = query_terms[0]
                if first_q not in stopwords and norm_tokens and norm_tokens[0] == first_q:
                    boost *= 1.5
            
            # --- CHIẾN LƯỢC 4: BLACKLIST TỪ NHIỄU (Noise Word Penalty) ---
            if not query_has_accessory:
                # Quét xem có từ nào trong tên thuộc NOISE_WORDS không
                all_name_tokens = name_norm.split()
                # Phạt nặng hơn nếu từ nhiễu ở ngay đầu
                first3 = set(all_name_tokens[:3])
                anywhere = set(all_name_tokens)

                noise_in_front  = sum(1 for t in first3 if t in NOISE_WORDS)
                noise_elsewhere = sum(1 for t in anywhere if t in NOISE_WORDS) - noise_in_front

                if noise_in_front >= 1:
                    boost *= (0.05 ** noise_in_front) # Phạt cực nặng nếu "Xác..." đứng đầu
                elif noise_elsewhere >= 1:
                    boost *= (0.35 ** noise_elsewhere) # Phạt vừa nếu "điện thoại ... xác"

            # --- CHIẾN LƯỢC 5: PHÂN BIỆT MODEL VS DUNG LƯỢNG (Unit vs Model) ---
            # Ví dụ: Tìm "iphone 16" thì không nên ra "iphone 6 16gb"
            if not query_has_unit:
                for i, t in enumerate(norm_tokens):
                    # Nếu từ trong doc khớp với một từ trong query (mà từ đó là số)
                    if t in query_terms and t.isdigit():
                        # Kiểm tra xem từ ngay sau nó trong doc có phải là đơn vị (gb, ram...) không
                        if i + 1 < len(norm_tokens) and norm_tokens[i+1] in units:
                            boost *= 0.1 # Phạt nặng vì đây là khớp dung lượng, không phải khớp model
                            break


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
    results = ranker.search("dien thoai", top_k=10)
    
    print("="*80)
    print("TOP 10 RESULTS:")
    print("="*80)
    for rank, (doc_id, score, query_text) in enumerate(results, 1):
        doc = ranker.get_doc_info(doc_id)
        print(f"{rank}. [Score: {score:.4f}] {doc.get('product_name', 'N/A')}")
        print(f"   Platform: {doc.get('platform', 'N/A')} | Price: {doc.get('price', 'N/A'):,}đ")
        print(f"   Link: {doc.get('product_url', 'N/A')}")
        print()
