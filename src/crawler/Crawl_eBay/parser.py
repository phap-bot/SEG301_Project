import re

# ================= ITEM PARSER =================

def parse_item(item, keyword):
    """
    Parse a single eBay product item (BeautifulSoup element).
    Returns a dictionary or None if invalid.
    """
    try:
        # Lấy Title
        title_el = item.select_one('.s-item__title') or item.select_one('.s-card__title')
        if not title_el: return None
        title = title_el.get_text(strip=True)
        if "Shop on eBay" in title: return None

        # Lấy Link và ID
        link_el = item.select_one('a.s-item__link') or item.select_one('a.s-card__link')
        if not link_el: return None
        url = link_el['href'].split('?')[0]
        
        product_id = None
        if "/itm/" in url:
            try:
                product_id = url.split("/itm/")[1].split("/")[0].split("?")[0]
            except:
                pass
        
        if not product_id: return None

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

        return {
            "platform": "ebay",
            "product_id": product_id,
            "product_name": title,
            "price": price_val,
            "product_url": url,
            "image_url": image,
            "rating": rating,
            "review_count": review_count,
            "category": keyword,
        }
    except:
        return None
