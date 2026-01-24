import os
import json
import time
import random
import re
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ================= CONFIG =================
KEYWORDS = [
    # Electronics & Computers (30 keywords)
    "laptop", "gaming laptop", "macbook", "chromebook", "tablet", "ipad", "kindle",
    "desktop computer", "gaming pc", "mini pc", "all in one pc",
    "graphics card", "cpu processor", "motherboard", "ram memory", "ssd hard drive",
    "power supply", "pc case", "cpu cooler", "gaming monitor", "4k monitor",
    "wireless mouse", "mechanical keyboard", "gaming headset", "webcam", "usb hub",
    "external hard drive", "portable ssd", "network switch", "wifi router",
]

MAX_PAGE = 20 
SLEEP_RANGE = (2.0, 5.0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "ebay_products.jsonl")
CHECKPOINT_FILE = os.path.join(BASE_DIR, "checkpoint.json")

# Thread-safe locks replaced with asyncio locks
file_lock = asyncio.Lock()
seen_lock = asyncio.Lock()
checkpoint_lock = asyncio.Lock()
total_saved = 0

# ================= CHECKPOINT MANAGEMENT =================
def load_checkpoint():
    """Load checkpoint data from file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

async def save_checkpoint(checkpoint_data):
    """Save checkpoint data to file"""
    async with checkpoint_lock:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

# ================= LOAD SEEN IDS =================
def load_seen_ids():
    seen = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "product_id" in data:
                        seen.add(data["product_id"])
                except:
                    pass
    print(f"Loaded seen_ids: {len(seen)}")
    global total_saved
    total_saved = len(seen)
    return seen

# ================= SAVE =================
async def save_item(item):
    async with file_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

# ================= CRAWL =================
async def crawl_keyword(keyword, seen_ids, page_obj, checkpoint_data):
    print(f"\n[eBay Scraper] keyword='{keyword}'")
    
    # Check if keyword is already completed
    if checkpoint_data.get(keyword, {}).get("status") == "completed":
        print(f"  Keyword '{keyword}' already completed. Skipping.")
        return
    
    # Get starting page from checkpoint
    start_page = checkpoint_data.get(keyword, {}).get("last_page", 0) + 1
    if start_page > 1:
        print(f"  Resuming from page {start_page}")

    for pgn in range(start_page, MAX_PAGE + 1):
        search_url = f"https://www.ebay.com/sch/i.html?_nkw={keyword.replace(' ', '+')}&_pgn={pgn}&_ipg=60"
        print(f" Page {pgn} | URL: {search_url}")

        try:
            # Truy cập trang bằng Playwright
            await page_obj.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            
            # Đợi một chút để eBay load (và có thể vượt qua kiểm tra bot đơn giản)
            await asyncio.sleep(random.uniform(*SLEEP_RANGE))
            
            content = await page_obj.content()
            
            if "captcha-delivery" in content or "distil_captcha" in content or "security check" in content.lower():
                print("  Detected Bot Protection! Try to wait or manual solve if needed.")
                # Save checkpoint before breaking
                checkpoint_data[keyword] = {"last_page": pgn - 1, "status": "blocked"}
                await save_checkpoint(checkpoint_data)
                break
                
            soup = BeautifulSoup(content, 'lxml')
            
            # Tìm danh sách sản phẩm
            items = soup.select('li.s-item') or soup.select('li.s-card')
            
            if not items:
                print("  No items found on this page. Possible block or no results.")
                checkpoint_data[keyword] = {"last_page": pgn - 1, "status": "no_items"}
                await save_checkpoint(checkpoint_data)
                break

            new_count = 0
            for item in items:
                try:
                    # Lấy Title
                    title_el = item.select_one('.s-item__title') or item.select_one('.s-card__title')
                    if not title_el: continue
                    title = title_el.get_text(strip=True)
                    if "Shop on eBay" in title: continue

                    # Lấy Link và ID
                    link_el = item.select_one('a.s-item__link') or item.select_one('a.s-card__link')
                    if not link_el: continue
                    url = link_el['href'].split('?')[0]
                    
                    product_id = None
                    if "/itm/" in url:
                        product_id = url.split("/itm/")[1].split("/")[0].split("?")[0]
                    
                    if not product_id: continue

                    async with seen_lock:
                        if product_id in seen_ids:
                            continue
                        seen_ids.add(product_id)

                    # Lấy Price và format thành số
                    price_el = item.select_one('.s-item__price') or item.select_one('.s-card__attribute-row')
                    price_text = price_el.get_text(strip=True) if price_el else "0"
                    
                    # Regex lấy số đầu tiên thấy được (xử lý case "1,200 VND to 1,500 VND")
                    price_val = 0.0
                    try:
                        # Tìm tất cả cụm số có thể có dấu phẩy hoặc chấm
                        # VD: 5,016,352.35 -> 5016352.35
                        nums = re.findall(r'[\d\.,]+', price_text)
                        if nums:
                            clean_num = nums[0].replace(',', '')
                            # Nếu có nhiều hơn 1 dấu chấm, giả định dấu chấm cuối là thập phân
                            if clean_num.count('.') > 1:
                                parts = clean_num.split('.')
                                clean_num = "".join(parts[:-1]) + "." + parts[-1]
                            price_val = float(clean_num)
                    except:
                        pass

                    # Lấy Rating
                    rating_el = (
                        item.select_one('.x-star-rating') or 
                        item.select_one('.s-item__stars') or
                        item.select_one('.s-card__stars') or
                        item.select_one('[class*="star-rating"]')
                    )
                    rating = "0"
                    if rating_el:
                        # Thử lấy text, nếu không có thì thử lấy aria-label
                        rating_text = rating_el.get_text(strip=True) or rating_el.get('aria-label') or ""
                        r_match = re.search(r'(\d[\d\.]*)', rating_text)
                        if r_match:
                            rating = r_match.group(1)
                    
                    # Fallback nếu selector trên fail, search trong toàn bộ item text
                    if rating == "0":
                        item_text = item.get_text(" ", strip=True)
                        # Tìm mẫu "4.5 out of 5 stars"
                        r_match = re.search(r'(\d[\d\.]*)\\s*out of 5 stars', item_text, re.IGNORECASE)
                        if r_match:
                            rating = r_match.group(1)

                    # Lấy Review Count
                    reviews_el = (
                        item.select_one('.s-item__reviews-count') or 
                        item.select_one('.s-item__review-count') or
                        item.select_one('.s-card__reviews-count') or
                        item.select_one('.s-item__reviews')
                    )
                    review_count = "0"
                    if reviews_el:
                        review_count_text = reviews_el.get_text(strip=True)
                        rv_match = re.search(r'(\d[\d\.,]*)', review_count_text)
                        if rv_match:
                            review_count = rv_match.group(1).replace(',', '')
                    
                    # Fallback review count
                    if review_count == "0":
                        item_text = item.get_text(" ", strip=True)
                        # Tìm "120 product ratings" hoặc "(120)" sau rating
                        rv_match = re.search(r'(\d[\d\.,]*)\s*product ratings', item_text, re.IGNORECASE)
                        if rv_match:
                            review_count = rv_match.group(1).replace(',', '')

                    # Lấy Image
                    img_el = item.select_one('.s-item__image-img') or item.select_one('img')
                    image = img_el.get('src') or img_el.get('data-src') if img_el else None

                    await save_item({
                        "platform": "ebay",
                        "product_id": product_id,
                        "product_name": title,
                        "price": price_val,
                        "product_url": url,
                        "image_url": image,
                        "rating": rating,
                        "review_count": review_count,
                        "category": keyword,
                    })
                    new_count += 1
                except:
                    continue

            if new_count > 0:
                print(f"  Saved {new_count} new products")
                global total_saved
                total_saved += new_count
                print(f"  [Progress] Total unique products: {total_saved:,} / 200,000")
            
            # Update checkpoint after successful page
            checkpoint_data[keyword] = {"last_page": pgn, "status": "in_progress"}
            await save_checkpoint(checkpoint_data)
            
            # Check pagination
            if not soup.select_one('.pagination__next'):
                print("  Reached last page.")
                checkpoint_data[keyword] = {"last_page": pgn, "status": "completed"}
                await save_checkpoint(checkpoint_data)
                break

        except Exception as e:
            print(f"  Error on page {pgn}: {e}")
            checkpoint_data[keyword] = {"last_page": pgn - 1, "status": "error"}
            await save_checkpoint(checkpoint_data)
            break
    
    # Mark as completed if we finished all pages
    if pgn == MAX_PAGE:
        checkpoint_data[keyword] = {"last_page": MAX_PAGE, "status": "completed"}
        await save_checkpoint(checkpoint_data)

# ================= MAIN =================
async def main():
    seen_ids = load_seen_ids()
    checkpoint_data = load_checkpoint()
    
    async with async_playwright() as p:
        # Chạy trình duyệt ẩn danh
        browser = await p.chromium.launch(headless=True)
        # Fake một số thông tin để bớt giống bot
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        # Create tasks for all keywords
        page = await context.new_page()   # ✅ CHỈ TẠO 1 PAGE DUY NHẤT

        for kw in KEYWORDS:
            await crawl_keyword(
                kw,
                seen_ids,
                page,
                checkpoint_data,
            )

        
        await browser.close()
        
    print("\n[Done] Crawling finished.")

if __name__ == "__main__":
    asyncio.run(main())
