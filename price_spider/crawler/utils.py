"""
Utils module: Helper functions
"""
import asyncio
import random
from typing import Optional, Dict, List
import hashlib
from playwright.async_api import Page, BrowserContext, async_playwright

# Try to import stealth - simplify for debugging
try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page: Page):
        pass

# User-Agent pool
USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"]

PROXY_POOL = []

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

def get_random_proxy() -> Optional[str]:
    if PROXY_POOL:
        return random.choice(PROXY_POOL)
    return None

def load_proxies_from_file(filepath: str) -> List[str]:
    try:
        with open(filepath, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except FileNotFoundError:
        return []

async def random_delay(min_sec: float = 0.1, max_sec: float = 0.3):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def human_like_delay():
    await random_delay(0.2, 0.5)

async def quick_delay():
    await random_delay(0.05, 0.15)

async def scroll_to_bottom(page: Page, scroll_steps: int = 3, step_delay: float = 0.1):
    for i in range(scroll_steps):
        scroll_distance = random.randint(800, 1200)
        await page.mouse.wheel(0, scroll_distance)
        await asyncio.sleep(step_delay)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(0.2)
    
def normalize_product_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(name.lower().split())

def generate_dedup_key(platform: str, product_name: str, product_url: str) -> str:
    raw_key = f"{platform}|{normalize_product_name(product_name)}|{product_url}"
    return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

async def random_mouse_movement(page: Page):
    """
    Simulate random mouse movements to appear human
    """
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y, steps=random.randint(5, 20))
        await asyncio.sleep(random.uniform(0.1, 0.3))

async def create_stealth_context(playwright, headless: bool = True, proxy: Optional[str] = None, cookies: Optional[List[Dict]] = None, extra_http_headers: Optional[Dict[str, str]] = None):
    user_agent = get_random_user_agent()
    
    context_options = {
        "user_agent": user_agent,
        "viewport": {"width": 1280, "height": 800},
        "locale": "vi-VN",
        "timezone_id": "Asia/Ho_Chi_Minh",
        "ignore_https_errors": True,
    }
    
    if proxy:
        context_options["proxy"] = {"server": proxy}

    if extra_http_headers:
        context_options["extra_http_headers"] = extra_http_headers
    
    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-images",
            "--disable-javascript-harmony-shipping",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-ipc-flooding-protection",
        ]
    )
    
    context = await browser.new_context(**context_options)
    
    if cookies:
        context._cookies_to_add = cookies
    
    async def route_handler(route):
        resource_type = route.request.resource_type
        if resource_type in ["image", "media", "font"]:
            await route.abort()
        else:
            await route.continue_()
    
    await context.route("**/*", route_handler)
    
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['vi-VN', 'vi', 'en-US', 'en']
        });
    """)
    
    return context, browser

async def apply_stealth(page: Page):
    await stealth_async(page)
    await page.add_init_script("""
        window.chrome = {
            runtime: {}
        };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)

async def navigate_with_retry(page: Page, url: str, timeout: int = 20000, retries: int = 1):
    return await safe_goto(page, url, timeout, retries)

async def safe_goto(page: Page, url: str, timeout: int = 20000, retries: int = 1, cookies: Optional[List[Dict]] = None):
    for attempt in range(retries):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            if cookies:
                formatted_cookies = []
                for cookie in cookies:
                    if isinstance(cookie, dict):
                        cookie_dict = {
                            "name": cookie.get("name", ""),
                            "value": cookie.get("value", ""),
                            "domain": cookie.get("domain", "").lstrip("."),
                            "path": cookie.get("path", "/"),
                            "url": url,
                        }
                        if "expirationDate" in cookie and cookie["expirationDate"]:
                            cookie_dict["expires"] = int(cookie["expirationDate"])
                        if "secure" in cookie:
                            cookie_dict["secure"] = cookie["secure"]
                        if "httpOnly" in cookie:
                            cookie_dict["httpOnly"] = cookie["httpOnly"]
                        if "sameSite" in cookie and cookie["sameSite"] != "unspecified":
                            same_site_map = {"strict": "Strict", "lax": "Lax", "none": "None"}
                            cookie_dict["sameSite"] = same_site_map.get(cookie["sameSite"], "Lax")
                        formatted_cookies.append(cookie_dict)
                if formatted_cookies:
                    try:
                        await page.context.add_cookies(formatted_cookies)
                    except: pass
            await random_delay(0.05, 0.1)
            return True
        except:
            if attempt < retries - 1:
                await random_delay(0.2, 0.4)
    return False
