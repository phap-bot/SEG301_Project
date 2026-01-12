import asyncio
import random
import os
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page):
        pass

# Ensure entity resolution is imported correctly regardless of run context
try:
    from crawler.entity_resolution import normalize_text
except ImportError:
    try:
        from entity_resolution import normalize_text
    except ImportError:
        def normalize_text(t): return t.lower()

class TikiScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape_keyword(self, keyword, max_pages=50):
        print(f"🚀 [Tiki] Starting scrape for '{keyword}'...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            
            page = await context.new_page()
            await stealth_async(page)
            
            all_products = []

            for page_num in range(1, max_pages + 1):
                url = f"https://tiki.vn/search?q={keyword}&page={page_num}"
                print(f"📄 [Tiki] Navigating to Page {page_num}: {url}")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Scroll to trigger lazy loading
                    await self.scroll_to_bottom(page)
                    
                    # Tiki product cards usually have class `product-item`
                    # We look for 'a.product-item'
                    product_elements = await page.locator('a.product-item').all()
                    
                    print(f"🔍 [Tiki] Found {len(product_elements)} items on page {page_num}")

                    for item in product_elements:
                        try:
                            # Extract basic info
                            # Tiki text is often in:
                            # name: .name >span or h3 or div
                            # price: .price-discount__price
                            # img: .thumbnail img or just img
                            
                            # Note: Tiki DOM changes, we try to be robust
                            
                            # Name
                            name_el = item.locator('.style__Name-sc-139nb47-3, .product-name, h3, div[class*="name"]') 
                            if await name_el.count() > 0:
                                name = await name_el.first.inner_text()
                            else:
                                # Fallback: get text from the link itself but might contain price
                                name = await item.inner_text()
                                name = name.split('\n')[0]

                            # Price
                            price_el = item.locator('.price-discount__price, .price-discount, .product-price')
                            if await price_el.count() > 0:
                                price_text = await price_el.first.inner_text()
                            else:
                                price_text = "0"
                            
                            # Clean price
                            import re
                            price_clean = re.sub(r'[^\d]', '', price_text)
                            price = float(price_clean) if price_clean else 0.0

                            # URL
                            link = await item.get_attribute("href")
                            if link and link.startswith("//"):
                                link = "https:" + link
                            if link and link.startswith("/"):
                                link = "https://tiki.vn" + link

                            # Image
                            img_el = item.locator('img')
                            # Try webp / srcset first if available, or src
                            img = await img_el.first.get_attribute("src")
                            
                            # High res logic if needed (Tiki often uses thumbnails)
                            # Tiki images: https://salt.tikicdn.com/cache/280x280/ts/product/...
                            if img and "cache" in img:
                                # Try to remove cache part to get original? 
                                # Actually Tiki CDN structure is complex, usually 280x280 is decent for listing
                                pass
                                
                            all_products.append({
                                "source": "Tiki",
                                "name": name,
                                "price": price,
                                "url": link,
                                "image": img,
                                "normalized_name": normalize_text(name)
                            })
                            
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ [Tiki] Error on page {page_num}: {e}")
            
            await browser.close()
            return all_products

    async def scroll_to_bottom(self, page):
        for _ in range(4):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(1)
        # Check if "Load More" exists? Tiki usually pagination.


def search(keyword):
    """
    Sync wrapper for main.py integration
    """
    scraper = TikiScraper(headless=True)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
        else:
             return loop.run_until_complete(scraper.scrape_keyword(keyword))
    except RuntimeError:
         return asyncio.run(scraper.scrape_keyword(keyword))

if __name__ == "__main__":
    asyncio.run(main())


