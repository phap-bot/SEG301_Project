# Auto sync (Windows Task Scheduler)

This project does **not** auto-sync by itself. Use Windows Task Scheduler to run the sync pipeline on a schedule.

## What the pipeline does

`scripts/sync_pipeline.ps1` runs:

1. *(Optional)* Run crawlers (best-effort)
2. Upload `data_1tr_clean_tokenized.jsonl` → Supabase `products` (upsert)
3. Rebuild BM25 index (`src/indexer/build_index.py`)
4. Rebuild Vector/FAISS index (`src/indexer/vector_indexer.py`)

Logs are written to `SEG301_Project/logs/`.

## Prerequisites

- Python available on PATH (`python`)
- `SEG301_Project/.env` contains `SUPABASE_URL` and `SUPABASE_KEY`
- Dependencies installed (at minimum: `supabase`, `python-dotenv`, plus indexer deps like `faiss`, `sentence-transformers`)

## Run manually (test first)

From `SEG301_Project/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_pipeline.ps1
```

Dry-run (test wiring without writing to Supabase, and skip heavy rebuild steps):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_pipeline.ps1 -DryRun -SkipBM25 -SkipVector
```

Optional: run crawlers too:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_pipeline.ps1 -RunCrawlers
```

## Create a Scheduled Task (GUI)

1. Open **Task Scheduler**
2. **Create Task...**
3. Tab **General**
   - Name: `PriceSaver Sync`
   - Run whether user is logged on or not
   - Run with highest privileges (recommended)
4. Tab **Triggers**
   - New... → Daily (or as needed)
5. Tab **Actions**
   - New...
   - **Program/script**: `powershell.exe`
   - **Add arguments**:
     - `-NoProfile -ExecutionPolicy Bypass -File "D:\Antigravity\SEG301\SEG301_Project\scripts\sync_pipeline.ps1"`
   - **Start in**:
     - `D:\Antigravity\SEG301\SEG301_Project`
6. Tab **Conditions/Settings**: tune as desired

## Create a Scheduled Task (CLI)

Run in an elevated PowerShell:

```powershell
$taskName = "PriceSaver Sync"
$ps1 = "D:\Antigravity\SEG301\SEG301_Project\scripts\sync_pipeline.ps1"

schtasks /Create /F /TN $taskName /SC DAILY /ST 02:00 `
  /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ps1`""
```

## Notes / common issues

- If you see a lock error, check `SEG301_Project/logs/sync.lock`. It prevents overlapping runs.
- If `python` is not on PATH for Scheduled Tasks, use a full path to python, e.g.:
  - `C:\Python311\python.exe`
- If the task runs but nothing updates, open the latest log in `SEG301_Project/logs/`.

