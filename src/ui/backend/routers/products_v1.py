from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import deps
from ..schemas import ProductResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["products"])


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_endpoint(product_id: int):
    if deps.mongo_client is None or deps.products_col is None:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")

    try:
        doc = deps.products_col.find_one({"id": product_id}, projection={"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product endpoint error: {str(e)}", exc_info=True)
        if "JSON object requested, multiple (or no) rows returned" in str(e):
            raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(status_code=500, detail="Internal server error during fetch product.")

