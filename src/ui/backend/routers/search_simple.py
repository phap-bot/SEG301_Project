from __future__ import annotations

import logging
import time
from typing import Any, List, cast

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from .. import deps
from ..schemas import HybridSearchResponse, Product

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


async def _log_search_query(
    search_logs_col,
    query_text: str,
    bm25_res: list,
    vector_res: list,
    hybrid_res: list,
    user_id: str | None = None,
) -> None:
    if search_logs_col is None:
        return
    try:
        bm25_top10 = [str(item[0]) for item in bm25_res[:10]] if bm25_res else []
        vector_top10 = [str(item[0]) for item in vector_res[:10]] if vector_res else []
        hybrid_top10 = [str(item[0]) for item in hybrid_res[:10]] if hybrid_res else []
        payload = {
            "query_text": query_text,
            "bm25_top10": bm25_top10,
            "vector_top10": vector_top10,
            "hybrid_top10": hybrid_top10,
            "user_id": user_id,
            "created_at": time.time(),
        }
        search_logs_col.insert_one(payload)
    except Exception as e:
        logger.error(f"Error logging search query to MongoDB: {repr(e)}")


@router.get("/api/search", response_model=HybridSearchResponse)
async def hybrid_search_endpoint(
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="Search query string"),
    top_k: int = Query(20, ge=1, le=200, description="Number of results to return"),
    user_id: str = Query(None, description="Optional User ID for building profile"),
):
    start_time = time.perf_counter()

    if deps.mongo_client is None or deps.products_col is None:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")
    if not deps.search_engine:
        raise HTTPException(status_code=500, detail="BM25 Search engine is not initialized.")

    try:
        bm25_res = deps.search_engine.search(q, top_k=top_k)
        vec_res = []
        hybrid_res = []
        actual_search_type = "bm25"

        if deps.vector_engine and deps.HybridRanker:
            vec_res = deps.vector_engine.search(q, top_k=top_k)
            hybrid_res = deps.HybridRanker.search(bm25_res, vec_res, top_k=top_k)
            final_ranked = hybrid_res
            actual_search_type = "hybrid"
        else:
            logger.warning("Vector engine unavailable — falling back to BM25-only.")
            final_ranked = bm25_res

        background_tasks.add_task(
            _log_search_query,
            search_logs_col=deps.search_logs_col,
            query_text=q,
            bm25_res=bm25_res,
            vector_res=vec_res,
            hybrid_res=hybrid_res,
            user_id=user_id,
        )

        if not final_ranked:
            elapsed = (time.perf_counter() - start_time) * 1000
            return HybridSearchResponse(
                query=q,
                total=0,
                search_type=actual_search_type,
                processing_time_ms=round(elapsed, 2),
                results=[],
            )

        ranked_doc_ids = [res[0] for res in final_ranked]
        rank_map = {str(doc_id): rank for rank, doc_id in enumerate(ranked_doc_ids)}

        int_ids: List[Any] = []
        for did in ranked_doc_ids:
            try:
                int_ids.append(int(did))
            except (ValueError, TypeError):
                int_ids.append(did)

        cursor = deps.products_col.find({"id": {"$in": int_ids}}, projection={"_id": 0})
        product_rows: List[dict[str, Any]] = [cast(dict[str, Any], item) for item in cursor]

        sorted_products = sorted(
            product_rows,
            key=lambda p: rank_map.get(str(p.get("id", "")), float("inf")),
        )

        typed_results: List[Product] = []
        for row in sorted_products:
            try:
                typed_results.append(Product(**row))
            except Exception as e:
                logger.warning(f"Skipping invalid product row: {e}")

        elapsed = (time.perf_counter() - start_time) * 1000
        return HybridSearchResponse(
            query=q,
            total=len(typed_results),
            search_type=actual_search_type,
            processing_time_ms=round(elapsed, 2),
            results=typed_results,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/api/search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

