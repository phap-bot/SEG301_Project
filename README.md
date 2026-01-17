
***

```markdown
# SEG301 E-Commerce Search Engine Project

## 1. Team Information
**Group:** Group Tiki

| Name | Student ID | Role | Contribution | 
|------|-----------|------|--------------|
| Nguyễn Lê Tấn Pháp | QE190155 | Crawler Lead | Crawling Lazada & Điện Máy Xanh, anti-bot strategy |
| Tô Thanh Hậu | QE190039 | Crawler & Data Engineer | Crawling Tiki & Chợ Tốt, data normalization | 
| Nguyễn Hải Nam | QE190027 | Crawler | Crawling Lazada & CellphoneS, anti-bot detection | 

---

## 2. Project Description
This project implements an e-commerce search engine that aggregates product data from major Vietnamese e-commerce platforms. The system focuses on automated data collection, scalable indexing, and effective ranking methods.

### Key Functionalities
- **Data Collection:** Automated crawling with robust anti-bot detection handling.
- **Indexing:** Text indexing using the **SPIMI** algorithm.
- **Ranking:**
  - Keyword-based: **BM25** (handcoded).
  - Semantic-based: **Sentence Transformers**.
- **User Interface:** Web-based search interface and real-time monitoring dashboard.

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
- **Ranking:** Python (BM25 & Vector Models).
- **UI:** Streamlit (Python).
- **Database:** SQLite & JSONL files.

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
git clone https://github.com/your-group/SEG301-Project-GroupX
cd SEG301-Project-GroupX
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

**Step 3: Node.js Environment Setup (For Crawler)**
```bash
cd src/crawler/lazada
npm install
cd ../../..  # Return to root directory
```

---

## 5. Execution & Usage

### 5.1. Crawling Data
Navigate to the crawler directory and start the process:

```bash
cd src/crawler/lazada
node index.js
```

**Features:**
*   **Anti-bot Handling:**
    *   Automatic switching between `headless` and `visible` modes when CAPTCHA is detected.
    *   Detection of abnormal or empty search results.
*   **Persistence:** Automatic cookie saving/loading.

**Monitoring Dashboard:**
To view the real-time crawling status:
```bash
npm run web
```
> **Access:** [http://localhost:3000](http://localhost:3000)

**Configuration:**
Modify keywords in `src/crawler/lazada/config.json`:
```json
{
  "keywords": [
    "Man hinh may tinh",
    "Laptop gaming",
    "Chuot khong day"
  ]
}
```

### 5.2. Indexing & Ranking
Once data is collected, run the following scripts to build the index and calculate rankings:

1.  **Build Index (SPIMI):**
    ```bash
    python src/indexer/spimi.py
    ```
2.  **Run Ranking Algorithm (BM25):**
    ```bash
    python src/ranking/bm25.py
    ```

### 5.3. Search Interface
Launch the web application to search for products:

```bash
streamlit run src/ui/app.py
```

---

## 6. Dataset Description

### 6.1. Data Responsibilities
| Member | Platforms Assigned |
|--------|--------------------|
| **Nguyễn Lê Tấn Pháp** | Lazada, Điện Máy Xanh |
| **Tô Thanh Hậu** | Tiki, Chợ Tốt |
| **Nguyễn Hải Nam** | Lazada, CellphoneS |

### 6.2. Sample Dataset
Located in `data_sample/`. Contains 100–200 products per platform for testing.
*   `lazada_sample.jsonl`
*   `tiki_sample.jsonl`
*   `chotot_sample.jsonl`
*   `dienmayxanh_sample.jsonl`
*   `cellphones_sample.jsonl`

### 6.3. Data Schema
All datasets follow a unified JSON structure:

```json
{
  "platform": "lazada",
  "product_id": "123456",
  "name": "Product Name",
  "price": 1000000,
  "original_price": 1500000,
  "discount": 33,
  "url": "https://example.com/product/123",
  "rating": 4.5,
  "reviews": 120
}
```

### 6.4. Full Dataset Access
*   **Link:** `https://drive.google.com/...` (Update link)
*   **Total Size:** ~500MB (Compressed)
*   **Scale:** ~1,000,000 products
*   **Format:** JSONL and SQLite

> **Note:** This dataset is provided for academic purposes only.

---

## 7. Project Structure

```text
SEG301-Project-GroupX/
├── ai_log.md               # AI debugging logs
├── package.json            # Node.js dependencies
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── data_sample/            # Sample data files
│   ├── lazada_sample.jsonl
│   └── ...
│
├── src/                    # Source code
│   ├── crawler/            # Crawling scripts (Node/Python)
│   ├── indexer/            # SPIMI implementation
│   ├── ranking/            # BM25 & Semantic ranking
│   └── ui/                 # Streamlit App
│
└── tests/                  # Unit tests
```

---

## 8. Development Timeline

*   **Phase 1 (Weeks 1–4):**
    *   Setup environment.
    *   Implement crawlers for all platforms.
    *   Data cleaning and normalization.
*   **Phase 2 (Weeks 5–7):**
    *   Implement SPIMI indexing algorithm.
    *   Develop BM25 ranking and integrate semantic search.
*   **Phase 3 (Weeks 8–10):**
    *   Build Search UI (Streamlit).
    *   Final testing and presentation.

---

## 9. Credits & Attribution
*   **Lazada Crawler:** Adapted from [phap-bot/SEG301_Project](https://github.com/phap-bot/SEG301_Project).
*   **AI Assistance:** Debugging and bot-detection strategies are documented in `ai_log.md`.
```