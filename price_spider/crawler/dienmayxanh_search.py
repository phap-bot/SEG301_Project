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

class DienMayXanhScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape_keyword(self, keyword, max_pages=50):
        print(f" [DienMayXanh] Starting scrape for '{keyword}'...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            
            page = await context.new_page()
            await stealth_async(page)
            
            # DMX search URL usually: https://www.dienmayxanh.com/tim-kiem?key=iphone
            url = f"https://www.dienmayxanh.com/tim-kiem?key={keyword}"
            print(f"📄 [DMX] Navigating: {url}")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                
                # Selector: .listproduct .item or .item
                # DMX has a list `ul.listproduct` containing `li.item`
                
                product_elements = await page.locator('ul.listproduct li.item').all()
                
                print(f"🔍 [DMX] Found {len(product_elements)} items")
                results = []
                
                for item in product_elements:
                    try:
                        # Name
                        # h3
                        name_el = item.locator('h3')
                        if await name_el.count() > 0:
                            name = await name_el.first.inner_text()
                        else:
                            continue

                        # Price
                        price_el = item.locator('.price, .price-current')
                        if await price_el.count() > 0:
                            price_text = await price_el.first.inner_text()
                            import re
                            clean = re.sub(r'[^\d]', '', price_text)
                            price = float(clean) if clean else 0.0
                        else:
                            price = 0.0
                        
                        # URL
                        link_el = item.locator('a')
                        link = await link_el.first.get_attribute("href")
                        if link and link.startswith("/"):
                            link = "https://www.dienmayxanh.com" + link

                        # Image
                        img_el = item.locator('img')
                        img = await img_el.first.get_attribute("src")
                        if not img or "base64" in img or "lazy" in img:
                             img = await img_el.first.get_attribute("data-src")
                        
                        results.append({
                            "source": "DienMayXanh",
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
                print(f"⚠️ [DMX] Error: {e}")
                await browser.close()
                return []

def search(keyword):
    scraper = DienMayXanhScraper(headless=True)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
        else:
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
    except RuntimeError:
         return asyncio.run(scraper.scrape_keyword(keyword))
