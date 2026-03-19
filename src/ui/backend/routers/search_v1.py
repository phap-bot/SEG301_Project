from __future__ import annotations

import logging
from typing import Any, List, Optional, cast

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from .. import deps
from ..schemas import ProductResponse, SearchResponse
from ..services.search_utils import dummy_tokenize, normalize_platform_filter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


async def _log_search_query(
    client,
    query_text: str,
    bm25_res: list,
    vector_res: list,
    hybrid_res: list,
) -> None:
    if not client:
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
        }
        client.table("search_logs").insert(payload).execute()
    except Exception as e:
        logger.error(f"Error logging search query to Supabase: {repr(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_endpoint(
    background_tasks: BackgroundTasks,
    query: str = Query(..., min_length=1, description="Search query string"),
    min_price: Optional[int] = Query(None, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, description="Maximum price filter"),
    platforms: List[str] = Query(default=[], description="List of platforms to filter by"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search_type: str = Query("hybrid", description="Type of search: 'bm25', 'vector', or 'hybrid'"),
):
    if not deps.supabase_client:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")

    try:
        tokenized_query = dummy_tokenize(query)
        top_k = 200

        final_results = []
        bm25_res_for_log = []
        vec_res_for_log = []
        hybrid_res_for_log = []

        if search_type == "bm25":
            if not deps.search_engine:
                raise HTTPException(status_code=500, detail="BM25 Search engine is not initialized.")
            final_results = deps.search_engine.search(tokenized_query, top_k=top_k)
            bm25_res_for_log = final_results

        elif search_type == "vector":
            if not deps.vector_engine:
                raise HTTPException(status_code=500, detail="Vector Search engine is not initialized.")
            final_results = deps.vector_engine.search(query, top_k=top_k)
            vec_res_for_log = final_results

        elif search_type == "hybrid":
            if not deps.search_engine or not deps.vector_engine or not deps.HybridRanker:
                raise HTTPException(status_code=500, detail="Engines for Hybrid search not fully initialized.")

            bm25_res = deps.search_engine.search(tokenized_query, top_k=top_k)
            vec_res = deps.vector_engine.search(query, top_k=top_k)
            final_results = deps.HybridRanker.search(bm25_res, vec_res, top_k=top_k)

            bm25_res_for_log = bm25_res
            vec_res_for_log = vec_res
            hybrid_res_for_log = final_results
        else:
            raise HTTPException(status_code=400, detail=f"Invalid search_type: {search_type}")

        background_tasks.add_task(
            _log_search_query,
            client=deps.supabase_client,
            query_text=query,
            bm25_res=bm25_res_for_log,
            vector_res=vec_res_for_log,
            hybrid_res=hybrid_res_for_log,
        )

        if not final_results:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])

        top_doc_ids = [res[0] for res in final_results]
        relevance_map = {str(doc_id): idx for idx, doc_id in enumerate(top_doc_ids)}

        def to_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return val

        top_doc_ids_for_db = [to_int(doc_id) for doc_id in top_doc_ids]
        req = deps.supabase_client.table("products").select("*").in_("id", top_doc_ids_for_db)

        if min_price is not None:
            req = req.gte("price", min_price)
        if max_price is not None:
            req = req.lte("price", max_price)
        if platforms:
            normalized_platforms = normalize_platform_filter(platforms)
            req = req.in_("platform", normalized_platforms)

        db_response = req.execute()
        products_data = db_response.data
        if not products_data:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])

        product_rows: List[dict[str, Any]] = []
        for item in cast(List[Any], products_data):
            if isinstance(item, dict):
                product_rows.append(cast(dict[str, Any], item))

        if not product_rows:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])

        sorted_products = sorted(
            product_rows,
            key=lambda p: relevance_map.get(str(p.get("id", "")), float("inf")),
        )

        total_results = len(sorted_products)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_slice = sorted_products[start_idx:end_idx]

        typed_results: List[ProductResponse] = []
        for row in paginated_slice:
            try:
                typed_results.append(ProductResponse(**row))
            except Exception as e:
                logger.warning(f"Skipping invalid product row: {e}")

        return SearchResponse(
            total_results=total_results,
            page=page,
            limit=limit,
            results=typed_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

