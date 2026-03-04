# MILESTONE 2: CORE SEARCH ENGINE IMPLEMENTATION
## Executive Technical Report

---

### 1. Problem Statement

After Milestone 1, the system successfully integrated **1,028,125 product records** from seven e-commerce platforms (approx. 700MB). Managing this scale on standard hardware presents two primary challenges:

1.  **Memory Limits (Indexing)**: A typical computer cannot load 1 million records into memory at once. We need a way to process data in smaller pieces.
2.  **Search Relevance (Ranking)**: Keyword matching alone often fails to filter out "noise" like scrap parts or mismatched capacities (e.g., finding "16GB" when searching for "iPhone 16").

---

### 2. Indexing Architecture: SPIMI Algorithm

To solve memory issues, we implemented the **SPIMI (Single-Pass In-Memory Indexing)** algorithm. This allows the system to build a massive index while staying within defined memory limits.

-   **Workflow**:
    1.  **Block Processing**: The dataset is processed in small blocks of 10,000 documents. For each block, a local index is built in memory.
    2.  **Merging**: The system then merges these block files into one unified global index using a smart merging process that requires very little memory.
    3.  **Data Persistence**: The final index and metadata are saved as optimized JSON files for permanent storage.
-   **Instant Retrieval**: During indexing, we store the exact position (Byte Offset) of every document in the source file. This allows the system to jump directly to any product's data instantly without reading the entire file.

---

### 3. Ranking System: BM25 Algorithm

The system uses the **BM25 (Best Match 25)** ranking function to ensure the most relevant products appear first.

#### **Key Ranking Factors**
-   **Term Importance (IDF)**: Rewards rare terms (like specific model numbers) and gives less weight to common words.
-   **Keyword Saturation**: Prevents product titles from ranking higher just by repeating the same keyword many times.
-   **Length Normalization**: Adjusts scores to ensure concise titles are treated fairly compared to long, noisy ones.

| Parameter | Value | Role |
| :--- | :--- | :--- |
| **$k_1$** | 2.0 | Limits the influence of repeated keywords. |
| **$b$** | 0.8 | Penalizes titles that are unnecessarily long. |

---

### 4. Intelligent Reranking

After the initial ranking, we apply custom rules to further refine the results for the Vietnamese market:

| Strategy | Goal | Multiplier |
| :--- | :--- | :--- |
| **Phrase Match** | Bonus for exact consecutive words | $\times 2.5$ |
| **Position Priority** | Bonus for keywords at the start of the title | $\times 1.5$ |
| **Noise Filtering** | Penalizing "scrap" or "accessory" listings | $\times 0.05$ |
| **Unit Check** | Penalizing storage capacity mismatches | $\times 0.1$ |

---

### 5. System Performance Results

The system achieves high efficiency on standard hardware:

| Metric | Result |
| :--- | :--- |
| **Total Documents** | **1,028,125** |
| **Total Indexing Time** | **3m 46s** |
| **Search Speed** | **0.05s – 0.20s** (Instant) |
| **Peak Memory Usage** | **< 500MB** (Indexing) |
| **Total Index Size** | **175 MB** |

---

### 6. Conclusion

Milestone 2 delivers a robust search engine built from scratch. SPIMI allows us to index 1 million documents quickly and safely, while BM25 combined with custom reranking ensures high accuracy for product searches.

**Prepared by Team phap-bot**
