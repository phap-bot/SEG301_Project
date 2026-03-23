from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from .. import deps

router = APIRouter(prefix="/api/v1", tags=["profile_user_info"])


@router.get("/profile_user_info/{user_id}")
async def get_profile_user_info(user_id: str):
    """
    Read profile data from MongoDB collection `profile_user_info`.

    Since Supabase auth has been removed from the frontend, this endpoint is currently
    intended for manual testing / future wiring with your own auth.
    """
    if deps.mongo_client is None or deps.profile_user_info_col is None:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")

    try:
        doc: Optional[dict[str, Any]] = deps.profile_user_info_col.find_one(
            {"id": user_id},
            projection={"_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Profile not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load profile user info: {str(e)}")

