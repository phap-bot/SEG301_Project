import re
import unicodedata

# Common Vietnamese product aliases
PRODUCT_ALIASES = {
    'may loc khong khi': ['air purifier', 'may loc', 'loc khong khi'],
    'dieu hoa': ['air conditioner', 'ac', 'may lanh'],
    'tu lanh': ['refrigerator', 'fridge', 'tu dung'],
    'may giat': ['washing machine', 'may giat', 'giat'],
    'lo vi song': ['microwave', 'lo vi bo', 'lo song'],
    'iphone': ['apple iphone', 'iphone'],
    'samsung': ['samsung galaxy', 'samsung'],
}

def normalize(text):
    """
    Normalize text for better matching:
    1. Convert to lowercase
    2. Handle Vietnamese diacritics via Unicode normalization
    3. Remove special characters, keep alphanumeric and spaces
    4. Collapse multiple spaces
    """
    if not text:
        return ""
    
    text = text.lower()
    
    # Normalize Vietnamese diacritics: decompose combined chars
    # 'á' → 'a', 'ơ' → 'o', etc.
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def expand_keyword(keyword):
    """
    Expand search keyword with aliases to improve search coverage.
    E.g. "Máy lọc không khí" → includes "air purifier", "máy lọc", etc.
    """
    norm_keyword = normalize(keyword)
    
    expanded = [keyword, norm_keyword]
    
    # Check if keyword matches any alias
    for alias, variations in PRODUCT_ALIASES.items():
        if norm_keyword == alias or alias in norm_keyword:
            # Add all variations of this product
            expanded.extend(variations)
            break
    
    # Remove duplicates, preserving order
    seen = set()
    result = []
    for item in expanded:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    
    return result
