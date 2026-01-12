# SEG301 E-Commerce Search Engine Project

## Team Information
**Group:** Group X  
**Members:**

| Name | Student ID | Role | Contribution | Original Repo |
|------|-----------|------|--------------|---------------|
| Phap | SEXXXXXX | Crawler Lead (Lazada) | Milestone 1: Lazada crawler với anti-bot detection | [phap-bot/SEG301_Project](https://github.com/phap-bot/SEG301_Project) |
| [Bạn A] | SEXXXXXX | Crawler (Platform 2) | Milestone 1: [Platform] crawler | - |
| [Bạn B] | SEXXXXXX | Indexer | Milestone 2: SPIMI implementation | - |
| [Bạn C] | SEXXXXXX | Ranking & UI | Milestone 2 & 3: BM25 + Semantic Search + UI | - |

## Project Overview
Search engine cho sản phẩm e-commerce từ Lazada và các platform khác với khả năng:
- ✅ Thu thập dữ liệu tự động từ nhiều platform (anti-bot detection)
- ✅ Tạo chỉ mục với SPIMI algorithm
- ✅ Xếp hạng với BM25 và Semantic Search
- ✅ Giao diện web thân thiện với dashboard

## Tech Stack
- **Crawler**: Node.js (Playwright with Stealth) + Python (Selenium)
- **Indexer**: Python (SPIMI handcoded)
- **Ranking**: Python (BM25 handcoded + Sentence Transformers)
- **UI**: Streamlit / Web Dashboard
- **Database**: SQLite

## Installation

### Prerequisites
- Node.js >= 18.0
- Python >= 3.9
- Git

### Setup

#### 1. Clone repository
```bash
git clone https://github.com/your-group/SEG301-Project-GroupX
cd SEG301-Project-GroupX
```

#### 2. Install Python dependencies (for Milestone 2 & 3)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

#### 3. Install Node.js dependencies (for crawlers)
```bash
# Install dependencies for Lazada crawler
cd src/crawler/lazada
npm install
cd ../../..
```

## Usage

### Milestone 1: Data Collection

#### Run Lazada Crawler
```bash
cd src/crawler/lazada
node index.js
```

**Features:**
- ✅ Auto-detect và switch headless/visible mode cho CAPTCHA
- ✅ Phát hiện bot detection ("Tìm kiếm không có kết quả")
- ✅ Tự động lưu cookies
- ✅ Web dashboard để monitor tiến trình

**Access Dashboard:**
```bash
cd src/crawler/lazada
npm run web
# Open http://localhost:3000
```

#### Configure keywords
Edit `src/crawler/lazada/config.json`:
```json
{
  "keywords": [
    "Man hinh may tinh",
    "Laptop gaming",
    "Chuot khong day"
  ]
}
```

### Milestone 2: Indexing & Ranking
```bash
# TODO: Implement SPIMI indexer
python src/indexer/spimi.py

# TODO: Implement BM25 ranking
python src/ranking/bm25.py
```

### Milestone 3: Search UI
```bash  
# TODO: Implement search UI
streamlit run src/ui/app.py
```

## Dataset
- **Sample Data**: `data_sample/` (100-200 products for testing)
- **Full Dataset**: [📥 Download from Google Drive](https://drive.google.com/...) 
  - ~500MB compressed
  - ~1M products from Lazada
  - Format: SQLite database + JSONL

## Project Structure
```
SEG301-Project-GroupX/
├── .gitignore
├── README.md
├── ai_log.md              # AI usage tracking
├── requirements.txt       # Python dependencies
├── package.json          # Node.js workspace config
│
├── docs/                 # Reports & presentations
│   ├── Milestone1_Report.pdf
│   ├── Milestone2_Report.pdf
│   └── Milestone3_Presentation.pdf
│
├── data_sample/          # Sample data for testing
│   └── lazada_sample.jsonl
│
├── src/
│   ├── crawler/          # Milestone 1: Data collection
│   │   └── lazada/       # Lazada crawler (by Phap)
│   │       ├── index.js
│   │       ├── src/
│   │       │   ├── crawlers/lazada.js
│   │       │   └── utils/
│   │       └── web/      # Dashboard
│   │
│   ├── indexer/          # Milestone 2: SPIMI indexing
│   │   └── spimi.py
│   │
│   ├── ranking/          # Milestone 2 & 3: Ranking
│   │   ├── bm25.py
│   │   └── vector.py
│   │
│   └── ui/               # Milestone 3: Search interface
│       └── app.py
│
└── tests/                # Unit tests
    ├── test_spimi.py
    └── test_bm25.py
```

## Development Timeline
- **Milestone 1** (Week 1-3): Data Collection ✅
- **Milestone 2** (Week 4-6): Indexing & Ranking
- **Milestone 3** (Week 7-9): Search UI & Presentation

## Credits & Attribution
- **Lazada Crawler**: Developed by Phap, original repo: https://github.com/phap-bot/SEG301_Project
- **Bot Detection Fix**: Implemented with assistance from Google Gemini AI (see `ai_log.md`)

## License
MIT License - SEG301 Project 2026
