"""
Vietnamese Tokenizer Utility
Sử dụng underthesea để thực hiện Word Segmentation chuyên sâu
"""

try:
    from underthesea import word_tokenize
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False

def tokenize(text: str) -> list:
    """
    Tách từ Tiếng Việt:
    - Nếu có underthesea: "máy lọc nước" -> ["máy_lọc_nước"]
    - Nếu không: split theo khoảng trắng cơ bản
    """
    if not text:
        return []
        
    text = text.lower().strip()
    
    if HAS_UNDERTHESEA:
        # format="fixed" sẽ nối các từ ghép bằng dấu gạch dưới _
        return word_tokenize(text, format="fixed")
    else:
        return text.split()

if __name__ == "__main__":
    # Test nhanh
    test_text = "máy lọc nước hydrogen toshiba"
    print(f"Bản gốc: {test_text}")
    print(f"Tokenized: {tokenize(test_text)}")
