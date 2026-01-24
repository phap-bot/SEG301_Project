from utils import clean_text

# ================= PARSER LOGIC =================

def parse_price(price):
    """
    Parses the price field which can be a number, None, or a list.
    """
    if price is None:
        return 0
    if isinstance(price, list):
        return "-".join(map(str, price))
    return price

def parse_ad(ad, cg_id):
    """
    Extracts and standardizes ad data from the raw JSON object.
    Returns a dictionary if valid, or None if the ad should be skipped.
    """
    if not ad:
        return None

    ad_id = str(ad.get("list_id", "")).strip()
    if not ad_id:
        return None

    product_name = clean_text(ad.get("subject"))
    if not product_name or product_name == "Chưa có tên":
        return None

    cat_name = clean_text(ad.get("category_name")) or str(cg_id)

    record = {
        "platform": "Chotot",
        "product_id": ad_id,
        "product_name": product_name,
        "price": parse_price(ad.get("price")),
        "product_url": f"https://www.chotot.com/{ad_id}.htm",
        "image_url": ad.get("image", ""),
        "rating": ad.get("average_rating", 0.0),
        "review_count": ad.get("total_rating", 0),
        "category": cat_name,
    }
    return record
