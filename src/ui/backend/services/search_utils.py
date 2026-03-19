from __future__ import annotations

import datetime
import re
from typing import Any, List, Optional


def dummy_tokenize(query: str) -> str:
    return query.strip().lower()


def normalize_platform_filter(values: List[str]) -> List[str]:
    if not values:
        return []

    mapping = {
        "lazada": "lazada",
        "Lazada": "lazada",
        "cellphones": "cellphones",
        "CellphoneS": "cellphones",
        "tiki": "tiki",
        "Tiki": "tiki",
        "chotot": "Chotot",
        "Chotot": "Chotot",
        "Chợ Tốt": "Chotot",
        "dienmayxanh": "DienMayXanh",
        "DienMayXanh": "DienMayXanh",
        "Điện Máy Xanh": "DienMayXanh",
        "fptshop": "FPTShop",
        "FPTShop": "FPTShop",
        "FPT Shop": "FPTShop",
        "ebay": "ebay",
        "eBay": "ebay",
    }

    normalized: List[str] = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        normalized.append(mapping.get(s, mapping.get(s.lower(), s)))

    deduped: List[str] = []
    seen = set()
    for s in normalized:
        if s in seen:
            continue
        seen.add(s)
        deduped.append(s)
    return deduped


_STOPWORDS = {
    "chinh",
    "hãng",
    "hang",
    "new",
    "moi",
    "rẻ",
    "re",
    "giá",
    "gia",
    "sale",
    "km",
    "khuyen",
    "mai",
    "bh",
    "bao",
    "hanh",
    "fullbox",
    "like",
    "auth",
    "ship",
    "freeship",
    "free",
}


def name_tokens(name: str) -> List[str]:
    if not name:
        return []
    s = name.lower()
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    toks = [t for t in s.split(" ") if t and t not in _STOPWORDS]
    return toks[:40]


def jaccard(a: List[str], b: List[str]) -> float:
    sa = set(a)
    sb = set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def cluster_products(rows: List[dict[str, Any]], threshold: float = 0.55) -> List[List[dict[str, Any]]]:
    clusters: List[List[dict[str, Any]]] = []
    reps: List[List[str]] = []

    for row in rows:
        name = str(row.get("product_name", "") or "")
        toks = name_tokens(name)
        if not toks:
            clusters.append([row])
            reps.append([])
            continue

        placed = False
        for i, rep in enumerate(reps):
            if jaccard(toks, rep) >= threshold:
                clusters[i].append(row)
                placed = True
                break
        if not placed:
            clusters.append([row])
            reps.append(toks)

    clusters.sort(key=len, reverse=True)
    return clusters


def parse_iso_dt(val: Any) -> Optional[datetime.datetime]:
    if not val:
        return None
    if isinstance(val, datetime.datetime):
        return val
    try:
        return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


def best_voucher_for_offer(
    vouchers: List[dict[str, Any]],
    platform: str,
    price: Optional[float],
) -> Optional[dict[str, Any]]:
    if not vouchers or not platform or price is None:
        return None

    now = datetime.datetime.now(datetime.timezone.utc)
    best = None
    best_savings = 0.0

    for v in vouchers:
        if str(v.get("platform", "")).lower() != str(platform).lower():
            continue

        min_spend = v.get("min_spend")
        try:
            if min_spend is not None and float(min_spend) > float(price):
                continue
        except Exception:
            pass

        valid_until = parse_iso_dt(v.get("valid_until"))
        if valid_until and valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=datetime.timezone.utc)
        if valid_until and valid_until < now:
            continue

        savings = 0.0
        try:
            if v.get("discount_amount") is not None:
                savings += float(v.get("discount_amount") or 0.0)
            if v.get("discount_percentage") is not None:
                savings += float(price) * float(v.get("discount_percentage") or 0.0) / 100.0
        except Exception:
            savings = 0.0

        if savings > best_savings:
            best_savings = savings
            best = v

    return best


def compute_effective_price(
    price: Optional[float],
    discount_percent: Optional[float],
    voucher: Optional[dict[str, Any]],
) -> Optional[float]:
    if price is None:
        return None
    eff = float(price)
    if discount_percent:
        try:
            eff = eff * (1.0 - float(discount_percent) / 100.0)
        except Exception:
            pass
    if voucher:
        try:
            if voucher.get("discount_amount") is not None:
                eff -= float(voucher.get("discount_amount") or 0.0)
            if voucher.get("discount_percentage") is not None:
                eff -= float(price) * float(voucher.get("discount_percentage") or 0.0) / 100.0
        except Exception:
            pass
    return max(eff, 0.0)

