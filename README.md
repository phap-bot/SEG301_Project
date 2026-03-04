
# SEG301 E-Commerce Search Engine Project

## 1. Team Information
**Group:** 

| Name | Student ID | Role | Contribution | 
|------|-----------|------|--------------|
| Nguyễn Lê Tấn Pháp | QE190155 | Crawler Lead | Crawling Lazada & Điện Máy Xanh |
| Tô Thanh Hậu | QE190039 | Crawler | Crawling Tiki & Chợ Tốt & eBay | 
| Nguyễn Hải Nam | QE190027 | Crawler | Crawling Lazada & CellphoneS | 

---

## 2. Project Description
This project implements an e-commerce search engine that aggregates product data from major Vietnamese e-commerce platforms. The system focuses on automated data collection, scalable indexing, and effective ranking methods.

### Key Functionalities
- **Data Collection:** Automated crawling with robust anti-bot detection handling.
- **Indexing:** Text indexing using the **SPIMI** algorithm.
- **Ranking:** Keyword-based **BM25** (handcoded).

### Supported Platforms
The system aggregates data from:
- Lazada
- Tiki
- Chợ Tốt
- Điện Máy Xanh
- CellphoneS

---

## 3. System Architecture & Technologies
The system follows a modular pipeline design:

### Tech Stack
- **Crawler:**
  - *Node.js:* Playwright (with Stealth plugin).
  - *Python:* Selenium.
- **Indexer:** Python (Custom SPIMI implementation).
- **Ranking:** Python (BM25).
- **Database:** JSONL files.

---

## 4. Installation & Environment Setup

### 4.1. Requirements
Ensure you have the following installed:
- Node.js (>= version 18)
- Python (>= version 3.9)
- Git

### 4.2. Step-by-Step Setup

**Step 1: Clone the repository**
```bash
git clone https://github.com/phap-bot/SEG301_Project
cd SEG301_Project
```

**Step 2: Python Environment Setup**
```bash
# Create virtual environment
python -m venv venv

# Activate environment
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 5. Execution & Usage

### 5.1. Crawling Data
Navigate to the specific crawler directory and start the process:

- **Example for Lazada:**
  ```bash
  cd src/crawler/Crawl_lazada
  node index.js
  ```
- **Example for Shopee (or other Python crawlers):**
  ```bash
  python src/crawler/Crawl_eBay/spider.py
  ```

### 5.2. Chạy Indexing & Ranking
Sau khi đã thu thập dữ liệu, bạn cần chạy các script sau để xây dựng chỉ mục và tính toán thứ hạng:

1.  **Xây dựng Index (SPIMI):**
    ```bash
    python src/indexer/build_index.py
    ```
2.  **Chạy thuật toán xếp hạng (BM25):**
    ```bash
    python src/ranking/bm25.py
    ```

---

## 6. Dataset Description

### 6.1. Data Responsibilities
| Member | Platforms Assigned |
|--------|--------------------|
| **Nguyễn Lê Tấn Pháp** | Lazada, Điện Máy Xanh, FPTShop |
| **Tô Thanh Hậu** | Tiki, Chợ Tốt, eBay  |
| **Nguyễn Hải Nam** | Lazada, CellphoneS |

### 6.2. Sample Dataset
Located in `data_sample/`. Contains 100–200 products per platform for testing.

### 6.3. Full Dataset Access
*   **Link:** [Google Drive Download](https://drive.google.com/file/d/1U9lkNUmLp5H08vthkfQKPEZ2oy1ZIkAM/view?usp=sharing)
*   **Total Size:** ~500MB (Compressed)
*   **Scale:** ~1,000,000 products

---

## 7. Project Structure

```text
SEG301-Project-GroupX/
├── .gitignore               # Cấu hình git ignore
├── README.md                # Hướng dẫn dự án
├── ai_log.md                # Nhật ký sử dụng AI
├── requirements.txt         # Thư viện cần thiết
├── data_1tr_clean_tokenized.jsonl # File dữ liệu lớn
├── index/                   # Thư mục chứa chỉ mục (inverted index)
├── data_sample/             # Dữ liệu mẫu
│   └── sample.jsonl
├── docs/                    # Báo cáo và giải thích thuật toán
│   ├── Milestone1_Report.pdf
│   └── Search_Explained.md
└── src/                     # Source code chính
    ├── crawler/             # Milestone 1: Thu thập dữ liệu
    │   ├── parser.py        # Tiền xử lý
    │   └── merge.py         # Gộp dữ liệu từ các platform
    ├── indexer/             # Milestone 2: Tạo chỉ mục
    │   ├── spimi.py         # Thuật toán SPIMI
    │   └── build_index.py   # Script thực thi build index
    └── ranking/             # Milestone 2: Xếp hạng
        └── bm25.py          # Thuật toán BM25 (Code tay)
```

---

## 8. Development Timeline

*   **Phase 1 (Weeks 1–4):**
    *   Setup environment.
    *   Implement crawlers for all platforms.
    *   Data cleaning and normalization.
*   **Phase 2 (Weeks 5–7):**
    *   Implement SPIMI indexing algorithm.
    *   Develop BM25 ranking.
*   **Phase 3 (Weeks 8–10):**
    *   Build Search UI.
    *   Final testing and presentation.

---

## 9. Credits & Attribution
*   **AI Assistance:** Debugging and bot-detection strategies are documented in `ai_log.md`.
