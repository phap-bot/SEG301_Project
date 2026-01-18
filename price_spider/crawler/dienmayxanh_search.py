"""
DienMayXanh Spider - Sử dụng BaseSpider với cookies
"""
import asyncio
from typing import List, Dict, Optional
from crawler.spider import BaseSpider
from crawler.parser import (
    extract_text, extract_image_url, extract_product_url, parse_price, clean_text,
    extract_rating, extract_review_count, extract_original_price, calculate_discount_percent,
    extract_product_id_from_url, extract_category, normalize_url, normalize_image_url
)
from crawler.utils import safe_goto, scroll_to_bottom, random_delay, apply_stealth, navigate_with_retry, create_stealth_context, random_mouse_movement
from playwright.async_api import async_playwright

try:
    from crawler.entity_resolution import normalize_text
except ImportError:
    try:
        from entity_resolution import normalize_text
    except ImportError:
        def normalize_text(t): return t.lower()

# Cookies đầy đủ cho DienMayXanh (từ browser)

# Cookies minimized to avoid Playwright type errors
DMX_COOKIES = [
    {"domain": ".dienmayxanh.com", "name": "DMX_Personal", "path": "/", "value": "%7B%22CustomerId%22%3A0%2C%22CustomerSex%22%3A-1%2C%22CustomerName%22%3Anull%2C%22CustomerPhone%22%3Anull%2C%22CustomerMail%22%3Anull%2C%22Lat%22%3A0.0%2C%22Lng%22%3A0.0%2C%22Address%22%3Anull%2C%22CurrentUrl%22%3Anull%2C%22ProvinceId%22%3A1027%2C%22ProvinceType%22%3Anull%2C%22ProvinceName%22%3A%22H%E1%BB%93%20Ch%C3%AD%20Minh%22%2C%22DistrictId%22%3A0%2C%22DistrictType%22%3Anull%2C%22DistrictName%22%3Anull%2C%22WardId%22%3A0%2C%22WardType%22%3Anull%2C%22WardName%22%3Anull%2C%22StoreId%22%3A0%2C%22CouponCode%22%3Anull%2C%22HasLocation%22%3Afalse%7D", "expirationDate": 1802883707.089109, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "_gcl_gs", "path": "/", "value": "2.1.k1$i1768323709$u181333170", "expirationDate": 1776099710, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "_gcl_au", "path": "/", "value": "1.1.1069018065.1768323711", "expirationDate": 1776099711, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".www.dienmayxanh.com", "name": "utm_source", "path": "/", "value": "A8WKOm1Ng", "expirationDate": 1770915772, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "_ga", "path": "/", "value": "GA1.1.986625622.1768323711", "expirationDate": 1802883772.094618, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "cebs", "path": "/", "value": "1", "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "strict", "session": True},
    {"domain": "www.dienmayxanh.com", "name": "__uidac", "path": "/", "value": "0169667a7f5538639271bfe559490e79", "expirationDate": 1802883711.873162, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".www.dienmayxanh.com", "name": "__admUTMtime", "path": "/", "value": "1768323711", "expirationDate": 1770915711, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "_ce.clock_data", "path": "/", "value": "113989%2C1.53.167.33%2C1%2C89db729cfcdc129111f017b0e7ac324a%2CChrome%2CVN", "expirationDate": 1768410111, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "strict", "session": False},
    {"domain": ".dienmayxanh.com", "name": "_ce.s", "path": "/", "value": "v~99715d4d76984e34485001cbf4b6a923c5fe767b~lcw~1768323711884~vir~new~lva~1768323711419~vpv~0~v11.cs~454123~v11.s~8e733080-f0a1-11f0-a8ab-6f635d5da454~v11.vs~99715d4d76984e34485001cbf4b6a923c5fe767b~v11.fsvd~eyJ1cmwiOiJkaWVubWF5eGFuaC5jb20vbWF5LWxhbmgiLCJyZWYiOiJodHRwczovL3d3dy5nb29nbGUuY29tLyIsInV0bSI6WyJBOFdLT20xTmciLCIiLCIiLCIiLCIiXX0%3D~v11.sla~1768323711883~v11.wss~1768323711884~v11ls~8e733080-f0a1-11f0-a8ab-6f635d5da454~lcw~1768323711890", "expirationDate": 1799859787, "hostOnly": False, "httpOnly": False, "secure": True, "sameSite": "lax", "session": False},
    {"domain": ".www.dienmayxanh.com", "name": "__utm", "path": "/", "value": "source%3DA8WKOm1Ng", "expirationDate": 1770915713, "hostOnly": False, "httpOnly": False, "secure": True, "sameSite": "no_restriction", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__utm", "path": "/", "value": "source%3DA8WKOm1Ng", "expirationDate": 1770915713, "hostOnly": True, "httpOnly": False, "secure": True, "sameSite": "no_restriction", "session": False},
    {"domain": ".www.dienmayxanh.com", "name": "__iid", "path": "/", "value": "", "expirationDate": 1770915773, "hostOnly": False, "httpOnly": False, "secure": True, "sameSite": "no_restriction", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__iid", "path": "/", "value": "", "expirationDate": 1770915773, "hostOnly": True, "httpOnly": False, "secure": True, "sameSite": "no_restriction", "session": False},
    {"domain": ".www.dienmayxanh.com", "name": "__su", "path": "/", "value": "0", "expirationDate": 1770915773, "hostOnly": False, "httpOnly": False, "secure": True, "sameSite": "no_restriction", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__su", "path": "/", "value": "0", "expirationDate": 1770915773, "hostOnly": True, "httpOnly": False, "secure": True, "sameSite": "no_restriction", "session": False},
    {"domain": ".www.dienmayxanh.com", "name": "_aff_network", "path": "/", "value": "A8WKOm1Ng", "expirationDate": 1768928573, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".www.dienmayxanh.com", "name": "_aff_sid", "path": "/", "value": "zKEfFlztH2ABuyJLMJG2KUzQX4HD8_DIuFExQdl4LIM", "expirationDate": 1768928573, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "_fbp", "path": "/", "value": "fb.1.1768323714377.230435584547529456", "expirationDate": 1776099773, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "lax", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__RC", "path": "/", "value": "5", "expirationDate": 1802883715.504536, "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__R", "path": "/", "value": "3", "expirationDate": 1802883715.504941, "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "TBMCookie_3209819802479625248", "path": "/", "value": "4379930017683235961mnWl/lZWtOaP9/syNlcvurRj+8=", "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": True},
    {"domain": "www.dienmayxanh.com", "name": "___utmvm", "path": "/", "value": "###########", "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": True},
    {"domain": ".dienmayxanh.com", "name": "_gcl_aw", "path": "/", "value": "GCL.1768323772.CjwKCAiA95fLBhBPEiwATXUsxOn8z6e1raVmfLKSnhKjoBfad_qXfCCfPc4TQcvCPydwVFzmIy_ZGxoCK28QAvD_BwE", "expirationDate": 1776099772, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "cebsp_", "path": "/", "value": "2", "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "strict", "session": True},
    {"domain": ".dienmayxanh.com", "name": "_ga_Y7SWKJEHCE", "path": "/", "value": "GS2.1.s1768323710$o1$g1$t1768323773$j58$l0$h0", "expirationDate": 1802883773.171218, "hostOnly": False, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__uif", "path": "/", "value": "__uid%3A1635552648486634292%7C__ui%3A-1%7C__create%3A1761676784", "expirationDate": 1769187773, "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__tb", "path": "/", "value": "0", "expirationDate": 1802883773.835919, "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "__IP", "path": "/", "value": "20293409", "expirationDate": 1802883773.836194, "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": False},
    {"domain": ".dienmayxanh.com", "name": "ph_phc_SwFSIEWXGyEFX8K1CHR0SXqFF1itXUusCCgGgvSGlEk_posthog", "path": "/", "value": "%7B%22distinct_id%22%3A%22019bb84e-8019-7317-93c9-2d72403994b9%22%2C%22%24sesid%22%3A%5B1768323787270%2C%22019bb84e-8019-7317-93c9-2d70d9fc8000%22%2C1768323711001%5D%2C%22%24epp%22%3Atrue%2C%22%24initial_person_info%22%3A%7B%22r%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22u%22%3A%22https%3A%2F%2Fwww.dienmayxanh.com%2Fmay-lanh%3Futm_source%3DA8WKOm1Ng%26click_id%3DzKEfFlztH2ABuyJLMJG2KUzQX4HD8_DIuFExQdl4LIM%26gad_source%3D1%26gad_campaignid%3D22253923118%26gbraid%3D0AAAAA-dRZ4pZYv0xM7L4ITGL8T4OQFk6v%26gclid%3DCjwKCAiA95fLBhBPEiwATXUsxOn8z6e1raVmfLKSnhKjoBfad_qXfCCfPc4TQcvCPydwVFzmIy_ZGxoCK28QAvD_BwE%22%7D%7D", "expirationDate": 1799859787, "hostOnly": False, "httpOnly": False, "secure": True, "sameSite": "lax", "session": False},
    {"domain": "www.dienmayxanh.com", "name": "SvID", "path": "/", "value": "new2691|aWZ6X|aWZ6D", "hostOnly": True, "httpOnly": False, "secure": False, "sameSite": "unspecified", "session": True},
]

# Headers đầy đủ cho DienMayXanh để bypass anti-bot
DMX_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://www.google.com/",
    "Origin": "https://www.dienmayxanh.com",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate", 
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive"
}


class DienMayXanhSpider(BaseSpider):
    """DienMayXanh crawler sử dụng BaseSpider với cookies"""
    
    def __init__(self, headless=True, use_proxy=False, cookies: Optional[List[Dict]] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(
            source_name="DienMayXanh",
            base_url="https://www.dienmayxanh.com",
            headless=headless,
            use_proxy=use_proxy,
            headers=headers or DMX_HEADERS
        )
        self.cookies = cookies or DMX_COOKIES
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """Build DienMayXanh search URL (không có pagination)"""
        from urllib.parse import quote_plus
        encoded_keyword = quote_plus(keyword)
        return f"https://www.dienmayxanh.com/tim-kiem?key={encoded_keyword}"
    
    def get_product_selector(self) -> str:
        """DienMayXanh product selector - thử nhiều selector"""
        return 'ul.listproduct li.item, .listproduct .item, .product-item, a.product-item'
    
    async def scrape_category(self, category_url: str, max_pages: int = 50, on_items_crawled=None) -> List[Dict]:
        """
        Crawl theo Category URL với Anti-Blocking nâng cao (Human Emulation)
        """
        import random
        products = []
        
        async with async_playwright() as p:
            await self.setup_browser(p, cookies=self.cookies, headers=self.headers)
            
            if not self.page:
                return []
            
            page = self.page
            
            try:
                # 1. Logical Flow: Go to Home first
                print(f"🏠 [DienMayXanh] Visiting Homepage first...")
                await navigate_with_retry(page, "https://www.dienmayxanh.com/")
                await asyncio.sleep(random.uniform(0.5, 1.0)) # Minimized
                
                # 2. Go to Category
                print(f"📄 [DienMayXanh] Navigating: {category_url}")
                await navigate_with_retry(page, category_url)
                
                # Check for block
                if await page.locator("text=chúng tôi xin lỗi").count() > 0:
                    print("🛑 [BLOCK DETECTED] Site rejected connection. Exiting...")
                    return []

                # Wait for list
                try:
                    await page.wait_for_selector('ul.listproduct, .listproduct', state='attached', timeout=15000)
                except:
                    print("⚠️ Warning: Product list not immediately visible")
                
                print(f"🚀 [DienMayXanh] TURBO MODE: Event-Driven Crawling (Fix)...")
                
                view_more_clicks = 0
                max_clicks_session = 9999
                
                # Faster selector reuse
                item_selector = "ul.listproduct li.item, .listproduct .item"
                view_more_selector = ".view-more, .viewmore, a.view-more, .btn-viewmore"
                
                # Initial Parse
                last_count = await page.locator(item_selector).count()
                parsed_count = 0
                
                # Parse initial batch
                # Parse initial batch
                sem = asyncio.Semaphore(8) # Limit concurrent tabs

                if last_count > 0:
                    try:
                        current_items = await page.locator(item_selector).all()
                        # Use helper for concurrent processing
                        valid_p = await self.process_items_concurrently(current_items, self.context, sem)
                        
                        products.extend(valid_p)
                            
                        # Initial Callback
                        if on_items_crawled:
                            on_items_crawled(valid_p)

                        parsed_count = last_count
                        print(f"📦 Items: {len(products)}", end='\r')
                    except Exception as e:
                        print(f"Initial batch error: {e}")
                        pass

                consecutive_stuck_count = 0
                
                while view_more_clicks < max_clicks_session:
                    try:
                        # 1. Check Button Visibility
                        if page.is_closed(): break
                        
                        btn = None
                        try:
                            for selector in [".view-more", ".viewmore", "a.view-more", ".btn-viewmore"]:
                                 b = page.locator(selector).first
                                 if await b.is_visible():
                                     btn = b
                                     break
                        except: pass
                        
                        if btn:
                            # CLICK
                            await btn.click(force=True, timeout=2000)
                            view_more_clicks += 1
                            
                            # Minimal Log
                            # print(f"⚡ Loading...", end='\r') 
                            
                            # 2. SMART WAIT
                            try:
                                await page.wait_for_function(
                                    f"document.querySelectorAll('{item_selector}').length > {last_count}",
                                    timeout=8000
                                )
                                # items loaded
                                new_count = await page.locator(item_selector).count()
                                
                                if new_count > last_count:
                                    # 3. INCREMENTAL PARSE
                                    current_items = await page.locator(item_selector).all()
                                    
                                    
                                    # Parse only new items
                                    start_idx = parsed_count
                                    end_idx = len(current_items)
                                    
                                    # Slicing for batch
                                    batch_items = current_items[start_idx:end_idx]
                                    
                                    if batch_items:
                                        batch_valid = await self.process_items_concurrently(batch_items, self.context, sem)
                                        products.extend(batch_valid)
                                        
                                        # Incremental Callback
                                        if on_items_crawled:
                                            on_items_crawled(batch_valid)
                                    
                                    parsed_count = end_idx
                                    last_count = new_count
                                    consecutive_stuck_count = 0 
                                    
                                    # Minimal Update
                                    print(f"📦 Items: {len(products)}", end='\r')
                                else:
                                    consecutive_stuck_count += 1
                            except Exception:
                                consecutive_stuck_count += 1
                                
                            if consecutive_stuck_count >= 5:
                                break
                                
                        else:
                            # No button visible - Scroll
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            await asyncio.sleep(1) 
                            
                            if not page.is_closed() and await page.locator(view_more_selector).first.is_visible():
                                continue
                                
                            # End Check
                            h1 = await page.evaluate("document.body.scrollHeight")
                            await asyncio.sleep(1)
                            h2 = await page.evaluate("document.body.scrollHeight")
                            
                            if h1 == h2:
                                 break
                    except Exception as e:
                        # If critical error (closed), stop
                        if "closed" in str(e).lower():
                            break
                        await asyncio.sleep(1)

                print(f"\n✅ Finished. Total captured: {len(products)}")


            except KeyboardInterrupt:
                print(f"\n🛑 STOPPING CRAWLER (User Interrupt)...")
                print(f"✅ Preservation: Saving {len(products)} collected items before exit.")
            except Exception as e:
                print(f"❌ Error scraping: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await self.cleanup()
                
        return products
    async def extract_review_count_helper(self, locator) -> int:
        """
        Extract review count specifically for DMX
        Priority: .point-alltimerate -> regex '(\\d+) đánh giá'
        """
        try:
            # 1. Specific Selector (Preferred)
            # User specifically asked to avoid .point-satisfied
            el = locator.locator('.point-alltimerate').first
            if await el.is_visible():
                txt = await extract_text(el)
                if txt:
                     import re
                     # Strict regex for "number before đánh giá"
                     # Handle "12 đánh giá" or "1.2k đánh giá" (DMX usually just numbers)
                     m = re.search(r'([\d.,]+)\s*đánh giá', txt, re.IGNORECASE)
                     if m:
                         # Remove dots/commas before int conversion
                         raw_num = m.group(1).replace('.', '').replace(',', '')
                         return int(raw_num)
                     
                     # Fallback if just number in the specific class?
                     nums = re.findall(r'\d+', txt.replace('.', '').replace(',', ''))
                     if nums:
                         return int(nums[0])

            # 2. Regex on the whole element text (Fallback)
            # Use strict pattern to avoid "khách hài lòng"
            full_text = await extract_text(locator)
            if full_text:
                import re
                
                # P2: Strict Review Count
                m = re.search(r'([\d.,]+)\s*đánh giá', full_text, re.IGNORECASE)
                if m:
                    raw_num = m.group(1).replace('.', '').replace(',', '')
                    return int(raw_num)
                
                # P3: Satisfied Customer Fallback (User Requested)
                # Matches: "42,4k khách hài lòng", "120 khách hài lòng"
                m_sat = re.search(r'([\d.,]+)(k?)\s*khách hài lòng', full_text, re.IGNORECASE)
                if m_sat:
                    num_part = m_sat.group(1)
                    unit_part = m_sat.group(2).lower()
                    
                    if unit_part == 'k':
                        # Handle "42,4" -> 42.4
                        num_part = num_part.replace(',', '.')
                        return int(float(num_part) * 1000)
                    else:
                        # Handle "120" -> 120 (remove dots/commas if any, e.g. 1.200)
                        return int(num_part.replace('.', '').replace(',', ''))
                    
        except Exception:
            pass
            
        return 0

    async def parse_detail_page(self, context, listing_data: Dict, sem: asyncio.Semaphore) -> Dict:
        """
        Deep Crawl: Open new tab to fetch details (Review Count, Specs)
        Protected by Semaphore to limit concurrency.
        """
        url = listing_data.get('product_url')
        if not url: return listing_data
        
        async with sem:
            page = None
            try:
                page = await context.new_page()
                # Block media/css for speed
                await page.route("**/*.{png,jpg,jpeg,gif,css,woff,woff2,svg,mp4}", lambda route: route.abort())
                
                # Fast timeout (don't wait too long for deep crawl)
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                
                # --- Extract Deep Data ---
                body_content = await page.content()
                import re
                
                # 1. Review Count (Priority: Detail Page Specifics)
                # Matches "12 đánh giá" anywhere in body
                m_rev = re.search(r'(\d+)\s*đánh giá', body_content, re.IGNORECASE)
                if m_rev:
                    deep_count = int(m_rev.group(1))
                    # Only update if we found a valid number (Listing might have 'Satisfied' fallback)
                    # Use deep count if > 0, or if listing was 0
                    if deep_count > 0:
                        listing_data['review_count'] = deep_count
                        # listing_data['source_review'] = 'detail_page'

                # 2. Rating (More accurate on detail page)
                m_rating = re.search(r'class="point-average-score"[^>]*>([\d.,]+)', body_content)
                if m_rating:
                     pass # listing usually accurate enough for rating, but can update if needed
                     
            except Exception as e:
                # print(f"Deep crawl failed for {url}: {e}")
                pass
            finally:
                if page: await page.close()
                
        return listing_data

    async def process_items_concurrently(self, items, context, sem) -> List[Dict]:
        """
        Helper: Listing Parse -> Geometric Deep Fetch
        """
        # 1. Listing Parse (Fast, Parallel)
        tasks = [self.parse_listing_item(item, keyword="", location="Toàn quốc") for item in items]
        listing_results = await asyncio.gather(*tasks)
        valid_items = [i for i in listing_results if i]
        
        # 2. Deep Crawl (Concurrent limited by sem)
        deep_tasks = []
        for item in valid_items:
            deep_tasks.append(self.parse_detail_page(context, item, sem))
            
        final_items = await asyncio.gather(*deep_tasks)
        return final_items

    async def parse_listing_item(self, item_locator, keyword: str = "", location: str = "Toàn quốc") -> Optional[Dict]:
        """
        Parse DienMayXanh product item với format Nested JSON và filter accuracy
        """
        # --- 1. Extract Info ---
        
        # Name
        name = ""
        try:
            name_el = item_locator.locator('h3, .product-name, .name, a[title]').first
            name = await extract_text(name_el)
            if not name:
                name = await item_locator.get_attribute("title")
        except:
            pass
            
        if not name: return None
        name = clean_text(name)
        

        # Price
        price = 0.0
        try:
            price_el = item_locator.locator('.price, .price-current, .price-sale').first
            price = parse_price(await extract_text(price_el))
        except: pass
        
        # Original Price
        original_price = await extract_original_price(item_locator)
        discount_percent = calculate_discount_percent(original_price, price) if original_price > 0 else 0.0
        
        # URL & ID
        url = await extract_product_url(item_locator, self.base_url)
        
        # ID Extraction: Prioritize data-product-id
        product_id = ""
        try:
            product_id = await item_locator.get_attribute("data-product-id")
        except: pass

        # Image
        image_url = await extract_image_url(item_locator, self.base_url)
        
        # --- Discount Scraping (User Request: Crawl accurately) ---
        crawled_percent = 0.0
        try:
            # 1. Try DMX specific voucher badge
            discount_el = item_locator.locator('.border-voucher-pmh, .percent, .discount').first
            discount_text = await extract_text(discount_el)
            
            if discount_text:
                import re
                match = re.search(r'(\d+)\s*%', discount_text)
                if match:
                    crawled_percent = float(match.group(1))
        except:
            pass

        # Calculate logical discount
        calc_percent = calculate_discount_percent(original_price, price)
        
        # FINAL DECISION: Prioritize crawled badge if it exists and looks valid
        discount_percent = crawled_percent if crawled_percent > 0 else calc_percent

        # --- ID Validation (Fallback) ---
        if not product_id or len(str(product_id)) < 3:
             extracted_id = extract_product_id_from_url(url)
             if extracted_id and len(extracted_id) >= 3:
                 product_id = extracted_id
             else:
                 import hashlib
                 product_id = hashlib.md5(url.encode()).hexdigest()[:10]

        # Review Count
        review_count = 0
        # Review Count (Refined per instructions)
        review_count = await self.extract_review_count_helper(item_locator)

        
        # Rating (User Step 1212: Fix based on provided class)
        rating = 0.0
        try:
            # Priority 1: User specific class .point-average-score (e.g. "2")
            rating_el = item_locator.locator('.point-average-score').first
            rating_text = await extract_text(rating_el)
            if rating_text:
                rating = float(rating_text.replace(',', '.'))
            else:
                # Priority 2: Generic DMX classes
                rating = await extract_rating(item_locator)
        except:
            rating = await extract_rating(item_locator)
        
        # Category
        category = await extract_category(item_locator)
        
        # Location (New request)
        location = "Toàn quốc" # Default for DMX e-commerce
        try:
            # Sometimes location is represented in stock status or specific localized text, but rarely on search page
            # We fulfill the field requirement with a default or extracted value if found
            pass
        except: pass

        # Scrape Time
        from datetime import datetime
        scraped_at = datetime.now().isoformat()
        
        # Scrape Time
        from datetime import datetime
        scraped_at = datetime.now().isoformat()
        
        # --- 3. Construct Flat JSON (User requested format) ---
        discount_amount = max(original_price - price, 0) if original_price > price else 0.0
        
        return {
            "platform": "DienMayXanh",
            "product_id": str(product_id) if product_id else "unknown",
            "product_name": name,
            "price": float(price),
            "original_price": float(original_price),
            "discount_amount": float(discount_amount),
            "discount_percent": float(discount_percent),
            "product_url": url if url else "",
            "image_url": image_url if image_url else "",
            "rating": float(rating),
            "review_count": int(review_count),
            "category": keyword or category, # Prioritize keyword to match user sample, fallback to scraped
            "location": location,
            "scraped_at": scraped_at
        }


def search(keyword, max_pages=50):
    """Sync wrapper for main.py integration"""
    spider = DienMayXanhSpider(headless=True)
    return spider.run_sync(keyword, max_pages=max_pages)
