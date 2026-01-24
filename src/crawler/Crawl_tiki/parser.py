import json

def parse_product(it, keyword):
    """
    Parse a single product item from the API response.
    """
    pid = str(it.get("id"))
    if not pid:
        return None

    price = it.get("price", 0)
    ori = it.get("original_price", 0)
    discount = round((ori - price) / ori * 100, 2) if ori else 0

    record = {
        "platform": "Tiki",
        "product_id": pid,
        "product_name": it.get("name", "").strip(),
        "price": price,
        "original_price": ori,
        "discount_percent": discount,
        "product_url": "https://tiki.vn/" + (it.get("url_path") or ""),
        "image_url": it.get("thumbnail_url"),
        "rating": it.get("rating_average", 0),
        "review_count": it.get("review_count", 0),
        "category": keyword,
    }
    return record
