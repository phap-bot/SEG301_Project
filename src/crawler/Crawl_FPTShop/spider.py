import asyncio
import aiohttp
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, quote_plus

# Import local modules
from utils import (
    CATEGORIES, OUTPUT_FILE, 
    load_existing_keys, save_item
)
from parser import parse_api_item, extract_rating_html

class FPTShopSpider:
    """FPTShop crawler using Public API"""
    
    def __init__(self, headless=True):
        self.api_url = "https://papi.fptshop.com.vn/gw/v1/public/fulltext-search-service/search"
        self.base_url = "https://fptshop.com.vn"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Origin": "https://fptshop.com.vn",
            "Referer": "https://fptshop.com.vn/"
        }
    
    async def scrape_category(self, category_url: str, max_pages: int = 50) -> List[Dict]:
        """Crawl by calling API with keyword extracted from URL."""
        products = []
        
        # 1. Extract keyword
        parsed = urlparse(category_url)
        params = parse_qs(parsed.query)
        keyword = params.get('key', [''])[0]
        
        if not keyword:
            # Maybe path based?
            keyword = parsed.path.strip('/').split('/')[-1]
            if not keyword:
                print("⚠️ Could not extract keyword from URL")
                return []
        
        print(f"🔑 Keyword extracted: {keyword}")
        
        # 2. Pagination Loop
        batch_size = 24
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            total_fetched = 0
            for page_idx in range(max_pages):
                skip = page_idx * batch_size
                
                print(f"📡 Fetching API (skip={skip})...", end='\r')
                
                # Use Global Search Payload
                data = await self._fetch_page(session, keyword, skip, batch_size)
                if not data: break
                
                items = data.get("items", [])
                total_count = data.get("totalCount", 0)
                
                if not items:
                    break
                    
                # Process Items
                batch_products = []
                for item in items:
                    parsed_item = parse_api_item(item, self.base_url)
                    if parsed_item:
                        batch_products.append(parsed_item)
                
                # ENRICH WITH RATING (Fetch HTML)
                if batch_products:
                    await self.enrich_with_ratings(batch_products)
                    products.extend(batch_products)
                
                total_fetched += len(items)
                print(f"📦 Loaded {len(products)} products...", end='\r')
                
                # Check endpoint
                if skip + len(items) >= total_count:
                    break
                    
                # Rate limit safety
                await asyncio.sleep(0.5)
                
        return products

    async def _fetch_page(self, session, keyword, skip, limit):
        payload = {
            "skipCount": skip,
            "maxResultCount": limit,
            "keyword": keyword,
            "pipeline": "Normal",
            "sortMethod": "noi-bat",
            "isFilterAllCategory": True, 
            "categorySlug": None,        
            "location": None
        }
        try:
            async with session.post(self.api_url, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
        except: pass
        return {}

    async def enrich_with_ratings(self, items: List[Dict]):
        """Fetch detail pages concurrently to get ratings"""
        sem = asyncio.Semaphore(10) # 10 concurrent requests
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = []
            for item in items:
                tasks.append(self.fetch_rating(session, item, sem))
            await asyncio.gather(*tasks)

    async def fetch_rating(self, session, item, sem):
        url = item["product_url"]
        try:
            async with sem:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        rating, count = extract_rating_html(html)
                        item["rating"] = rating
                        item["review_count"] = count
        except:
            pass # Keep default 0

def main():
    print("===== FPTSHOP CRAWLER (REFACTORED) =====")
    
    print("\n📋 Danh mục có sẵn:")
    for cat_id, cat_info in sorted(CATEGORIES.items(), key=lambda x: int(x[0])):
        print(f"  {cat_id}. {cat_info['name']}")
        
    print("\n👉 Nhập ID (1,2...), từ khóa, URL hoặc 'ALL': ")
    user_input = input("   Nhập: ").strip()
    
    if not user_input:
        print("❌ Vui lòng nhập thông tin.")
        return

    selected_cats = []
    
    # Pre-process inputs
    raw_inputs = []
    if user_input.upper() == "ALL":
         raw_inputs = list(CATEGORIES.keys())
    else:
         raw_inputs = [x.strip() for x in user_input.split(',') if x.strip()]

    for inp in raw_inputs:
        cat_data = {}
        if inp in CATEGORIES:
            cat_data = CATEGORIES[inp].copy()
        elif inp.startswith("http"):
             cat_data = {"name": "Custom URL", "url": inp}
        else:
             # Search param
             cat_data = {
                 "name": f"Search: {inp}",
                 "url": f"https://fptshop.com.vn/tim-kiem/tat-ca?key={quote_plus(inp)}"
             }
        selected_cats.append(cat_data)

    # Load keys
    existing_keys = load_existing_keys(OUTPUT_FILE)
    total_new = 0
    
    for i, cat in enumerate(selected_cats):
        print(f"\n[{i+1}/{len(selected_cats)}] 🚀 Starting Crawl: {cat['name']}")
        
        spider = FPTShopSpider(headless=True)
        try:
            # Sync wrapper around async call
            items = asyncio.run(spider.scrape_category(cat['url'], max_pages=30))
            
            new_count = 0
            for item in items:
                # Add category info if not present or generic
                if not item.get("category"):
                    item["category"] = cat["name"]
                    
                if save_item(item, existing_keys):
                    new_count += 1
            
            total_new += new_count
            print(f"✅ Finished {cat['name']}. Saved {new_count} NEW items.")
            
        except Exception as e:
            print(f"⚠️ Error crawling {cat['name']}: {e}")
            import traceback
            traceback.print_exc()
        
    print(f"\n🏁 Complete. Total New: {total_new}")
    
if __name__ == "__main__":
    main()
