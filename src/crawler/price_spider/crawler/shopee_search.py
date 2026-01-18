import asyncio
import random
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page): pass

# Robust import for entity resolution
try:
    from crawler.entity_resolution import normalize_text
except ImportError:
    try:
        from entity_resolution import normalize_text
    except ImportError:
        def normalize_text(t): return t.lower()

class ShopeeScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape_keyword(self, keyword, max_pages=1):
        print(f"🚀 [Shopee] Starting scrape for '{keyword}'...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            
            page = await context.new_page()
            await stealth_async(page)
            
            all_products = []

            for page_num in range(0, max_pages): # Shopee pages are 0-indexed usually or offset based
                # For Shopee UI, we search normally.
                url = f"https://shopee.vn/search?keyword={keyword}&page={page_num}"
                print(f"📄 [Shopee] Navigating to search: {url}")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                    
                    # Shopee needs time to load JS
                    await asyncio.sleep(random.uniform(4, 6))
                    
                    # Scroll down to load all items
                    await self.scroll_to_bottom(page)
                    
                    # Selectors for Shopee Product Items
                    # Usually: [data-sqe="item"] or similar classes
                    item_selector = 'div[data-sqe="item"] button, a[data-sqe="link"]'
                    # Shopee DOM is complex and obfuscated classnames.
                    # Best bet: data-sqe="item" is a stable attribute for items.
                    # Actually valid selector for list items might be: 
                    # .shopee-search-item-result__item
                    
                    product_elements = await page.locator('.shopee-search-item-result__item').all()
                    
                    if not product_elements:
                        # Fallback try generic
                        product_elements = await page.locator('div[data-sqe="item"]').all()
                        
                    print(f"🔍 [Shopee] Found {len(product_elements)} items on page {page_num}")

                    for item in product_elements:
                        try:
                            # Name
                            # data-sqe="name"
                            name_el = item.locator('div[data-sqe="name"]')
                            if await name_el.count() > 0:
                                name = await name_el.first.inner_text()
                            else:
                                continue # No name, probably ad or skeleton

                            # Price
                            # .shopee-price-d2 or similar.
                            # Usually simple text check
                            text_content = await item.inner_text()
                            price = self.parse_price(text_content)
                            
                            # URL
                            # link is on the anchor tag
                            link_el = item.locator('a')
                            link = await link_el.first.get_attribute("href")
                            if link and link.startswith("/"):
                                link = "https://shopee.vn" + link

                            # Image
                            # img inside
                            img_el = item.locator('img')
                            img = await img_el.first.get_attribute("src")
                            
                            all_products.append({
                                "source": "Shopee",
                                "name": name,
                                "price": price,
                                "url": link,
                                "image": img,
                                "normalized_name": normalize_text(name)
                            })
                            
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ [Shopee] Error: {e}")
            
            await browser.close()
            return all_products

    async def scroll_to_bottom(self, page):
        for _ in range(5):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(random.uniform(0.5, 1.5))

    def parse_price(self, text):
        import re
        # Look for patterns like ₫15.000
        match = re.search(r'₫([\d,.]+)', text)
        if match:
            clean = match.group(1).replace('.', '').replace(',', '')
            return float(clean)
        # Or just numbers
        return 0.0

def search(keyword):
    scraper = ShopeeScraper(headless=True)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
        else:
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
    except RuntimeError:
         return asyncio.run(scraper.scrape_keyword(keyword))

if __name__ == "__main__":
    from pprint import pprint
    pprint(search("iphone 13"))
