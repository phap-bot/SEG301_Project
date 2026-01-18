"""
CellphoneS Spider - Sử dụng BaseSpider
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


class CellphoneSSpider(BaseSpider):
    """CellphoneS crawler sử dụng BaseSpider"""
    
    def __init__(self, headless=True, use_proxy=False):
        super().__init__(
            source_name="CellphoneS",
            base_url="https://cellphones.com.vn",
            headless=headless,
            use_proxy=use_proxy
        )
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """Build CellphoneS search URL"""
        return f"https://cellphones.com.vn/catalogsearch/result/?q={keyword}"
    
    def get_product_selector(self) -> str:
        """CellphoneS product selector"""
        return '.product-item, .product-info-container'
    
    async def parse_product(self, item_locator) -> dict:
        """Parse CellphoneS product item với format JSON chuẩn"""
        # Name - thử nhiều selector
        name_el = item_locator.locator('h3')
        if await name_el.count() == 0:
            name_el = item_locator.locator('.product__name h3')
        
        name = await extract_text(name_el)
        
        if not name:
            return None
        
        name = clean_text(name)
        
        # Price
        price_el = item_locator.locator('.product__price--show, .price-discount__price')
        price_text = await extract_text(price_el, "0")
        price = parse_price(price_text)
        
        # Original price
        original_price = await extract_original_price(item_locator)
        
        # Discount percent
        discount_percent = calculate_discount_percent(original_price, price) if original_price > 0 else 0.0
        
        # URL - kiểm tra nếu item là thẻ <a>
        try:
            tag_name = await item_locator.evaluate("node => node.tagName")
            if tag_name and tag_name.lower() == 'a':
                url = await extract_product_url(item_locator, self.base_url)
            else:
                link_el = item_locator.locator('a').first
                url = await extract_product_url(link_el, self.base_url)
        except:
            link_el = item_locator.locator('a').first
            url = await extract_product_url(link_el, self.base_url)
        
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
            "platform": "CellphoneS",
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
    spider = CellphoneSSpider(headless=True)
    return spider.run_sync(keyword, max_pages=max_pages)
