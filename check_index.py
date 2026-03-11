import pickle
import os

def check_terms():
    index_file = "index/inverted_index.pkl"
    if not os.path.exists(index_file):
        print("Index not found")
        return
        
    with open(index_file, 'rb') as f:
        index = pickle.load(f)
        
    candidates = ["tu", "lanh", "tu_lanh", "dien", "thoai", "dien_thoai", "xiaomi", "tu_lanh_samsung"]
    for c in candidates:
        status = f"EXISTS ({len(index[c])} docs)" if c in index else "MISSING"
        print(f"Term: {c:<20} | Status: {status}")

if __name__ == "__main__":
    check_terms()
