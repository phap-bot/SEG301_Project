# parser.py
def parse_tiki_product(item, keyword):
    product_id = item.get("id")
    if not product_id:
        return None

    price = item.get("price", 0)
    original_price = item.get("original_price", 0)
    discount_percent = (
        round((original_price - price) / original_price * 100, 2)
        if original_price else 0
    )

    return {
        "platform": "Tiki",
        "product_id": str(product_id),
        "product_name": item.get("name", "").strip(),
        "price": price,
        "original_price": original_price,
        "discount_percent": discount_percent,
        "product_url": "https://tiki.vn/" + (item.get("url_path") or ""),
        "image_url": item.get("thumbnail_url"),
        "rating": item.get("rating_average", 0),
        "review_count": item.get("review_count", 0),
        "category": keyword
    }
