# MILESTONE 2 REPORT: CORE SEARCH ENGINE IMPLEMENTATION

**Course:** SEG301 - Search Engines & Information Retrieval  
**Project:** Smart Price Comparison Bot  
**Team:** phap-bot/SEG301_Project  
**Milestone:** 2 - Core Search Engine (Indexing & Ranking)

---

## 1. PROJECT OVERVIEW

Following the data acquisition phase in **Milestone 1** (over **1,028,125 products** from 7 e-commerce platforms), **Milestone 2** implements the "engine" of the system: High-volume Indexing and accurate Search Ranking.

### Key Objectives:
*   **Indexing**: Implement the SPIMI algorithm to handle 1M+ documents with limited RAM.
*   **Ranking**: From-scratch implementation of the BM25 algorithm for relevance scoring.
*   **Performance**: Achieve sub-0.5s search latency.
*   **Vietnamese Optimization**: Handle noise (accessories/used parts) and language normalization.

---

## 2. INDEXING ARCHITECTURE: SPIMI ALGORITHM

To process over 1 million records on a personal computer, we implemented the **Single-Pass In-Memory Indexing (SPIMI)** algorithm in `src/indexer/spimi.py`.

### 2.1. Implementation Workflow
1.  **Block-based Processing**: Data is read in chunks of 10,000 products to maintain a safe memory footprint.
2.  **In-Memory Construction**: For each block, a local Inverted Index is built, storing both Document IDs and Term Frequencies (TF).
3.  **Binary Serialization**: Once a block is complete, it is sorted by term (A-Z) and saved as a `.pkl` binary file to disk, immediately freeing up RAM.
4.  **K-Way Merge**: A streaming merge process uses a **Heap** (Priority Queue) to combine all blocks into a final consolidated index without loading all data into RAM at once.

### 2.2. Indexing Statistics
*   **Total Documents**: 1,028,125
*   **Vocabulary Size**: ~314,042 unique terms
*   **Indexing Time**: Approx. 5-10 minutes (depending on hardware).

---

## 3. RANKING SYSTEM: BM25 ALGORITHM

The ranking logic in `src/ranking/bm25.py` was built from scratch to allow deep customization for the Vietnamese e-commerce market.

### 3.1. Core Mathematical Formula
The system utilizes the industry-standard **BM25** relevance scoring:
$$Score(D, Q) = \sum_{q \in Q} IDF(q) \cdot \frac{f(q, D) \cdot (k_1 + 1)}{f(q, D) + k_1 \cdot (1 - b + b \cdot \frac{|D|}{avgdl})}$$

Where:
*   **IDF (Inverse Document Frequency)**: Weights rare terms (like "iPhone") higher than common terms (like "and").
*   **TF ($f(q, D)$)**: Term Frequency in the product name, boosting products that match the query multiple times (with saturation via $k_1$).
*   **Length Normalization**: Penalizes extremely long product names to prevent "keyword stuffing" (SEO spam) using parameters $b$ and $avgdl$.

### 3.2. Advanced Vietnamese Optimizations
We implemented "hardcore" logic to distinguish our engine from basic search tools:
*   **Noise Word Penalty**: Automatically detects "accessories" (cases, cables) or "scrap/used parts" (broken screens, skeletons) to demote them unless explicitly searched for.
*   **Model vs. Capacity Distinction**: Prevents confusion between model numbers (iPhone 16) and storage capacity (16GB).
*   **Byte Offsets**: Metadata maps store the exact byte position of products in the source file, allowing `f.seek()` for near-instant retrieval.

---

## 4. PERFORMANCE & RESULTS

The system was validated via the CLI application `compare_prices.py`:
*   **Search Latency**: Average **0.05s - 0.2s** across 1 million records.
*   **Accuracy**: Returns Top-10 relevant items with high precision, filtering out irrelevant noise.
*   **Stability**: Zero memory errors during the indexing of 1M+ documents due to the SPIMI architecture.

---

## 5. CONCLUSION

Milestone 2 successfully fulfills all technical requirements. By implementing SPIMI and BM25 from scratch, we have established a high-performance foundation capable of handling Big Data, ready for AI/LLM integration in Milestone 3.

---
**Prepared By:** Team phap-bot
