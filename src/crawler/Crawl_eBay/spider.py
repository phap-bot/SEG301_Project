import asyncio
import random
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Import from local modules
from utils import (
    KEYWORDS, MAX_PAGE, SLEEP_RANGE, 
    load_seen_ids, load_checkpoint, save_checkpoint, save_item, 
    seen_lock
)
from parser import parse_item

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
            
            # Đợi một chút để eBay load
            await asyncio.sleep(random.uniform(*SLEEP_RANGE))
            
            content = await page_obj.content()
            
            if "captcha-delivery" in content or "distil_captcha" in content or "security check" in content.lower():
                print("  Detected Bot Protection! Try to wait or manual solve if needed.")
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
            for item_html in items:
                # Use parser to process item
                parsed_data = parse_item(item_html, keyword)
                
                if not parsed_data:
                    continue
                
                # Check duplication
                async with seen_lock:
                    if parsed_data["product_id"] in seen_ids:
                        continue
                    seen_ids.add(parsed_data["product_id"])

                # Save
                await save_item(parsed_data)
                new_count += 1

            if new_count > 0:
                print(f"  Saved {new_count} new products")
            
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
        page = await context.new_page()

        print(f"Starting crawl for {len(KEYWORDS)} keywords...")
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
