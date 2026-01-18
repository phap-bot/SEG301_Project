"""
Parser module: Xử lý HTML, tách từ, extract data
- Extract text
- Parse price
- Extract image URL
- Extract product URL
- Clean text
"""
import re
from typing import Optional, List
from playwright.async_api import Locator


async def extract_text(locator: Locator, fallback: str = "") -> str:
    """
    Extract text từ locator, với fallback nếu không tìm thấy
    """
    try:
        if not locator: 
             return fallback
        count = await locator.count()
        if count > 0:
            text = await locator.first.inner_text()
            return text.strip() if text else fallback
    except:
        pass
    return fallback


async def extract_attribute(locator: Locator, attr: str, fallback: str = "") -> str:
    """
    Extract attribute từ locator
    """
    try:
        count = await locator.count()
        if count > 0:
            value = await locator.first.get_attribute(attr)
            return value.strip() if value else fallback
    except:
        pass
    return fallback


def parse_price(text: str, currency_symbol: str = "₫") -> float:
    """
    Parse giá từ text, hỗ trợ nhiều format:
    - ₫15.000
    - 15.000₫
    - 15,000 VND
    - 15000
    """
    if not text:
        return 0.0
    
    # Remove whitespace
    text = text.strip()
    
    # Pattern 1: ₫15.000 hoặc 15.000₫
    pattern1 = rf'{currency_symbol}?[\s]*([\d,.]+)'
    match = re.search(pattern1, text)
    if match:
        price_str = match.group(1)
        # Remove dots and commas (Vietnamese format: 15.000 = 15000)
        price_str = price_str.replace('.', '').replace(',', '')
        try:
            return float(price_str)
        except:
            pass
    
    # Pattern 2: Chỉ số
    numbers = re.findall(r'\d+', text.replace('.', '').replace(',', ''))
    if numbers:
        try:
            return float(''.join(numbers))
        except:
            pass
    
    return 0.0


async def extract_image_url(locator: Locator, base_url: str = "") -> str:
    """
    Extract image URL từ locator
    Ưu tiên: data-src (lazy load) > src > data-original
    """
    img_locator = locator.locator('img').first
    
    # Try data-src first (lazy loading)
    img_url = await extract_attribute(img_locator, "data-src")
    if img_url and not any(x in img_url.lower() for x in ["base64", "lazy", "placeholder"]):
        return normalize_image_url(img_url, base_url)
    
    # Try src
    img_url = await extract_attribute(img_locator, "src")
    if img_url and not any(x in img_url.lower() for x in ["base64", "lazy", "placeholder"]):
        return normalize_image_url(img_url, base_url)
    
    # Try data-original
    img_url = await extract_attribute(img_locator, "data-original")
    if img_url:
        return normalize_image_url(img_url, base_url)
    
    return ""


def normalize_image_url(url: str, base_url: str = "") -> str:
    """
    Normalize image URL:
    - Thêm protocol nếu thiếu
    - Remove cache/resize parameters để lấy ảnh gốc
    """
    if not url:
        return ""
    
    # Fix protocol
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        if base_url:
            from urllib.parse import urljoin
            url = urljoin(base_url, url)
    
    # Remove resize/cache parameters (e.g., _200x200q80.jpg)
    # Pattern: _WIDTHxHEIGHTqQUALITY.ext
    url = re.sub(r'_\d+x\d+q\d+\.[\w]+$', '', url)
    
    return url


async def extract_product_url(locator: Locator, base_url: str = "") -> str:
    """
    Extract product URL từ locator
    Tìm thẻ <a> hoặc lấy href từ chính locator
    """
    # Nếu locator là thẻ <a>
    try:
        tag_name = await locator.evaluate("node => node.tagName")
        if tag_name and tag_name.lower() == 'a':
            url = await extract_attribute(locator, "href")
            if url:
                return normalize_url(url, base_url)
    except:
        pass
    
    # Tìm thẻ <a> bên trong
    link_locator = locator.locator('a').first
    url = await extract_attribute(link_locator, "href")
    if url:
        return normalize_url(url, base_url)
    
    return ""


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize URL:
    - Thêm protocol nếu thiếu
    - Thêm base URL nếu là relative path
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # Fix protocol
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        if base_url:
            from urllib.parse import urljoin
            url = urljoin(base_url, url)
        else:
            # Extract base from common domains
            if "tiki.vn" in base_url or not base_url:
                url = "https://tiki.vn" + url
            elif "shopee.vn" in base_url:
                url = "https://shopee.vn" + url
            elif "lazada.vn" in base_url:
                url = "https://www.lazada.vn" + url
            elif "dienmayxanh.com" in base_url:
                url = "https://www.dienmayxanh.com" + url
            elif "cellphones.com.vn" in base_url:
                url = "https://cellphones.com.vn" + url
    
    return url


