import json
import os
import time
from collections import defaultdict
from typing import Dict, List, Tuple
import heapq
import unicodedata
from underthesea import word_tokenize

def strip_accents(s, keep_underscore=False):
   if not s: return ""
   s = s.lower()
   s = s.replace('đ', 'd')
   s = "".join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
   
   if keep_underscore:
       return s
   
   return s.replace('_', ' ')

class SPIMIIndexer:
    
    def __init__(self, block_size: int = 10000, output_dir: str = "index"):
        self.block_size = block_size
        self.output_dir = output_dir
        self.block_count = 0
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "blocks"), exist_ok=True)
        
        self.total_docs = 0
        self.total_terms = 0
        self.total_tokens = 0
        self.doc_lengths = {}
        
    def process_block(self, documents: List[Dict]) -> Dict[str, Dict[int, int]]:
        inverted_index = defaultdict(lambda: defaultdict(int))
        
        for doc in documents:
            doc_id = self.total_docs
            tokens = doc.get('tokens')
            
            if tokens is None or not tokens:
                product_name = doc.get('product_name', '')
                if product_name:
                    segmented = word_tokenize(product_name, format="text")
                    tokens = segmented.split()
                else:
                    tokens = []
            
            self.doc_lengths[doc_id] = len(tokens)
            self.total_tokens += len(tokens)
            
            for token in tokens:
                clean_token = strip_accents(token, keep_underscore=True)
                if self._is_valid_term(clean_token):
                    inverted_index[clean_token][doc_id] += 1
                
                if '_' in clean_token:
                    sub_tokens = clean_token.split('_')
                    for sub_t in sub_tokens:
                        if self._is_valid_term(sub_t):
                            inverted_index[sub_t][doc_id] += 1
            
            self.total_docs += 1
        
        return {term: dict(doc_freqs) for term, doc_freqs in inverted_index.items()}
    
    def _is_valid_term(self, term: str) -> bool:
        if not term or len(term) < 2:
            return False
        if term.startswith('http://') or term.startswith('https://'):
            return False
        if term.replace('.', '').replace('_', '').isdigit():
            try:
                val = float(term.replace('_', '')) if '_' in term else float(term)
                if val > 5000:
                    return False
                if val < 1:
                    return False
            except ValueError:
                return True
                
        if term in [':', '/', '.', ',', '-', '+', '(', ')', '[', ']', 'với', 'cho', 'của', 'và']:
            return False
        return True
    
    def write_block_to_disk(self, inverted_index: Dict[str, List[int]], block_id: int):
        block_file = os.path.join(self.output_dir, "blocks", f"block_{block_id:03d}.json")
        
        sorted_index = dict(sorted(inverted_index.items()))
        
        with open(block_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_index, f, ensure_ascii=False)
        
        print(f"  ✓ Wrote block {block_id}: {len(sorted_index)} unique terms")
    
    def merge_blocks(self) -> Dict[str, Dict[int, int]]:
        print(f"\n🔗 Merging {self.block_count} blocks using K-way merge...")
        
        block_files = []
        iterators = []
        
        for i in range(self.block_count):
            path = os.path.join(self.output_dir, "blocks", f"block_{i:03d}.json")
            f = open(path, 'r', encoding='utf-8')
            block_files.append(f)
            block_data = json.load(f)
            iterators.append(iter(sorted(block_data.items())))
        
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
            
            final_index[term].update(doc_tfs)
            
            try:
                next_term, next_doc_tfs = next(iterators[block_idx])
                heapq.heappush(heap, (next_term, block_idx, next_doc_tfs))
            except StopIteration:
                pass
        
        for f in block_files:
            f.close()
            
        print(f"  ✓ Merged into {len(final_index)} unique terms")
        return final_index
    
    def build_index(self, input_file: str) -> dict:
        print(f"🚀 Starting SPIMI Indexing")
        print(f"   Input: {input_file}")
        print(f"   Block size: {self.block_size:,} documents")
        print()

        timing = {}

        doc_offsets = {}

        # ── Phase 1: Block Processing ──────────────────────────────────────────
        print("📦 Phase 1: Processing blocks...")
        current_block = []
        t1_start = time.time()

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

        # ── Phase 2: Merge ──────────────────────────────────────────────────────
        timing["phase2_merge"] = time.time() - t2_start
        print(f"  ⏱  Phase 2 done in {timing['phase2_merge']:.2f}s")

        # ── Phase 3: Save ──────────────────────────────────────────────────────
        print("\n💾 Phase 3: Saving final files...")
        t3_start = time.time()

        with open(os.path.join(self.output_dir, "inverted_index.json"), 'w', encoding='utf-8') as f:
            json.dump(final_index, f, ensure_ascii=False)

        with open(os.path.join(self.output_dir, "doc_metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(self.doc_lengths, f, ensure_ascii=False)

        with open(os.path.join(self.output_dir, "doc_offsets.json"), 'w', encoding='utf-8') as f:
            json.dump(doc_offsets, f, ensure_ascii=False)

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
    indexer = SPIMIIndexer(block_size=10000, output_dir="index")
    indexer.build_index("data_1tr_clean_tokenized.jsonl")
