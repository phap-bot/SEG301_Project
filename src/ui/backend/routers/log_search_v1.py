from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, HTTPException, Query

from .. import deps

router = APIRouter(prefix="/api/v1", tags=["log_search"])


@router.get("/log_search")
async def list_search_logs(limit: int = Query(50, ge=1, le=500)):
    """
    Read-only endpoint to view latest search logs from MongoDB.
    """
    if deps.mongo_client is None or deps.search_logs_col is None:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")

    try:
        cursor = deps.search_logs_col.find(
            {},
            projection={"_id": 0},
        ).sort("_id", -1).limit(limit)
        logs: List[dict[str, Any]] = list(cursor)
        return {"total": len(logs), "logs": logs}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load search logs: {str(e)}")