def clean_text(text: str) -> str:
    """
    Clean text: remove extra whitespace, normalize
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_keywords(text: str) -> List[str]:
    """
    Tách từ từ text (Vietnamese support)
    """
    if not text:
        return []
    
    # Simple word extraction (có thể dùng thư viện như underthesea cho tiếng Việt)
    words = re.findall(r'\b\w+\b', text.lower())
    return words


async def extract_rating(locator: Locator) -> float:
    """
    Extract rating từ locator
    """
    try:
        # Thử nhiều selector phổ biến cho rating
        rating_selectors = [
            '.rating',
            '[class*="rating"]',
            '[class*="star"]',
            '.review-rating',
            '.product-rating'
        ]
        
        for selector in rating_selectors:
            rating_el = locator.locator(selector).first
            rating_text = await extract_text(rating_el)
            if rating_text:
                # Extract số từ text (e.g., "4.8", "4,8", "4.8/5")
                match = re.search(r'(\d+[.,]\d+)', rating_text)
                if match:
                    rating_str = match.group(1).replace(',', '.')
                    try:
                        rating = float(rating_str)
                        if 0 <= rating <= 5:  # Rating thường từ 0-5
                            return rating
                    except:
                        pass
        
        # Thử extract từ attribute data-rating
        rating_attr = await extract_attribute(locator, "data-rating")
        if rating_attr:
            try:
                rating = float(rating_attr)
                if 0 <= rating <= 5:
                    return rating
            except:
                pass
    except:
        pass
    
    return 0.0


async def extract_review_count(locator: Locator) -> int:
    """
    Extract số lượng review từ locator
    """
    try:
        # Thử nhiều selector phổ biến cho review count
        review_selectors = [
            '[class*="review"]',
            '[class*="rating-count"]',
            '.review-count',
            '.rating-count'
        ]
        
        for selector in review_selectors:
            review_el = locator.locator(selector).first
            review_text = await extract_text(review_el)
            if review_text:
                # Extract số từ text (e.g., "1208 đánh giá", "(1208)", "1.2k")
                # Remove text và chỉ lấy số
                numbers = re.findall(r'\d+', review_text.replace('.', '').replace(',', ''))
                if numbers:
                    try:
                        return int(''.join(numbers))
                    except:
                        pass
    except:
        pass
    
    return 0


async def extract_original_price(locator: Locator) -> float:
    """
    Extract giá gốc (giá trước khi giảm) từ locator
    """
    try:
        # Thử nhiều selector cho giá gốc
        original_price_selectors = [
            '.price-original',
            '.original-price',
            '.price-old',      # Common DMX
            '.old-price',
            '[class*="original"]',
            '.price-before',
            's',  # Thẻ <s> thường dùng cho giá gạch ngang
            '.strike-through'
        ]
        
        for selector in original_price_selectors:
            price_el = locator.locator(selector).first
            price_text = await extract_text(price_el)
            if price_text:
                price = parse_price(price_text)
                if price > 0:
                    return price
    except:
        pass
    
    return 0.0


def calculate_discount_percent(original_price: float, price: float) -> float:
    """
    Tính phần trăm giảm giá (Standardized for ML)
    """
    if not original_price or not price:
        return 0.0
    
    if original_price <= price:
        return 0.0

    discount = (original_price - price) / original_price * 100

    # Remove noise (0.1% ~ 0.9%)
    if discount < 1:
        return 0.0

    return round(discount, 2)


def extract_product_id_from_url(url: str) -> str:
    """
    Extract product ID từ URL
    """
    if not url:
        return ""
    
    # Remove query params
    url_path = url.split('?')[0].split('#')[0]
    
    # Tiki: ...-p{id}.html
    match = re.search(r'-p(\d+)\.html', url_path)
    if match:
        return match.group(1)
    
    # Shopee: /product/{shopid}/{itemid}
    match = re.search(r'/product/\d+/(\d+)', url_path)
    if match:
        return match.group(1)
    
    # Lazada: ...-i{id}-s{id}.html
    match = re.search(r'-i(\d+)-', url_path)
    if match:
        return match.group(1)
    
    # DienMayXanh: .../{slug}-{id}.html hoặc .../{id}.html
    # Prioritize precise match
    match = re.search(r'[-/](\d{3,})\.html', url_path)
    if match:
        return match.group(1)
    
    # DienMayXanh: .../{slug}-{id} (ID usually > 3 digits to avoid confusing with dates/small nums)
    match = re.search(r'[-/](\d{4,})$', url_path.rstrip('/'))
    if match:
        return match.group(1)
    
    # CellphoneS: tìm số trong path
    # match = re.search(r'/(\d+)', url) # Too risky if matches small numbers
    
    # Generic: lấy số cuối cùng trong PATH (not full url)
    numbers = re.findall(r'\d+', url_path)
    if numbers:
        # Filter for likely ID length (e.g. >= 3 digits) to avoid "v2", "2024" etc if possible
        # But for reliability, just taking the last one is often safe IF query params are gone
        # However, checking if it looks like an ID (longer is better?)
        candidate = numbers[-1]
        if len(candidate) >= 3:
             return candidate
    
    return ""


async def extract_category(locator: Locator) -> str:
    """
    Extract category từ locator
    """
    try:
        category_selectors = [
            '[class*="category"]',
            '.category',
            '.breadcrumb',
            '[class*="breadcrumb"]'
        ]
        
        for selector in category_selectors:
            category_el = locator.locator(selector).first
            category_text = await extract_text(category_el)
            if category_text:
                # Lấy category cuối cùng trong breadcrumb hoặc category chính
                categories = [c.strip() for c in category_text.split('>') if c.strip()]
                if categories:
                    return categories[-1]
    except:
        pass
    
    return ""

