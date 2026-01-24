import asyncio
import re
import os
import aiohttp
import time
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

# Import local modules
from utils import (
    DMX_HEADERS, DMX_COOKIES, 
    generate_dedup_key, load_existing_keys, save_item, 
    navigate_with_retry
)
from parser import parse_items_from_html

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: Using absolute path from previous file or relative? 
# User used: C:\Users\letan\Downloads\SEG301\price_spider\data\dienmayxanh_products.jsonl
# We should probably use a relative path or the one the user had.
# Let's use a local 'output' folder to be safe/portable.
OUTPUT_FILE = os.path.join(BASE_DIR, "dienmayxanh_products.jsonl")
CACHE_FILE = os.path.join(BASE_DIR, "dmx_cate_map.json")

CATEGORIES = {
    "1": {"name": "iPhone 15", "url": "https://www.dienmayxanh.com/iphone-15"},
    "2": {"name": "iPhone 14", "url": "https://www.dienmayxanh.com/iphone-14"},
    "3": {"name": "iPhone 13", "url": "https://www.dienmayxanh.com/iphone-13"},
    "4": {"name": "iPhone 12", "url": "https://www.dienmayxanh.com/iphone-12"},
    "5": {"name": "iPhone 11", "url": "https://www.dienmayxanh.com/iphone-11"},
    "7": {"name": "Samsung Galaxy S", "url": "https://www.dienmayxanh.com/dien-thoai-samsung-galaxy-s"},
    "8": {"name": "Samsung Galaxy Z", "url": "https://www.dienmayxanh.com/dien-thoai-samsung-galaxy-z"},
    "9": {"name": "Samsung Galaxy A", "url": "https://www.dienmayxanh.com/dien-thoai-samsung-galaxy-a"},
    "12": {"name": "Xiaomi 13", "url": "https://www.dienmayxanh.com/dien-thoai-xiaomi-13"},
    "14": {"name": "Redmi", "url": "https://www.dienmayxanh.com/dien-thoai-redmi"},
    "17": {"name": "OPPO Find", "url": "https://www.dienmayxanh.com/dien-thoai-oppo-find"},
    "18": {"name": "OPPO Reno", "url": "https://www.dienmayxanh.com/dien-thoai-oppo-reno"},
    "19": {"name": "OPPO A", "url": "https://www.dienmayxanh.com/dien-thoai-oppo-a"},
    # Add more as needed or keep simple for now
}

