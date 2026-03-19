from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int  # Matching the BM25 doc_id as requested
    platform: str
    product_id: str
    product_name: str
    price: float
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    product_url: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class SearchResponse(BaseModel):
    total_results: int
    page: int
    limit: int
    results: List[ProductResponse]


class Product(BaseModel):
    """Lightweight product schema for the /api/search endpoint."""

    id: int
    product_name: str
    price: Optional[float] = None
    platform: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class HybridSearchResponse(BaseModel):
    """Response for the /api/search endpoint."""

    query: str
    total: int
    search_type: str  # 'hybrid' or 'bm25' (fallback)
    processing_time_ms: float
    results: List[Product]


class Voucher(BaseModel):
    platform: str
    code: str
    discount_amount: Optional[float] = None
    discount_percentage: Optional[float] = None
    min_spend: Optional[float] = None
    description: Optional[str] = None
    valid_until: Optional[str] = None  # ISO string if present


class Offer(BaseModel):
    platform: str
    product: ProductResponse
    base_price: Optional[float] = None
    discount_percent: Optional[float] = None
    voucher: Optional[Voucher] = None
    effective_price: Optional[float] = None
    score: float


class RecommendationGroup(BaseModel):
    group_key: str
    display_name: str
    best_overall: Optional[Offer] = None
    best_by_platform: List[Offer]


class CompareResponse(BaseModel):
    query: str
    groups: List[RecommendationGroup]

