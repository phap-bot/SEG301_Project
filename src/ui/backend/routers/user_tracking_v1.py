from typing import Any
from fastapi import APIRouter, HTTPException, Body
from .. import deps
from ..schemas import Product, Voucher

router = APIRouter(prefix="/api/v1/user", tags=["user_tracking"])

@router.get("/{user_id}/tracking")
async def get_tracking(user_id: str):
    if deps.user_tracking_col is None:
        raise HTTPException(status_code=500, detail="Database not ready")
    
    doc = deps.user_tracking_col.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        return {"tracked_products": [], "saved_vouchers": []}
    
    return {
        "tracked_products": doc.get("tracked_products", []),
        "saved_vouchers": doc.get("saved_vouchers", [])
    }

@router.post("/{user_id}/tracked_products")
async def add_tracked_product(user_id: str, product: Product = Body(...)):
    if deps.user_tracking_col is None:
        raise HTTPException(status_code=500, detail="Database not ready")
    
    deps.user_tracking_col.update_one(
        {"user_id": user_id},
        {"$pull": {"tracked_products": {"id": product.id}}},
        upsert=True
    )
    deps.user_tracking_col.update_one(
        {"user_id": user_id},
        {"$push": {"tracked_products": product.model_dump()}}
    )
    return {"status": "ok"}

@router.delete("/{user_id}/tracked_products/{product_id}")
async def remove_tracked_product(user_id: str, product_id: int):
    if deps.user_tracking_col is None:
        raise HTTPException(status_code=500, detail="Database not ready")
        
    deps.user_tracking_col.update_one(
        {"user_id": user_id},
        {"$pull": {"tracked_products": {"id": product_id}}}
    )
    return {"status": "ok"}

@router.post("/{user_id}/saved_vouchers")
async def add_saved_voucher(user_id: str, voucher: Voucher = Body(...)):
    if deps.user_tracking_col is None:
        raise HTTPException(status_code=500, detail="Database not ready")
        
    deps.user_tracking_col.update_one(
        {"user_id": user_id},
        {"$pull": {"saved_vouchers": {"code": voucher.code}}},
        upsert=True
    )
    deps.user_tracking_col.update_one(
        {"user_id": user_id},
        {"$push": {"saved_vouchers": voucher.model_dump()}}
    )
    return {"status": "ok"}

@router.delete("/{user_id}/saved_vouchers/{voucher_code}")
async def remove_saved_voucher(user_id: str, voucher_code: str):
    if deps.user_tracking_col is None:
        raise HTTPException(status_code=500, detail="Database not ready")
        
    deps.user_tracking_col.update_one(
        {"user_id": user_id},
        {"$pull": {"saved_vouchers": {"code": voucher_code}}}
    )
    return {"status": "ok"}
