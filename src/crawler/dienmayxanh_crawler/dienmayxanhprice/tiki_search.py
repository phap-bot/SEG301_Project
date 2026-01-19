"""
Tiki Spider - Sử dụng BaseSpider
"""
from crawler.spider import BaseSpider
from crawler.parser import (
    extract_text, extract_image_url, extract_product_url, parse_price, clean_text,
    extract_rating, extract_review_count, extract_original_price, calculate_discount_percent,
    extract_product_id_from_url, extract_category
)

try:
    from crawler.entity_resolution import normalize_text
except ImportError:
    try:
        from entity_resolution import normalize_text
    except ImportError:
        def normalize_text(t): return t.lower()


class TikiSpider(BaseSpider):
    """Tiki crawler sử dụng BaseSpider"""
    
    def __init__(self, headless=True, use_proxy=False):
        super().__init__(
            source_name="Tiki",
            base_url="https://tiki.vn",
            headless=headless,
            use_proxy=use_proxy
        )
    
    def build_search_url(self, keyword: str, page: int = 50) -> str:
        """Build Tiki search URL"""
        return f"https://tiki.vn/search?q={keyword}&page={page}"
    
    def get_product_selector(self) -> str:
        """Tiki product selector"""
        return 'a.product-item'
    
    async def parse_product(self, item_locator) -> dict:
        """Parse Tiki product item với format JSON chuẩn"""
        # Name - thử nhiều selector
        name = ""
        name_selectors = [
            '.style__Name-sc-139nb47-3',
            '.product-name',
            'h3',
            'div[class*="name"]'
        ]
        
        for selector in name_selectors:
            name_el = item_locator.locator(selector)
            name = await extract_text(name_el)
            if name:
                break
        
        if not name:
            # Fallback: lấy text từ item và lấy dòng đầu
            full_text = await extract_text(item_locator)
            name = full_text.split('\n')[0] if full_text else ""
        
        if not name:
            return None
        
        name = clean_text(name)
        
        # Price (giá hiện tại)
        price_el = item_locator.locator('.price-discount__price, .price-discount, .product-price')
        price_text = await extract_text(price_el, "0")
        price = parse_price(price_text)
        
        # Original price (giá gốc)
        original_price = await extract_original_price(item_locator)
        
        # Discount percent
        discount_percent = calculate_discount_percent(original_price, price) if original_price > 0 else 0.0
        
        # URL
        url = await extract_product_url(item_locator, self.base_url)
        
        # Product ID từ URL
        product_id = extract_product_id_from_url(url)
        
        # Image
        image_url = await extract_image_url(item_locator, self.base_url)
        
        # Rating
        rating = await extract_rating(item_locator)
        
        # Review count
        review_count = await extract_review_count(item_locator)
        
        # Category
        category = await extract_category(item_locator)
        
        return {
            "platform": "Tiki",
            "product_id": product_id if product_id else "",
            "product_name": name if name else "",
            "price": price if price > 0 else 0.0,
            "original_price": original_price if original_price > 0 else 0.0,
            "discount_percent": discount_percent if discount_percent > 0 else 0.0,
            "product_url": url if url else "",
            "image_url": image_url if image_url else "",
            "rating": rating if rating > 0 else 0.0,
            "review_count": review_count if review_count > 0 else 0,
            "category": category if category else ""
        }


def search(keyword, max_pages=50):
    """Sync wrapper for main.py integration"""
    spider = TikiSpider(headless=True)
    return spider.run_sync(keyword, max_pages=max_pages)


