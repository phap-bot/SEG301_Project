import json
from datetime import datetime
from typing import Dict, Tuple

def extract_rating_html(html: str) -> Tuple[float, int]:
    """Extract rating and review count from HTML content"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        
        # 1. Try JSON-LD
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for d in data:
                        if "aggregateRating" in d:
                            agg = d["aggregateRating"]
                            return float(agg.get("ratingValue", 0)), int(agg.get("reviewCount", 0))
                elif isinstance(data, dict):
                        if "aggregateRating" in data:
                            agg = data["aggregateRating"]
                            return float(agg.get("ratingValue", 0)), int(agg.get("reviewCount", 0))
            except: pass
            
        # 2. Try Selector (Fallback)
        # Return 0 if not found
        return 0.0, 0
    except:
        return 0.0, 0

def parse_api_item(item: Dict, base_url: str) -> Dict:
    """Map API item to standard format"""
    # Basic fields
    pid = item.get("sku") or item.get("code") or "unknown"
    name = item.get("name") or item.get("displayName") or ""
    
    # Price
    price = float(item.get("currentPrice", 0))
    original_price = float(item.get("originalPrice", 0))
    if original_price == 0: original_price = price
    
    # Discount
    discount_amount = original_price - price
    discount_percent = item.get("discountPercentage", 0.0)
    
    if discount_amount > 0 and discount_percent == 0 and original_price > 0:
        discount_percent = round((discount_amount / original_price) * 100, 1)

    # URL
    slug = item.get("slug", "")
    if slug.startswith("http"):
            url = slug
    else:
            url = f"{base_url}/{slug}".replace("//", "/") if slug else ""
            # fix https:/ -> https://
            url = url.replace("https:/fpt", "https://fpt")
            
    # Image
    image_url = ""
    img_obj = item.get("image")
    if isinstance(img_obj, dict):
        image_url = img_obj.get("src", "")
    elif isinstance(img_obj, str):
        image_url = img_obj
        
    # Default Rating (Enriched later)
    rating = 0.0
    review_count = 0
    
    return {
        "platform": "FPTShop",
        "product_id": str(pid),
        "product_name": name,
        "price": price,
        "original_price": original_price,
        "discount_amount": float(discount_amount),
        "discount_percent": float(discount_percent),
        "product_url": url,
        "image_url": image_url,
        "rating": rating,
        "review_count": review_count,
        "category": "", # Caller fills
        "location": "Toàn quốc",
        "scraped_at": datetime.now().isoformat()
    }
