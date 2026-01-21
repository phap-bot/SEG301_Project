# parser.py
import re

def clean_text(text):
    if not text:
        return None
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text or None

def parse_chotot_ad(ad, category_fallback):
    ad_id = str(ad.get("list_id", "")).strip()
    if not ad_id:
        return None

    product_name = clean_text(ad.get("subject"))
    if not product_name or product_name == "Chưa có tên":
        return None

    price = ad.get("price", 0)
    if isinstance(price, list):
        price = "-".join(map(str, price))
    if price is None:
        price = 0

    image_url = ad.get("image") or ""
    category = clean_text(ad.get("category_name")) or category_fallback

    return {
        "platform": "Chotot",
        "product_id": ad_id,
        "product_name": product_name,
        "price": price,
        "product_url": f"https://www.chotot.com/{ad_id}.htm",
        "image_url": image_url,
        "rating": ad.get("average_rating", 0.0),
        "review_count": ad.get("total_rating", 0),
        "category": category,
    }
