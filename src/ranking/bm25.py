import json
import math
from collections import Counter
from typing import Dict, List, Tuple
import sys
import os

import unicodedata
from underthesea import word_tokenize


def normalize_text(text: str, remove_accents: bool = False, keep_underscore: bool = False) -> str:
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFC', text)
    if remove_accents:
        text = text.replace('đ', 'd')
        text = unicodedata.normalize('NFD', text)
        text = "".join([ch for ch in text if unicodedata.category(ch) != 'Mn'])
        text = unicodedata.normalize('NFC', text)
        if not keep_underscore:
            text = text.replace('_', ' ')
    return text

def strip_accents(s, keep_underscore=False):
   return normalize_text(s, remove_accents=True, keep_underscore=keep_underscore)


class BM25Ranker:
    
    def __init__(self, index_dir: str = "index", k1: float = 2.0, b: float = 0.8):
        self.index_dir = index_dir
        self.k1 = k1
        self.b = b
        
        self.inverted_index = None
        self.doc_lengths = None
        self.stats = None
        self.avg_doc_length = 0
        self.total_docs = 0
        
        self.load_index()
    
    def load_index(self):
        print("📚 Loading index...")
        index_file = f"{self.index_dir}/inverted_index.json"
        with open(index_file, 'r', encoding='utf-8') as f:
            raw_index = json.load(f)
        
        self.inverted_index = {}
        for term, doc_freqs in raw_index.items():
            self.inverted_index[term] = {int(doc_id): tf for doc_id, tf in doc_freqs.items()}
            
        print(f"  ✓ Loaded inverted index: {len(self.inverted_index):,} terms")
        
        metadata_file = f"{self.index_dir}/doc_metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            raw_lengths = json.load(f)
        self.doc_lengths = {int(k): v for k, v in raw_lengths.items()}
        print(f"  ✓ Loaded doc metadata: {len(self.doc_lengths):,} documents")
        
        stats_file = f"{self.index_dir}/index_stats.json"
        with open(stats_file, 'r', encoding='utf-8') as f:
            self.stats = json.load(f)
        
        self.total_docs = self.stats['total_documents']
        self.avg_doc_length = self.stats['average_doc_length']
        
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
        if term not in self.inverted_index:
            return 0.0
        df = len(self.inverted_index[term])
        idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
        return idf
    
    def calculate_tf(self, term: str, doc_id: int, doc_tokens: List[str]) -> int:
        return doc_tokens.count(term)
    
    def calculate_bm25_score(self, query_terms: List[str], doc_id: int, 
                            doc_tokens: List[str]) -> float:
        doc_len = len(doc_tokens)
        score = 0.0
        for term in query_terms:
            idf = self.calculate_idf(term)
            if idf == 0.0:
                continue
            tf = self.calculate_tf(term, doc_id, doc_tokens)
            if tf == 0:
                continue
            numerator = tf * (self.k1 + 1)
            length_norm = 1 - self.b + self.b * (doc_len / self.avg_doc_length)
            denominator = tf + self.k1 * length_norm
            term_score = idf * (numerator / denominator)
            score += term_score
        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float, str]]:
        segmented_query = word_tokenize(query.lower(), format="text")
        raw_query_terms = segmented_query.split()
        if not raw_query_terms: return []
            
        query_terms = []
        for t in raw_query_terms:
            # Chuẩn hóa không dấu nhưng GIỮ lại dấu gạch dưới (_) để khớp cụm từ
            norm_t = strip_accents(t, keep_underscore=True)
            query_terms.append(norm_t)
            
            # Nếu là từ ghép, thêm cả các từ thành phần để tăng kết quả (recall)
            if '_' in norm_t:
                query_terms.extend(norm_t.split('_'))
        
        # Bỏ trùng lặp
        query_terms = list(dict.fromkeys(query_terms))
        
        print(f"🔍 Searching: '{query}' (Terms: {query_terms})")
        
        # Intent Recognition
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
            
            # Coordination Factor
            unique_matches = sum(1 for q in important_q_terms if q in name_norm)
            if total_q_terms > 0:
                match_ratio = unique_matches / total_q_terms
                boost *= (match_ratio ** 2)
            
            # Phrase Match Boost
            if query_phrase in name_norm:
                boost *= 2.5
            
            # Position Boost
            if query_terms and norm_tokens:
                first_q = query_terms[0]
                if first_q not in stopwords and norm_tokens and norm_tokens[0] == first_q:
                    boost *= 1.5
            
            # Noise Word Penalty
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

            # Unit vs Model Distinction
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