class DienMayXanhSpider:
    """DienMayXanh crawler using Optimized API approach"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.headers = DMX_HEADERS
        self.cookies = DMX_COOKIES
        self.cate_map = self._load_cate_map()
        self.page = None
        self.context = None
        self.browser = None
        
    def _load_cate_map(self) -> Dict[str, str]:
        if os.path.exists(CACHE_FILE):
            try:
                import json
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_cate_map(self):
        try:
            import json
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cate_map, f, ensure_ascii=False, indent=2)
        except: pass

    async def setup_browser(self, p):
        """Setup Playwright Browser"""
        self.browser = await p.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent=self.headers["User-Agent"],
            viewport={"width": 1280, "height": 720}
        )
        self.page = await self.context.new_page()
        
    async def cleanup(self):
        if self.page: await self.page.close()
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()

    async def scrape_category(self, category_url: str, max_pages: int = 50) -> List[Dict]:
        """
        Optimized Crawl: Check Map -> API Fast -> Fallback Playwright
        """
        products = []
        cate_id = self.cate_map.get(category_url)
        
        # 1. Try Cached API
        if cate_id:
            print(f"🚀 [Hit Cache] Using CateId {cate_id} for {category_url}")
            try:
               products = await self.crawl_category_fast(cate_id, category_url, max_pages)
               if products:
                   return products
            except Exception as e:
                print(f"⚠️ Cache crawl failed: {e}")

        # 2. Discovery (Playwright) if no cache or cache failed
        async with async_playwright() as p:
            await self.setup_browser(p)
            if not self.page: return []
            page = self.page
            
            print(f"📄 [Discovery] Visiting: {category_url}")
            try:
                await navigate_with_retry(page, category_url)
                
                # Check for block
                if await page.locator("text=chúng tôi xin lỗi").count() > 0:
                     print("🛑 [BLOCK] Site rejected connection.")
                     return []
                     
                # EXTRACT CATE ID
                cate_id = await page.evaluate("window.g_cateId || document.querySelector('#cateId')?.value || ''")
                if not cate_id:
                     try:
                         cate_id = await page.locator("#cateId, #g_cateId, input[name='cateId']").get_attribute("value")
                     except: pass
                
                if not cate_id:
                     content = await page.content()
                     m = re.search(r"cateId\s*=\s*(\d+)", content)
                     if m: cate_id = m.group(1)
                
                # Try locating from product item class (e.g. __cate_1944)
                if not cate_id:
                     try:
                         clazz = await page.locator(".item, .product-item").first.get_attribute("class")
                         if clazz:
                             m = re.search(r"__cate_(\d+)", clazz)
                             if m: cate_id = m.group(1)
                     except: pass

                if not cate_id:
                    print(f"⚠️ Discovery Failed. Switching to Playwright Fallback...")
                    return await self._crawl_playwright_fallback(page, category_url)
                
                # SUCCESS: Save to Map
                print(f"✅ Discovered CateId: {cate_id}")
                self.cate_map[category_url] = cate_id
                self._save_cate_map()
                
                # NOW RUN FAST API
                return await self.crawl_category_fast(cate_id, category_url, max_pages)
                            
            except Exception as e:
                print(f"\n❌ Init Error: {e}")
            finally:
                await self.cleanup()
                
        return products

    async def crawl_category_fast(self, cate_id: str, category_url: str, max_pages: int):
        """Windowed Concurrency Fetching"""
        total_products = []
        
        cookie_dict = {} # self.cookies is list? empty for now
        
        api_headers = self.headers.copy()
        api_headers["Referer"] = category_url
        api_headers["X-Requested-With"] = "XMLHttpRequest"
        api_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        window = 10 
        max_empty_streak = 2
        pi = 0
        empty_streak = 0
        
        print(f"🚀 Racing API (Window={window})...")
        sem = asyncio.Semaphore(10)
        
        async with aiohttp.ClientSession(cookies=cookie_dict, headers=api_headers) as session:
             while True:
                pis = list(range(pi, pi + window))
                
                tasks = [self._fetch_fragment(session, cate_id, p, sem) for p in pis]
                results = await asyncio.gather(*tasks)
                
                any_non_empty = False
                batch_items = []
                
                for pageno, html in zip(pis, results):
                    if not html:
                        empty_streak += 1
                        continue
                        
                    items = parse_items_from_html(html, category_url)
                    if not items:
                        empty_streak += 1
                        continue
                        
                    any_non_empty = True
                    empty_streak = 0
                    batch_items.extend(items)
                
                if batch_items:
                    total_products.extend(batch_items)

                print(f"📦 API Batch {pi}-{pi+window}: Captured {len(batch_items)} / Total {len(total_products)}", end='\r')
                
                if not any_non_empty or empty_streak >= max_empty_streak:
                    break
                    
                if len(total_products) > (max_pages * 20):
                    break

                pi += window
                await asyncio.sleep(0.05) 
                
        return total_products

    async def _fetch_fragment(self, session, cate_id, pi, sem):
        async with sem:
            payload = {
                "c": int(cate_id),
                "o": 3,
                "pi": pi,
                "IsParentCate": "False",
                "IsShowCompare": "True",
                "prevent": "true"
            }
            try:
                for _ in range(3):
                    async with session.post("https://www.dienmayxanh.com/Category/FilterProductBox", data=payload, timeout=60) as resp:
                        if resp.status == 200:
                            try:
                                data = await resp.json()
                                return data.get("listproducts", "")
                            except:
                                return await resp.text()
                        elif resp.status in [429, 503]:
                            await asyncio.sleep(2)
                        else:
                            break
            except: pass
        return None

    async def _crawl_playwright_fallback(self, page, category_url) -> List[Dict]:
        print(f"🔄 Starting Fallback Crawl (Scrolling)...")
        products = []
        try:
            try:
                await page.wait_for_selector('ul.listproduct, .listproduct', state='attached', timeout=10000)
            except:
                print("⚠️ Warning: Product list not immediately visible")
            
            view_more_clicks = 0
            max_clicks_session = 30
            
            while view_more_clicks < max_clicks_session:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                
                btn = None
                try:
                    for s in [".view-more", ".viewmore", "a.view-more"]:
                         if await page.locator(s).first.is_visible():
                             btn = page.locator(s).first
                             break
                except: pass
                
                if btn:
                    await btn.click(force=True, timeout=1000)
                    view_more_clicks += 1
                    print(f"👇 Loaded More ({view_more_clicks})...", end='\r')
                else: 
                     break

            print(f"\nParsing loaded items...")
            list_html = await page.inner_html("ul.listproduct, .listproduct")
            products = parse_items_from_html(list_html, category_url)
                
            print(f"📦 Fallback Parsed: {len(products)} items")
            
        except Exception as e:
             pass
        return products

# ================= EXECUTION =================

async def crawl_category_wrapper(spider, cat, existing_keys):
    """Crawl single category wrapper"""
    print(f"🚀 Starting Crawl: {cat['name']}")
    new_count = 0
    try:
        items = await spider.scrape_category(cat['url'], max_pages=50)
        for item in items:
            if not item.get("category"):
                item["category"] = cat["name"]
            if save_item(item, existing_keys, OUTPUT_FILE):
                new_count += 1
    except Exception as e:
        print(f"⚠️ Error crawling {cat['name']}: {e}")
    
    print(f"✅ Finished {cat['name']}. Saved {new_count} NEW items.")
    return new_count

async def process_all_categories(selected_cats, existing_keys):
    """Process categories in parallel chunks"""
    CATEGORY_PARALLEL = 4
    sem = asyncio.Semaphore(CATEGORY_PARALLEL)
    
    async def _worker(cat):
        async with sem:
             spider = DienMayXanhSpider(headless=True)
             try:
                 new_count = await crawl_category_wrapper(spider, cat, existing_keys)
                 return new_count
             except Exception as e:
                 print(f"\n⚠️ Task Failed {cat['name']}: {e}")
                 return 0
             finally:
                 await spider.cleanup()

    tasks = [_worker(cat) for cat in selected_cats]
    print(f"🔥 Launching {len(tasks)} tasks...")
    start_t = time.time()
    
    results = await asyncio.gather(*tasks)
    total_new_items = sum(results)
    
    print(f"\n🏁 Crawl Session Completed in {time.time() - start_t:.1f}s. Total New Items: {total_new_items}")

def main():
    print("===== DIENMAYXANH CRAWLER (REFACTORED) =====")
    print("\n📋 Danh mục có sẵn:")
    for cat_id, cat_info in sorted(CATEGORIES.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
        print(f"  {cat_id}. {cat_info['name']}")
    
    user_input = input("\n👉 Nhập ID (1,2) hoặc 'ALL': ").strip()
    if not user_input: return

    raw_inputs = []
    if user_input.upper() == "ALL":
        raw_inputs = list(CATEGORIES.keys())
    else:
        raw_inputs = [x.strip() for x in user_input.split(',') if x.strip()]
        
    selected_cats = []
    for inp in raw_inputs:
        if inp in CATEGORIES:
            selected_cats.append(CATEGORIES[inp])
        elif inp.startswith("http"):
            selected_cats.append({"name": "Custom URL", "url": inp})
            
    existing_keys = load_existing_keys(OUTPUT_FILE)
    
    try:
        asyncio.run(process_all_categories(selected_cats, existing_keys))
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")

if __name__ == "__main__":
    main()
