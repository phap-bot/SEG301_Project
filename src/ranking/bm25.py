import json
import math
import re
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
        self.split_cache = {}
        
        self.load_index()
    
    def load_index(self):
        print("Loading index...")
        index_file = f"{self.index_dir}/inverted_index.json"
        with open(index_file, 'r', encoding='utf-8') as f:
            raw_index = json.load(f)
        
        self.inverted_index = {}
        for term, doc_freqs in raw_index.items():
            self.inverted_index[term] = {int(doc_id): tf for doc_id, tf in doc_freqs.items()}
            
        print(f"  [OK] Loaded inverted index: {len(self.inverted_index):,} terms")
        
        metadata_file = f"{self.index_dir}/doc_metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            raw_lengths = json.load(f)
        self.doc_lengths = {int(k): v for k, v in raw_lengths.items()}
        print(f"  [OK] Loaded doc metadata: {len(self.doc_lengths):,} documents")
        
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
            print(f"  [OK] Loaded doc offsets: {len(self.doc_offsets):,} documents")
        except FileNotFoundError:
            print("  [WARN] Warning: doc_offsets.json not found. Search results retrieval will be slow.")
            self.doc_offsets = {}

        print(f"  [OK] Total docs: {self.total_docs:,}")
        print(f"  [OK] Avg doc length: {self.avg_doc_length:.2f}")
        print()

    def _split_stuck_word_dynamic(self, word: str) -> List[str]:
        """Sử dụng quy hoạch động để tách các từ dính chữ dựa trên tần suất trong index."""
        if not word: return []
        if word in self.split_cache: return self.split_cache[word]
        
        n = len(word)
        # dp[i] = (max_score, best_split_index)
        dp = [(-1.0, -1)] * (n + 1)
        dp[0] = (0.0, 0)
        
        for i in range(1, n + 1):
            for j in range(max(0, i - 15), i):
                part = word[j:i]
                
                is_valid = False
                part_score = 0
                
                if part in self.inverted_index:
                    is_valid = True
                    df = len(self.inverted_index[part])
                    # Tăng trọng số cho độ dài để tránh việc tách quá vụn (ví dụ: 'iphone' -> 'i', 'phone')
                    # Nhưng vẫn đủ để 'redmi' + 'note' thắng 'redminote'
                    part_score = math.log(df + 1) * (len(part) ** 1.8) 
                elif part.isdigit():
                    is_valid = True
                    # Phạt nhẹ các chuỗi số đơn lẻ để ưu tiên các từ có nghĩa
                    part_score = math.log(self.total_docs / 100 + 1) * (len(part) ** 1.2)
                
                if is_valid:
                    current_total_score = dp[j][0] + part_score
                    if current_total_score > dp[i][0]:
                        dp[i] = (current_total_score, j)
        
        if dp[n][1] == -1:
            return [word]
            
        result = []
        curr = n
        while curr > 0:
            prev = dp[curr][1]
            result.append(word[prev:curr])
            curr = prev
            
        final_splits = result[::-1]
        
        # Heuristic: Ưu tiên tách từ ngay cả khi từ đó tồn tại trong index, nếu việc tách mang lại độ phủ/trọng số tốt hơn.
        self.split_cache[word] = final_splits
        return final_splits
    
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
            norm_t = strip_accents(t, keep_underscore=True)
            if '_' not in norm_t:
                splits = self._split_stuck_word_dynamic(norm_t)
                if len(splits) > 1:
                    query_terms.extend(splits)
                    print(f"  [Auto-Split] '{norm_t}' -> {splits}")
                    continue
            
            query_terms.append(norm_t)
            
            # Nếu từ có dấu gạch dưới (từ underthesea), thêm cả các phần lẻ vào
            if '_' in norm_t:
                query_terms.extend(norm_t.split('_'))
        
        query_terms = [t for t in dict.fromkeys(query_terms) if len(t) > 1 or t.isdigit()]
        
        print(f"Searching: '{query}' (Terms: {query_terms})")
        
        term_metadata = {}
        for t in query_terms:
            if t in self.inverted_index:
                df = len(self.inverted_index[t])
                idf = self.calculate_idf(t)
                term_metadata[t] = {'df': df, 'idf': idf}
            else:
                term_metadata[t] = {'df': 0, 'idf': 0}

        dynamic_stopwords = {t for t, meta in term_metadata.items() if meta['df'] > self.total_docs * 0.05}
        
        valid_idfs = [meta['idf'] for meta in term_metadata.values() if meta['idf'] > 0]
        max_idf = max(valid_idfs) if valid_idfs else 0
        mean_idf = sum(valid_idfs) / len(valid_idfs) if valid_idfs else 0
        
        # Heuristic: Phát hiện các từ phụ (như phụ kiện) dựa trên IDF thấp so với đỉnh cao của query.
        potential_noise = {t for t, meta in term_metadata.items() if meta['idf'] < max_idf * 0.4 and t not in dynamic_stopwords}
        
        doc_scores = {}
        for term in query_terms:
            if term not in self.inverted_index:
                continue
            
            meta = term_metadata[term]
            idf = meta['idf']
            
            for doc_id, tf in self.inverted_index[term].items():
                doc_len = self.doc_lengths.get(doc_id, self.avg_doc_length)
                numerator = tf * (self.k1 + 1)
                length_norm = 1 - self.b + self.b * (doc_len / self.avg_doc_length)
                denominator = tf + self.k1 * length_norm
                
                score = idf * (numerator / denominator)
                
                # Phạt các từ là số (ví dụ: '1000') để tránh chúng chiếm ưu thế quá mức
                if term.isdigit():
                    score *= 0.2
                
                # Phạt các từ quá phổ biến nếu truy vấn có nhiều hơn 1 từ
                if len(query_terms) > 1 and df > self.total_docs * 0.05: score *= 0.3
                
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + score
        
        if not doc_scores:
            return []
            
        raw_top = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:200]
        print(f"   Smart Reranking top {len(raw_top)} results...")
        
        final_results = []
        
        important_q_terms = [t for t in query_terms if t not in dynamic_stopwords and len(t) > 1]
        if not important_q_terms: important_q_terms = query_terms[:]
        
        total_q_terms = len(important_q_terms)
        query_phrase = " ".join(query_terms)

        for doc_id, base_score in raw_top:
            doc = self.get_doc_info(doc_id)
            if not doc:
                continue
            
            doc_tokens = doc.get('tokens', [])
            norm_tokens = []
            for t in doc_tokens:
                norm_tokens.extend(strip_accents(t).split())
            
            # Normalized product name for comparison
            name_norm = strip_accents(doc.get('product_name', ''))
            name_tokens = name_norm.split()
            
            boost = 1.0

            # Bảo vệ truy vấn đơn lẻ
            if len(query_terms) == 1 and query_terms[0] not in dynamic_stopwords:
                q_term = query_terms[0]
                q_pos = name_tokens.index(q_term) if q_term in name_tokens else -1
                if q_pos > 3: boost *= 0.1
                if len(name_tokens) > 12: boost *= 0.5
            
            # 1. IDF-weighted Coordination Factor (Tỷ lệ khớp theo trọng số IDF)
            # Thưởng cho tài liệu chứa nhiều từ khóa, đặc biệt là các từ hiếm.
            query_term_idfs = {t: self.calculate_idf(t) for t in query_terms if t not in dynamic_stopwords}
            if not query_term_idfs: query_term_idfs = {t: self.calculate_idf(t) for t in query_terms}
            
            total_idf_sum = sum(query_term_idfs.values())
            matched_terms = [t for t in query_term_idfs if t in name_norm]
            matched_idf_sum = sum(query_term_idfs[t] for t in matched_terms)
            
            if total_idf_sum > 0:
                match_ratio = matched_idf_sum / total_idf_sum
                # Bình phương tỷ lệ để thưởng mạnh cho các tiêu đề khớp hoàn toàn
                boost *= (match_ratio ** 2)
            
            if len(matched_terms) == len(query_term_idfs) and len(query_term_idfs) > 1:
                boost *= 1.5

            # 2. Kiểm tra từ khóa thiết yếu (Failsafe)
            if query_term_idfs:
                non_numeric_idfs = {t: idf for t, idf in query_term_idfs.items() if not t.isdigit()}
                if not non_numeric_idfs: non_numeric_idfs = query_term_idfs
                
                max_idf = max(non_numeric_idfs.values())
                essential_terms = [t for t, idf in non_numeric_idfs.items() if idf > max_idf * 0.8]
                matched_essential = sum(1 for t in essential_terms if t in name_norm)
                if len(essential_terms) > 0 and (matched_essential / len(essential_terms)) < 0.7:
                    # Phạt nếu thiếu quá nhiều từ khóa thiết yếu
                    boost *= 0.1

            # 3. Thưởng cho từ khóa đứng gần nhau (Không phân biệt thứ tự)
            # Tìm cửa sổ nhỏ nhất chứa càng nhiều từ khóa càng tốt
            if len(query_terms) > 1:
                positions = []
                for q_term in query_terms:
                    if q_term in dynamic_stopwords: continue
                    # Find all positions of this query term in the name
                    pos_list = [i for i, t in enumerate(name_tokens) if t == q_term]
                    if pos_list:
                        positions.append(pos_list)
                
                if len(positions) >= 2:
                    # Tính toán độ gần: các từ cách nhau bao xa?
                    # Kiểm tra các cặp liền kề (khoảng cách 1) hoặc gần kề (khoảng cách 2)
                    min_dist = 999
                    for i in range(len(positions)):
                        for j in range(i + 1, len(positions)):
                            for p1 in positions[i]:
                                for p2 in positions[j]:
                                    dist = abs(p1 - p2)
                                    if dist < min_dist: min_dist = dist
                    
                    if min_dist == 1:
                        boost *= 3.0 # Đứng sát nhau (như một cụm từ, bất kể thứ tự)
                    elif min_dist == 2:
                        boost *= 2.0 # Cách nhau 1 từ
                    elif min_dist <= 4:
                        boost *= 1.3 # Tương đối gần
            
            if query_terms and norm_tokens:
                # Vị trí xuất hiện
                first_two_q = set(query_terms[:2])
                first_two_doc = set(norm_tokens[:2])
                if first_two_q.intersection(first_two_doc):
                    boost *= 1.2
            
            # Hình phạt động cho "Nhiễu" và Chất lượng
            doc_noise_count = sum(1 for t in name_tokens if self.calculate_idf(t) < 1.0)
            if doc_noise_count > 5:
                boost *= 0.5
            
            # Nếu tiêu đề quá dài mà query quá ngắn, có khả năng là mô tả rác (spam)
            if len(query_terms) <= 2 and len(name_tokens) > 15:
                boost *= 0.5

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
