"""
Shopee Spider - Sử dụng BaseSpider
"""
import asyncio
from typing import List, Dict
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


class ShopeeSpider(BaseSpider):
    """Shopee crawler sử dụng BaseSpider"""
    
    def __init__(self, headless=True, use_proxy=False):
        super().__init__(
            source_name="Shopee",
            base_url="https://shopee.vn",
            headless=headless,
            use_proxy=use_proxy
        )
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """Build Shopee search URL (0-indexed)"""
        return f"https://shopee.vn/search?keyword={keyword}&page={page - 1}"
    
    def get_product_selector(self) -> str:
        """Shopee product selector"""
        return '.shopee-search-item-result__item, div[data-sqe="item"]'
    
    async def scrape_keyword(self, keyword: str, max_pages: int = 1) -> list:
        """Override để xử lý Shopee pagination (0-indexed) với parallel crawling"""
        all_products = []
        
        from playwright.async_api import async_playwright
        from crawler.utils import safe_goto, scroll_to_bottom, random_delay, apply_stealth
        
        async with async_playwright() as p:
            await self.setup_browser(p)
            
            try:
                # Crawl pages song song
                async def scrape_page(page_num: int) -> List[Dict]:
                    """Crawl một page Shopee"""
                    try:
                        url = f"https://shopee.vn/search?keyword={keyword}&page={page_num}"
                        
                        # Tạo page mới cho parallel
                        page = await self.context.new_page()
                        await apply_stealth(page)
                        
                        try:
                            if await safe_goto(page, url, timeout=20000, retries=2):
                                await random_delay(0.3, 0.6)  # Shopee cần chút thời gian
                                await scroll_to_bottom(page, scroll_steps=3, step_delay=0.1)
                                
                                # Thử selector chính trước
                                product_elements = await page.locator('.shopee-search-item-result__item').all()
                                if not product_elements:
                                    product_elements = await page.locator('div[data-sqe="item"]').all()
                                
                                products = []
                                # Parse song song
                                tasks = [self.parse_product(item) for item in product_elements]
                                results = await asyncio.gather(*tasks, return_exceptions=True)
                                
                                for result in results:
                                    if isinstance(result, dict) and result:
                                        products.append(result)
                                
                                return products
                        finally:
                            await page.close()
                    except Exception as e:
                        print(f"⚠️ [{self.source_name}] Error on page {page_num}: {e}")
                        return []
                
                # Crawl tất cả pages song song (batch)
                batch_size = 10
                for batch_start in range(0, max_pages, batch_size):
                    batch_end = min(batch_start + batch_size, max_pages)
                    page_nums = range(batch_start, batch_end)
                    
                    tasks = [scrape_page(page_num) for page_num in page_nums]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for page_num, result in zip(page_nums, batch_results):
                        if isinstance(result, list):
                            all_products.extend(result)
                            print(f"✅ [{self.source_name}] Page {page_num + 1}: {len(result)} items")
                        elif isinstance(result, Exception):
                            print(f"❌ [{self.source_name}] Page {page_num + 1}: {result}")
                            
            finally:
                await self.cleanup()
        
        return all_products
    
    async def parse_product(self, item_locator) -> dict:
        """Parse Shopee product item với format JSON chuẩn"""
        # Name
        name_el = item_locator.locator('div[data-sqe="name"]')
        name = await extract_text(name_el)
        
        if not name:
            return None  # Không có name, có thể là ad hoặc skeleton
        
        name = clean_text(name)
        
        # Price - lấy từ toàn bộ text của item
        text_content = await extract_text(item_locator)
        price = parse_price(text_content)
        
        # Original price
        original_price = await extract_original_price(item_locator)
        
        # Discount percent
        discount_percent = calculate_discount_percent(original_price, price) if original_price > 0 else 0.0
        
        # URL
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
            "platform": "Shopee",
            "product_id": product_id,
            "product_name": name,
            "price": price,
            "original_price": original_price if original_price > 0 else None,
            "discount_percent": discount_percent if discount_percent > 0 else None,
            "product_url": url,
            "image_url": image_url,
            "rating": rating if rating > 0 else None,
            "review_count": review_count if review_count > 0 else None,
            "category": category if category else None
        }


def search(keyword, max_pages=50):
    """Sync wrapper for main.py integration"""
    spider = ShopeeSpider(headless=True)
    return spider.run_sync(keyword, max_pages=max_pages)
