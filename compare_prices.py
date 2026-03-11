import sys, os, time

sys.path.append(os.path.join(os.getcwd(), 'src', 'ranking'))
sys.path.append(os.path.join(os.getcwd(), 'src', 'indexer'))

from bm25 import BM25Ranker

def fmt_price(doc):
    p = doc.get('price', 0) or 0
    o = doc.get('original_price', 0) or 0
    try: p = float(p)
    except: p = 0
    try: o = float(o)
    except: o = 0
    if p > 0:
        s = f"{p:,.0f} VND"
        if o > p: s += f" (original {o:,.0f} VND)"
        return s
    if o > 0: return f"{o:,.0f} VND"
    return "Contact for price"

def show_results(results, ranker):
    SEP = "-" * 65
    for i, (doc_id, score, _) in enumerate(results, 1):
        doc = ranker.get_doc_info(doc_id)
        name     = doc.get('product_name', 'N/A')
        platform = doc.get('platform', '?').upper()
        price    = fmt_price(doc)
        rating   = doc.get('rating', 0) or 0
        reviews  = int(doc.get('review_count', 0) or 0)
        url      = doc.get('product_url', '#')

        print(SEP)
        print(f"[{i}] [Score: {score:.2f}] {name}")
        print(f"    Platform: {platform}  |  Price: {price}  |  ⭐ {rating} ({reviews:,} reviews)")
        print(f"    🔗 {url}")
    print(SEP)

def main():
    print("Initializing search engine...")
    ranker = BM25Ranker(index_dir="index")

    while True:
        print("\n" + "=" * 60)
        query = input("Search (q = quit): ").strip()
        if query.lower() == 'q':
            print("Goodbye!")
            break
        if not query:
            continue

        start = time.time()
        results = ranker.search(query, top_k=10)
        elapsed = time.time() - start

        print(f"\nResults for '{query}' [{elapsed:.2f}s]: {len(results)} products\n")

        if not results:
            print("No matching results found.")
        else:
            show_results(results, ranker)

if __name__ == "__main__":
    main()
