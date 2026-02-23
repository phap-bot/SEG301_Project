"""
Build Index Script
Wrapper script để build index từ data file
"""

import sys
import argparse
from spimi import SPIMIIndexer


def main():
    parser = argparse.ArgumentParser(
        description='Build search index using SPIMI algorithm'
    )
    parser.add_argument(
        '--input',
        default='data_1tr_clean_tokenized.jsonl',
        help='Input JSONL file (default: data_1tr_clean_tokenized.jsonl)'
    )
    parser.add_argument(
        '--output',
        default='index',
        help='Output directory for index files (default: index/)'
    )
    parser.add_argument(
        '--block-size',
        type=int,
        default=10000,
        help='Documents per block (default: 10000)'
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
    response = input("Proceed with indexing? [Y/n]: ").strip().lower()
    if response and response not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    print()
    
    # Build index
    indexer = SPIMIIndexer(block_size=args.block_size, output_dir=args.output)
    indexer.build_index(args.input)
    
    print("\n🎉 Index building complete!")
    print(f"   Index files saved to: {args.output}/")
    print()
    print("Next steps:")
    print("  1. Run search app: python search_app.py")
    print("  2. Or test with: python bm25_ranker.py")


if __name__ == "__main__":
    main()
