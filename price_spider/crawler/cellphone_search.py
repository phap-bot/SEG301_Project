import asyncio
import random
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page): pass

try:
    from crawler.entity_resolution import normalize_text
except ImportError:
    try:
        from entity_resolution import normalize_text
    except ImportError:
        def normalize_text(t): return t.lower()

class CellphoneSScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape_keyword(self, keyword, max_pages=50):
        print(f" [CellphoneS] Starting scrape for '{keyword}'...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            
            page = await context.new_page()
            await stealth_async(page)
            
            url = f"https://cellphones.com.vn/catalogsearch/result/?q={keyword}"
            print(f"📄 [CellphoneS] Navigating: {url}")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                
                # CellphoneS uses 'product-item' class or grids.
                # Grid selector: .product-list-filter .product-item
                # But DOM structure changes often.
                # Let's target grid items general class often seen: .product-info-container or .product-item
                
                product_elements = await page.locator('.product-item, .product-info-container').all()
                
                print(f"🔍 [CellphoneS] Found {len(product_elements)} items")
                results = []
                
                for item in product_elements:
                    try:
                        # Extract Name
                        # usually h3
                        name_el = item.locator('h3')
                        if await name_el.count() == 0:
                            name_el = item.locator('.product__name h3')
                            
                        if await name_el.count() > 0:
                            name = await name_el.first.inner_text()
                        else:
                            continue
                            
                        # Price
                        price_el = item.locator('.product__price--show, .price-discount__price')
                        if await price_el.count() > 0:
                            price_text = await price_el.first.inner_text()
                            import re
                            clean = re.sub(r'[^\d]', '', price_text)
                            price = float(clean) if clean else 0.0
                        else:
                            price = 0.0

                        # URL
                        link_el = item.locator('a') 
                        # If the item itself is an A tag or has common parent
                        if await item.evaluate("node => node.tagName") == 'A':
                             link_el = item
                        else:
                             # try finding a inside
                             link_el = item.locator('a').first
                        
                        link = await link_el.get_attribute("href")
                        if link and link.startswith("/"):
                            link = "https://cellphones.com.vn" + link

                        # Image
                        img_el = item.locator('img')
                        img = await img_el.first.get_attribute("src")
                        if not img or "base64" in img:
                             img = await img_el.first.get_attribute("data-src")

                        results.append({
                            "source": "CellphoneS",
                            "name": name,
                            "price": price,
                            "url": link,
                            "image": img,
                            "normalized_name": normalize_text(name)
                        })

                    except Exception as e:
                        continue
                
                await browser.close()
                return results

            except Exception as e:
                print(f"⚠️ [CellphoneS] Error: {e}")
                await browser.close()
                return []

def search(keyword):
    scraper = CellphoneSScraper(headless=True)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
        else:
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
    except RuntimeError:
         return asyncio.run(scraper.scrape_keyword(keyword))
