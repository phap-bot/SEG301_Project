# MILESTONE 2: CORE SEARCH ENGINE IMPLEMENTATION
## Executive Technical Report
**SEG301 — Search Engines & Information Retrieval**
**Project:** Smart Price Comparison Bot
**Team:** phap-bot

---

## 1. Problem Statement
After Milestone 1, the system successfully integrated **1,028,125 product records** from seven e-commerce platforms (~700MB). Managing this scale on standard hardware presents a primary challenge:

**Memory Limits (Indexing):** A typical computer cannot load 1 million records into memory at once. We need a way to process data in smaller pieces.

---

## 2. Indexing Architecture: SPIMI Algorithm
To solve memory issues, we implemented the **SPIMI (Single-Pass In-Memory Indexing)** algorithm. This allows the system to build a massive index while staying within defined memory limits.

### Workflow
1.  **Block Processing:** Documents are processed in blocks of 10,000.
2.  **Merging:** Block files are merged into one unified global index using a K-way merge (Heap-based).
3.  **Data Persistence:** Optimized JSON files for storage.

### Core Implementation (`spimi.py`)

#### Block Processing Logic:
```python
def process_block(self, documents: List[Dict]) -> Dict[str, Dict[int, int]]:
    inverted_index = defaultdict(lambda: defaultdict(int))
    for doc in documents:
        doc_id = self.total_docs
        tokens = doc.get('tokens', [])
        for token in tokens:
            sub_tokens = strip_accents(token).split()
            for sub_t in sub_tokens:
                if self._is_valid_term(sub_t):
                    inverted_index[sub_t][doc_id] += 1
        self.total_docs += 1
    return inverted_index
```

#### Memory-Efficient Merging:
```python
def merge_blocks(self):
    # Using heapq for K-way merge to keep memory usage low
    heap = []
    for i, it in enumerate(iterators):
        term, doc_tfs = next(it)
        heapq.heappush(heap, (term, i, doc_tfs))
    
    while heap:
        term, block_idx, doc_tfs = heapq.heappop(heap)
        final_index[term].update(doc_tfs)
        # Load next term from the same block
        next_term, next_doc_tfs = next(iterators[block_idx])
        heapq.heappush(heap, (next_term, block_idx, next_doc_tfs))
```

### Instant Retrieval
We store the **Byte Offset** of every document to jump directly to any product’s data using `f.seek()`.

---

## 3. Ranking System: BM25 Algorithm
The system uses the **BM25 (Best Match 25)** ranking function to ensure the most relevant products appear first.

### Key Ranking Factors
*   **Term Importance (IDF):** Rewards rare terms.
*   **Keyword Saturation:** Prevents score inflation from keyword repeating.
*   **Length Normalization:** Adjusts scores for title length differences.

| Parameter | Value | Role |
| :--- | :--- | :--- |
| **k1** | 2.0 | Limits influence of repeated keywords |
| **b** | 0.8 | Penalizes unnecessarily long titles |

### BM25 Calculation (`bm25.py`)
```python
def calculate_bm25_score(self, query_terms, doc_id, doc_tokens):
    score = 0
    doc_len = len(doc_tokens)
    for term in query_terms:
        if term not in self.inverted_index: continue
        idf = self.calculate_idf(term)
        tf = self.inverted_index[term].get(str(doc_id), 0)
        
        # BM25 Formula Implementation
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
        score += idf * (numerator / denominator)
    return score
```

---

## 4. Dynamic Query Processing: N-gram Splitting
A major highlight of our implementation is the **Dynamic N-gram Splitter**. This eliminates the need for hardcoded "stuck word" lists (e.g., `dienthoai`, `maygiat`).

### The Algorithm:
We use a **Weighted Shortest Path (Viterbi-style)** approach to find the most likely split points based on the inverted index.
*   **Candidate Generation**: Generates all possible N-gram combinations.
*   **Scoring**: Each segment is scored using `log(DF) * length^1.5`.
*   **Result**: Automatically splits `redminote13` -> `['redmi', 'note', '13']` without manual rules.

---

## 5. Intelligent Reranking
Custom rules refined for the Vietnamese marketplace.

| Strategy | Goal | Multiplier |
| :--- | :--- | :--- |
| **Proximity Boost** | Bonus for keywords appearing close together | **×1.3 to ×3.0** |
| **Position Boost** | Matches at the start of the product name | **×1.2** |
| **Universal Noise Penalty** | Penalize generic/spammy titles via IDF | **×0.5** |
| **Essential Term Check** | Penalize if key search terms are missing | **×0.1** |

---

## 6. System Performance Results
The system achieves high efficiency on standard hardware:

| Metric | Result |
| :--- | :--- |
| **Total Documents** | 1,028,125 |
| **Total Indexing Time** | 6m 39s |
| **Search Speed** | < 1s |
| **Peak Memory Usage** | < 500MB |
| **Total Index Size** | 175 MB |

---

## 7. Conclusion
Milestone 2 delivers a robust search engine built entirely from scratch. **SPIMI** enables efficient indexing of one million documents, while **Universal BM25** (no hardcoded word lists) combined with **Dynamic N-gram Splitting** ensures high accuracy and flexibility for any product category.

**Prepared by Team phap-bot**
