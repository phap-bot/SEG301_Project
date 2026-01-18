"""
Spider module: Logic crawl chính
Base class cho các spider với các phương thức chung
"""
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, BrowserContext, Browser

from crawler.utils import (
    create_stealth_context,
    apply_stealth,
    safe_goto,
    scroll_to_bottom,
    random_delay,
    get_random_proxy
)
from crawler.parser import (
    extract_text,
    extract_attribute,
    parse_price,
    extract_image_url,
    extract_product_url,
    clean_text
)

# Import entity resolution
try:
    from crawler.entity_resolution import normalize_text
except ImportError:
    try:
        from entity_resolution import normalize_text
    except ImportError:
        def normalize_text(t): return t.lower()


class BaseSpider:
    """
    Base class cho tất cả spider
    Cung cấp các phương thức chung: browser setup, navigation, extraction
    """
    
    def __init__(self, source_name: str, base_url: str, headless: bool = True, use_proxy: bool = False, headers: Optional[Dict[str, str]] = None):
        """
        Args:
            source_name: Tên nguồn (Tiki, Shopee, etc.)
            base_url: Base URL của website
            headless: Chạy browser ở chế độ headless
            use_proxy: Có sử dụng proxy không
            headers: Headers tùy chỉnh (nếu có)
        """
        self.source_name = source_name
        self.base_url = base_url
        self.headless = headless
        self.use_proxy = use_proxy
        self.headers = headers
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def setup_browser(self, playwright, cookies: Optional[List] = None, headers: Optional[Dict] = None):
        """Setup browser với stealth settings và cookies"""
        proxy = get_random_proxy() if self.use_proxy else None
        
        # Merge headers if needed (method headers override class headers)
        browser_headers = headers if headers else self.headers
        
        result = await create_stealth_context(
            playwright, 
            headless=self.headless,
            proxy=proxy,
            cookies=cookies,
            extra_http_headers=browser_headers
        )
        self.context, self.browser = result
        self.page = await self.context.new_page()
        await apply_stealth(self.page)
    
    async def navigate(self, url: str, timeout: int = 30000) -> bool:
        """Navigate đến URL với retry logic"""
        if not self.page:
            return False
        return await safe_goto(self.page, url, timeout=timeout)
    
    async def wait_for_load(self, min_sec: float = 0.2, max_sec: float = 0.5):
        """Đợi trang load với delay tối thiểu"""
        await random_delay(min_sec, max_sec)
    
    async def scroll_page(self, steps: int = 3):
        """Scroll trang nhanh để trigger lazy loading"""
        if self.page:
            await scroll_to_bottom(self.page, scroll_steps=steps, step_delay=0.1)
    
    async def extract_products(self, product_selector: str) -> List[Dict]:
        """
        Extract products từ page với concurrent parsing
        """
        if not self.page:
            return []
        
        product_elements = await self.page.locator(product_selector).all()
        
        # Parse products song song để tăng tốc
        tasks = [self.parse_product(item) for item in product_elements]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        products = []
        for result in results:
            if isinstance(result, dict) and result:
                products.append(result)
        
        return products
    
    async def parse_product(self, item_locator) -> Optional[Dict]:
        """
        Parse một product item
        Subclass PHẢI override method này
        """
        raise NotImplementedError("Subclass must implement parse_product method")
    
    async def scrape_keyword(self, keyword: str, max_pages: int = 1) -> List[Dict]:
        """
        Main scraping method với parallel page crawling để tối ưu tốc độ
        """
        all_products = []
        
        async with async_playwright() as p:
            await self.setup_browser(p, headers=self.headers)
            
            try:
                # Crawl pages song song để tăng tốc
                async def scrape_page(page_num: int) -> List[Dict]:
                    """Crawl một page"""
                    try:
                        url = self.build_search_url(keyword, page_num)
                        
                        # Tạo page mới cho mỗi request để parallel
                        page = await self.context.new_page()
                        await apply_stealth(page)
                        
                        try:
                            # Tối ưu timeout
                            timeout = 25000 if self.source_name == "Lazada" else 15000
                            
                            if await safe_goto(page, url, timeout=timeout, retries=1):
                                # Delay tối thiểu
                                if self.source_name == "Lazada":
                                    await random_delay(0.3, 0.5)
                                else:
                                    await random_delay(0.05, 0.15)
                                
                                await scroll_to_bottom(page, scroll_steps=3, step_delay=0.1)
                                
                                product_selector = self.get_product_selector()
                                product_elements = await page.locator(product_selector).all()
                                
                                if len(product_elements) == 0:
                                    print(f"⚠️ [{self.source_name}] Page {page_num}: No products found")
                                
                                products = []
                                # Parse products song song
                                tasks = [self.parse_product(item) for item in product_elements]
                                results = await asyncio.gather(*tasks, return_exceptions=True)
                                
                                for result in results:
                                    if isinstance(result, dict) and result:
                                        products.append(result)
                                    elif isinstance(result, Exception):
                                        # Skip lỗi parse từng item
                                        pass
                                
                                return products
                        finally:
                            await page.close()
                    except Exception as e:
                        print(f"⚠️ [{self.source_name}] Error on page {page_num}: {type(e).__name__}: {str(e)[:100]}")
                        import traceback
                        traceback.print_exc()
                        return []
                
                # Crawl tất cả pages song song (batch để tránh quá tải)
                batch_size = 20  # Tăng batch size để crawl nhanh hơn
                for batch_start in range(1, max_pages + 1, batch_size):
                    batch_end = min(batch_start + batch_size, max_pages + 1)
                    page_nums = range(batch_start, batch_end)
                    
                    # Crawl batch song song
                    tasks = [scrape_page(page_num) for page_num in page_nums]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for page_num, result in zip(page_nums, batch_results):
                        if isinstance(result, list):
                            all_products.extend(result)
                            print(f"✅ [{self.source_name}] Page {page_num}: {len(result)} items")
                        elif isinstance(result, Exception):
                            print(f"❌ [{self.source_name}] Page {page_num}: {result}")
                        
            finally:
                await self.cleanup()
        
        return all_products
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """
        Build search URL từ keyword và page number
        Subclass PHẢI override method này
        """
        raise NotImplementedError("Subclass must implement build_search_url method")
    
    def get_product_selector(self) -> str:
        """
        Trả về CSS selector cho product items
        Subclass PHẢI override method này
        """
        raise NotImplementedError("Subclass must implement get_product_selector method")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
    
    def run_sync(self, keyword: str, max_pages: int = 1) -> List[Dict]:
        """
        Sync wrapper để tích hợp với main.py
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.run_until_complete(self.scrape_keyword(keyword, max_pages))
            else:
                return loop.run_until_complete(self.scrape_keyword(keyword, max_pages))
        except RuntimeError:
            return asyncio.run(self.scrape_keyword(keyword, max_pages))

