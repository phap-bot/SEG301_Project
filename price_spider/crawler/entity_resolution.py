import unicodedata
import re

def normalize_text(text):
    """
    Normalize text: lower case, strip accents, remove special chars.
    e.g. "Apple iPhone 13 128GB VN/A" -> "apple iphone 13 128gb vn a"
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Normalize unicode characters (e.g. decomposed chars)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_storage(text):
    """Extract storage capacity (ticket feature) e.g. 128GB, 256GB"""
    match = re.search(r'\b(\d+)\s*(gb|tb)\b', text)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return None

def extract_model(text):
    """
    Heuristic to extract core model name? 
    This is hard without a database. For now, we rely on token overlap.
    """
    # Placeholder for more advanced NER
    return text

def are_same_product(name1, name2, threshold=0.7):
    """
    Compare two product names.
    Strategy:
    1. Normalize both.
    2. Check strict containment of critical specs (storage).
    3. Measure token overlap (Jaccard).
    """
    n1 = normalize_text(name1)
    n2 = normalize_text(name2)
    
    # 1. Check storage mismatch (e.g. 128GB vs 256GB should NOT match)
    s1 = extract_storage(n1)
    s2 = extract_storage(n2)
    if s1 and s2 and s1 != s2:
        return False
        
    # 2. Token Jaccard Similarity
    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    
    if not tokens1 or not tokens2:
        return False
        
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    score = len(intersection) / len(union)
    
    # Boost score if one resembles the other strongly (subset)
    # e.g. "Iphone 13" vs "Apple Iphone 13" -> one is subset of other
    if len(tokens1) < len(tokens2):
        if tokens1.issubset(tokens2):
            return True
    else:
        if tokens2.issubset(tokens1):
            return True
            
    return score >= threshold
