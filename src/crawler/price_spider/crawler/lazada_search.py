import asyncio
import random
import pandas as pd
import os
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async
except ImportError:
    # If playwright-stealth is not installed, define a dummy function
    async def stealth_async(page):
        pass

try:
    from crawler.entity_resolution import normalize_text
except ImportError:
    from entity_resolution import normalize_text

CSV_FILE = "lazada_products.csv"

class LazadaScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape_keyword(self, keyword, max_pages=50):
        print(f"🚀 Starting scrape for '{keyword}'...")
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            
            page = await context.new_page()
            await stealth_async(page)  # Apply stealth
            
            all_products = []

            for page_num in range(1, max_pages + 1):
                url = f"https://www.lazada.vn/catalog/?q={keyword}&page={page_num}"
                print(f"📄 Navigating to Page {page_num}: {url}")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Anti-bot: Random wait
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    # Scroll to trigger lazy loading
                    await self.scroll_to_bottom(page)
                    
                    # Extract products
                    # Selectors might change, this targets common Lazada product cards
                    product_elements = await page.locator('div[data-qa-locator="product-item"]').all()
                    
                    # If not found, try alternative selector
                    if not product_elements:
                         product_elements = await page.locator('.bm-product-item-list > .bm-product-item').all()

                    print(f"🔍 Found {len(product_elements)} potential items on page {page_num}")

                    for item in product_elements:
                            title_el = item.locator('a[title]')
                            price_el = item.locator('span:not([class*="origin"])') # loosely target price
                            # Better precise selectors based on recent Lazada DOM:
                            # Title usually in `div[class*="title--"] > a` or just `a` with title attr inside the card
                            
                            title = await title_el.first.get_attribute("title")
                            if not title:
                                title = await title_el.first.inner_text()
                                
                            link = await title_el.first.get_attribute("href")
                            if link and link.startswith("//"):
                                link = "https:" + link
                                
                            # Price logic is tricky, grab the first non-strikethrough text in the price area
                            price = self.parse_price(await item.inner_text())

                            # Image extraction with lazy load handling
                            img_el = item.locator('img')
                            # Try data-src first (lazy load), then src
                            img = await img_el.first.get_attribute("data-src")
                            if not img:
                                img = await img_el.first.get_attribute("src")
                            
                            # Clean up image URL to get high-res (remove _200x200q80.jpg suffix)
                            if img:
                                import re
                                # Pattern: removes _200x200....jpg or similar suffix to get original
                                img = re.sub(r'_\d+x\d+q\d+\.[\w]+$', '', img)
                                if img.startswith("//"):
                                    img = "https:" + img

                            all_products.append({
                                "source": "lazada",
                                "keyword": keyword,
                                "title": title,
                                "price_raw": price, 
                                "url": link,
                                "image": img, # High res image
                                "normalized_name": normalize_text(title)
                            })
                            
                            
                except Exception as e:
                    print(f"⚠️ Error on page {page_num}: {e}")
                    
            await browser.close()
            return pd.DataFrame(all_products)

    async def scroll_to_bottom(self, page):
        """Slow scroll to trigger lazy loads"""
        for _ in range(5):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
        # Ensure bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

    def parse_price(self, text):
        # Naive extraction of first ₫... sequence
        import re
        match = re.search(r'[\d,.]+₫', text) or re.search(r'₫[\d,.]+', text)
        if match:
            return match.group(0)
        # Try to find just numbers if it looks like a price block
        lines = text.split('\n')
        for line in lines:
            if '₫' in line:
                return line.strip()
        return text.split('\n')[0] if text else ""

async def main():
    scraper = LazadaScraper(headless=True) # Run headless by default
    
    while True:
        try:
            keyword = input("\n👉 Nhập keyword (Enter để thoát): ").strip()
            if not keyword:
                print("👋 Exiting...")
                break
                
            df = await scraper.scrape_keyword(keyword, max_pages=1)
            
            if not df.empty:
                print(df.head())
                # Save
                df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False, encoding='utf-8-sig')
                print(f"✅ Saved {len(df)} items to {CSV_FILE}")
            else:
                print("❌ No items found.")
                
        except KeyboardInterrupt:
            break

def search(keyword):
    """
    Wrapper for integration with main.py
    Returns: List[dict]
    """
    scraper = LazadaScraper(headless=True)
    try:
        # Check if there is an existing loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If running (e.g. inside another async app), this might fail if not handled carefully.
            # But main.py is sync, so asyncio.run is usually safe.
            # However, Nest_asyncio might be needed if we were in a notebook.
            # Here we assume standard script usage.
             df = loop.run_until_complete(scraper.scrape_keyword(keyword, max_pages=1))
        else:
             df = loop.run_until_complete(scraper.scrape_keyword(keyword, max_pages=1))
    except RuntimeError:
         # No loop?
         df = asyncio.run(scraper.scrape_keyword(keyword, max_pages=1))

    if df.empty:
        return []
    
    # Rename columns to match main.py expectation if needed
    # main.py expects: name, price, url, image, source
    # Our df has: source, keyword, title, price_raw, url, image, normalized_name
    
    df = df.rename(columns={
        "title": "name",
        "price_raw": "price"
    })
    
    return df.to_dict("records")

if __name__ == "__main__":
    asyncio.run(main())
