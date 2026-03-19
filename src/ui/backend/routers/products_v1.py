from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import deps
from ..schemas import ProductResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["products"])


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_endpoint(product_id: int):
    if not deps.supabase_client:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")

    try:
        req = deps.supabase_client.table("products").select("*").eq("id", product_id).single()
        db_response = req.execute()
        if not db_response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return db_response.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product endpoint error: {str(e)}", exc_info=True)
        if "JSON object requested, multiple (or no) rows returned" in str(e):
            raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(status_code=500, detail="Internal server error during fetch product.")

