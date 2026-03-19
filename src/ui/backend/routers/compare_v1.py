from __future__ import annotations

import logging
from typing import Any, List, cast

from fastapi import APIRouter, HTTPException, Query

from .. import deps
from ..schemas import (
    CompareResponse,
    Offer,
    ProductResponse,
    RecommendationGroup,
    Voucher,
)
from ..services.search_utils import (
    best_voucher_for_offer,
    cluster_products,
    compute_effective_price,
    dummy_tokenize,
    name_tokens,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["compare"])


@router.get("/compare", response_model=CompareResponse)
async def compare_endpoint(
    query: str = Query(..., min_length=1, description="Product query to compare across platforms"),
    search_type: str = Query("hybrid", description="bm25|vector|hybrid"),
    max_candidates: int = Query(100, ge=20, le=200, description="How many candidates to fetch before grouping"),
    max_groups: int = Query(5, ge=1, le=20, description="How many grouped recommendations to return"),
):
    if not deps.supabase_client:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")
    if not deps.search_engine:
        raise HTTPException(status_code=500, detail="BM25 Search engine is not initialized.")

    tokenized_query = dummy_tokenize(query)

    bm25_res: list = []
    vec_res: list = []
    final_ranked: list = []

    if search_type == "bm25":
        bm25_res = deps.search_engine.search(tokenized_query, top_k=max_candidates)
        final_ranked = bm25_res
    elif search_type == "vector":
        if not deps.vector_engine:
            raise HTTPException(status_code=500, detail="Vector Search engine is not initialized.")
        vec_res = deps.vector_engine.search(query, top_k=max_candidates)
        final_ranked = vec_res
    else:
        if deps.vector_engine and deps.HybridRanker:
            bm25_res = deps.search_engine.search(tokenized_query, top_k=max_candidates)
            vec_res = deps.vector_engine.search(query, top_k=max_candidates)
            final_ranked = deps.HybridRanker.search(bm25_res, vec_res, top_k=max_candidates)
        else:
            bm25_res = deps.search_engine.search(tokenized_query, top_k=max_candidates)
            final_ranked = bm25_res

    if not final_ranked:
        return CompareResponse(query=query, groups=[])

    ranked_doc_ids = [res[0] for res in final_ranked]
    rank_map = {str(doc_id): rank for rank, doc_id in enumerate(ranked_doc_ids)}

    int_ids: List[Any] = []
    for did in ranked_doc_ids:
        try:
            int_ids.append(int(did))
        except (ValueError, TypeError):
            int_ids.append(did)

    db_response = (
        deps.supabase_client.table("products").select("*").in_("id", int_ids).execute()
    )
    products_data = db_response.data or []

    product_rows: List[dict[str, Any]] = []
    for item in cast(List[Any], products_data):
        if isinstance(item, dict):
            product_rows.append(cast(dict[str, Any], item))

    if not product_rows:
        return CompareResponse(query=query, groups=[])

    product_rows.sort(key=lambda p: rank_map.get(str(p.get("id", "")), float("inf")))

    vouchers: List[dict[str, Any]] = []
    try:
        v_res = deps.supabase_client.table("vouchers").select("*").execute()
        v_data = v_res.data or []
        for item in cast(List[Any], v_data):
            if isinstance(item, dict):
                vouchers.append(cast(dict[str, Any], item))
    except Exception:
        vouchers = []

    clusters = cluster_products(product_rows, threshold=0.55)[:max_groups]

    groups: List[RecommendationGroup] = []
    for cluster in clusters:
        typed_cluster: List[ProductResponse] = []
        for row in cluster:
            try:
                typed_cluster.append(ProductResponse(**row))
            except Exception:
                continue
        if not typed_cluster:
            continue

        typed_cluster.sort(key=lambda p: rank_map.get(str(p.id), float("inf")))
        display_name = typed_cluster[0].product_name
        group_key = " ".join(name_tokens(display_name)[:8]) or str(typed_cluster[0].id)

        offers: List[Offer] = []
        for p in typed_cluster:
            base_price = float(p.price) if p.price is not None else None
            discount_percent = float(p.discount_percent) if p.discount_percent is not None else None
            voucher_row = best_voucher_for_offer(vouchers, p.platform, base_price)
            eff = compute_effective_price(base_price, discount_percent, voucher_row)

            score = 0.0
            if eff is not None and eff > 0:
                score = 1_000_000.0 / eff
            if discount_percent:
                score += discount_percent * 0.01

            offers.append(
                Offer(
                    platform=p.platform,
                    product=p,
                    base_price=base_price,
                    discount_percent=discount_percent,
                    voucher=Voucher(**voucher_row) if voucher_row else None,
                    effective_price=eff,
                    score=score,
                )
            )

        if not offers:
            continue

        best_by_platform: List[Offer] = []
        by_plat: dict[str, List[Offer]] = {}
        for o in offers:
            by_plat.setdefault(o.platform, []).append(o)
        for plat, plat_offers in by_plat.items():
            plat_offers.sort(
                key=lambda x: (x.effective_price is None, x.effective_price or float("inf"), -x.score)
            )
            best_by_platform.append(plat_offers[0])

        best_by_platform.sort(
            key=lambda x: (x.effective_price is None, x.effective_price or float("inf"), -x.score)
        )
        best_overall = best_by_platform[0] if best_by_platform else None

        groups.append(
            RecommendationGroup(
                group_key=group_key,
                display_name=display_name,
                best_overall=best_overall,
                best_by_platform=best_by_platform,
            )
        )

    return CompareResponse(query=query, groups=groups)

