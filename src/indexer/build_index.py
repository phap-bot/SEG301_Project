import sys
import os
import argparse
import time
import json
import datetime
from spimi import SPIMIIndexer


def get_file_size_mb(path: str) -> float:
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except FileNotFoundError:
        return 0.0


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.1f}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}h {m}m {s:.1f}s"


def main():
    parser = argparse.ArgumentParser(
        description='Build search index using SPIMI algorithm'
    )
    parser.add_argument(
        '--input',
        default='data_1tr_clean_tokenized.jsonl',
        help='Input JSONL file (supports raw data or tokenized data)'
    )
    parser.add_argument(
        '--output',
        default='index',
        help='Output directory for index files (default: index/)'
    )
    parser.add_argument(
        '--block-size',
        type=int,
        default=1000,
        help='Documents per block (default: 1000)'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    print("🏗️  BUILD INDEX CONFIGURATION")
    print("="*80)
    print(f"Input file:  {args.input}")
    print(f"Output dir:  {args.output}")
    print(f"Block size:  {args.block_size:,} documents")
    print("="*80)
    print()

    # Confirm before proceeding
    if not args.yes:
        response = input("Proceed with indexing? [Y/n]: ").strip().lower()
        if response and response not in ['y', 'yes']:
            print("Cancelled.")
            return

    print()

    # ─── Bắt đầu tính giờ tổng ───────────────────────────────────────────────
    wall_start = time.time()
    started_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build index (spimi trả về dict timing từng phase)
    indexer = SPIMIIndexer(block_size=args.block_size, output_dir=args.output)
    timing = indexer.build_index(args.input)

    wall_end = time.time()
    total_elapsed = wall_end - wall_start

    output_files = {
        "inverted_index.json": os.path.join(args.output, "inverted_index.json"),
        "doc_metadata.json":   os.path.join(args.output, "doc_metadata.json"),
        "doc_offsets.json":    os.path.join(args.output, "doc_offsets.json"),
        "index_stats.json":    os.path.join(args.output, "index_stats.json"),
    }
    file_sizes = {name: get_file_size_mb(path) for name, path in output_files.items()}
    total_index_size = sum(file_sizes.values())
    
    stats_path = os.path.join(args.output, "index_stats.json")
    with open(stats_path, 'r', encoding='utf-8') as f:
        idx_stats = json.load(f)

    # ─── In báo cáo ra console ─────────────────────────────────────────────────
    print("\n" + "="*80)
    print("📊  INDEXING REPORT")
    print("="*80)
    print(f"  Total wall time    : {format_duration(total_elapsed)}")
    print()
    print("  ── CORPUS ──────────────────────────────────────────────────")
    print(f"  Total documents    : {idx_stats['total_documents']:,}")
    print(f"  Vocabulary size    : {idx_stats['vocabulary_size']:,} unique terms")
    print(f"  Avg document length: {idx_stats['average_doc_length']:.2f} tokens")
    print(f"  Total tokens       : {idx_stats.get('total_tokens', 0):,}")
    print()
    print("  ── SPIMI PHASES ─────────────────────────────────────────────")
    print(f"  Phase 1 (block)    : {format_duration(timing.get('phase1_block', 0))}")
    print(f"  Phase 2 (merge)    : {format_duration(timing.get('phase2_merge', 0))}")
    print(f"  Phase 3 (save)     : {format_duration(timing.get('phase3_save', 0))}")
    print(f"  Total blocks       : {idx_stats['total_blocks']}")
    print(f"  Docs/second        : {idx_stats['total_documents'] / max(total_elapsed, 0.001):,.0f}")
    print()
    print("  ── OUTPUT FILES ─────────────────────────────────────────────")
    for name, size in file_sizes.items():
        print(f"  {name:<26}: {size:7.2f} MB")
    print(f"  {'TOTAL index size':<26}: {total_index_size:7.2f} MB")
    print("="*80)

    # ─── Ghi báo cáo ra file .txt ──────────────────────────────────────────────
    report = {
        "total_wall_time_seconds": round(total_elapsed, 3),
        "total_wall_time_human": format_duration(total_elapsed),
        "corpus": {
            "total_documents": idx_stats["total_documents"],
            "vocabulary_size": idx_stats["vocabulary_size"],
            "average_doc_length": round(idx_stats["average_doc_length"], 4),
            "total_tokens": idx_stats.get("total_tokens", 0),
        },
        "spimi_phases": {
            "phase1_block_seconds": round(timing.get("phase1_block", 0), 3),
            "phase2_merge_seconds": round(timing.get("phase2_merge", 0), 3),
            "phase3_save_seconds": round(timing.get("phase3_save", 0), 3),
            "total_blocks": idx_stats["total_blocks"],
            "docs_per_second": round(idx_stats["total_documents"] / max(total_elapsed, 0.001), 1),
        },
        "output_files_mb": {name: round(size, 3) for name, size in file_sizes.items()},
        "total_index_size_mb": round(total_index_size, 3),
    }

    report_path = os.path.join(args.output, "build_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Full report saved to: {report_path}")
    print()
    print("Next steps:")
    print("  1. Run search app: python search_app.py")
    print("  2. Or test with: python bm25_ranker.py")


if __name__ == "__main__":
    main()
