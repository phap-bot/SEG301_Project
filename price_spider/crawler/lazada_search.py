"""
Lazada Spider - Sử dụng BaseSpider
"""
from crawler.spider import BaseSpider
from crawler.parser import (
    extract_text, extract_attribute, extract_image_url, extract_product_url, parse_price, clean_text,
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


class LazadaSpider(BaseSpider):
    """Lazada crawler sử dụng BaseSpider"""
    
    def __init__(self, headless=True, use_proxy=False):
        super().__init__(
            source_name="Lazada",
            base_url="https://www.lazada.vn",
            headless=headless,
            use_proxy=use_proxy
        )
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """Build Lazada search URL"""
        return f"https://www.lazada.vn/catalog/?q={keyword}&page={page}"
    
    def get_product_selector(self) -> str:
        """Lazada product selector"""
        return 'div[data-qa-locator="product-item"], .bm-product-item-list > .bm-product-item'
    
    async def parse_product(self, item_locator) -> dict:
        """Parse Lazada product item với format JSON chuẩn"""
        # Title - thử title attribute trước, sau đó inner_text
        title_el = item_locator.locator('a[title]').first
        title = await extract_attribute(title_el, "title")
        
        if not title:
            title = await extract_text(title_el)
        
        if not title:
            return None
        
        title = clean_text(title)
        
        # Price - parse từ toàn bộ text
        text_content = await extract_text(item_locator)
        price = parse_price(text_content)
        
        # Original price
        original_price = await extract_original_price(item_locator)
        
        # Discount percent
        discount_percent = calculate_discount_percent(original_price, price) if original_price > 0 else 0.0
        
        # URL
        url = await extract_product_url(title_el, self.base_url)
        
        # Product ID từ URL
        product_id = extract_product_id_from_url(url)
        
        # Image - ưu tiên data-src (lazy load)
        image_url = await extract_image_url(item_locator, self.base_url)
        
        # Rating
        rating = await extract_rating(item_locator)
        
        # Review count
        review_count = await extract_review_count(item_locator)
        
        # Category
        category = await extract_category(item_locator)
        
        return {
            "platform": "Lazada",
            "product_id": product_id if product_id else "",
            "product_name": title if title else "",
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
    spider = LazadaSpider(headless=True)
    return spider.run_sync(keyword, max_pages=max_pages)
