import re
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, Optional, List

# ================= PARSE HELPER =================

def parse_price(text):
    """
    Parse price string to float.
    Example: "24.990.000₫" -> 24990000.0
    """
    if not text:
        return 0.0
    try:
        # Remove non-digit characters except dot/comma if needed
        # Commonly Vietnam format: 24.990.000
        clean = re.sub(r"[^\d]", "", text)
        return float(clean)
    except:
        return 0.0

def parse_html_item(soup_el, base_url) -> Optional[Dict]:
    """Parse single product from BS4 soup element"""
    try:
        # Name
        name_el = soup_el.select_one("h3, .product-name, .name, a[title]")
        if not name_el: return None
        name = name_el.get_text(strip=True)
        
        # URL
        url_el = soup_el.select_one("a[href]")
        url = ""
        if url_el:
            href = url_el.get("href")
            if href:
                if href.startswith("/"): url = "https://www.dienmayxanh.com" + href
                else: url = href
        
        # Clean URL (strip params)
        if url:
             url = url.split("?")[0]
        
        # Image
        image_url = ""
        img_el = soup_el.select_one("img")
        if img_el:
            src = img_el.get("data-src") or img_el.get("src")
            if src: image_url = src

        # ID
        pid = soup_el.get("data-product-id") or soup_el.get("data-id") or soup_el.get("id") or ""
        
        # Fallback 1: URL Clean
        if not pid and url:
             clean_url = url.split('?')[0]
             parts = clean_url.strip('/').split('/')[-1]
             m = re.search(r'-(\d+)$', parts)
             if m: pid = m.group(1)

        # Fallback 2: Image URL
        if not pid and image_url:
            m = re.search(r'/Images/\d+/(\d+)/', image_url)
            if m: pid = m.group(1)

        # Fallback 3: Hashing
        if not pid and url:
             import hashlib
             pid = hashlib.md5(url.encode()).hexdigest()[:12]

        # Price
        price = 0.0
        p_el = soup_el.select_one(".price, .price-current, .price-sale")
        if p_el:
            price = parse_price(p_el.get_text(strip=True))
            
        # Original
        original = 0.0
        o_el = soup_el.select_one(".price-old, .price-regular")
        if o_el:
            original = parse_price(o_el.get_text(strip=True))
        if original == 0: original = price
        
        # Discount
        discount_p = 0.0
        d_el = soup_el.select_one(".percent, .discount")
        if d_el:
            m = re.search(r"(\d+)", d_el.get_text())
            if m: discount_p = float(m.group(1))
        
        if discount_p == 0 and original > price:
             discount_p = round(((original - price) / original) * 100, 1)

        # Rating & Review
        rating = 0.0
        review = 0
        
        # 1. Extract Review Count
        review_selectors = [
            ".item-rating-total", ".item-rating", ".total-review",
            ".review-count", ".rating-count", "span[class*='rating']", "span[class*='review']"
        ]
        for selector in review_selectors:
            r_el = soup_el.select_one(selector)
            if r_el:
                txt = r_el.get_text(strip=True)
                m_r = re.search(r"(\d+)", txt)
                if m_r:
                    review = int(m_r.group(1))
                    break
        
        # 2. Calculate Rating from Stars
        star_selectors = [
            ".icon-star", ".icon-star-dark", ".icont-star", ".star", ".fa-star", "i[class*='star']"
        ]
        
        for selector in star_selectors:
            stars = soup_el.select(selector)
            if stars:
                full_stars = len([s for s in stars if "dark" in s.get("class", [])])
                rating = float(full_stars)
                
                # Check for half-stars
                half_stars = soup_el.select(".icon-star-half, .star-half, .fa-star-half-o")
                if half_stars:
                    rating += 0.5
                break
        
        # 3. If rating not found, try to extract from text
        if rating == 0:
            rating_text = ""
            rating_selectors = [".rating", ".product-rating", ".rate"]
            for selector in rating_selectors:
                r_el = soup_el.select_one(selector)
                if r_el:
                    rating_text = r_el.get_text(strip=True)
                    break
            
            if rating_text:
                m_rating = re.search(r"(\d+(?:\.\d+)?)", rating_text)
                if m_rating:
                    rating = float(m_rating.group(1))
        
        # 4. Fallback: If we have reviews but no rating detected, assume 5 stars
        if review > 0 and rating == 0:
            rating = 5.0

        return {
            "platform": "DienMayXanh",
            "product_id": str(pid),
            "product_name": name,
            "price": price,
            "original_price": original,
            "discount_amount": float(original - price),
            "discount_percent": discount_p,
            "product_url": url,
            "image_url": image_url,
            "rating": rating,
            "review_count": review,
            "category": "",
            "location": "Toàn quốc",
            "scraped_at": datetime.now().isoformat()
        }
    except Exception: 
        return None

def parse_items_from_html(html, category_url) -> List[Dict]:
    """Parse list of items from HTML string using BS4"""
    # lxml is faster if available
    try:
        soup = BeautifulSoup(html, "lxml")
    except:
        soup = BeautifulSoup(html, "html.parser")
        
    items = []
    els = soup.select("li.item, div.item, .product-item")
    for el in els:
        i = parse_html_item(el, category_url)
        if i: items.append(i)
    return items
