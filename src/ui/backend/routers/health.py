from __future__ import annotations

from fastapi import APIRouter

from .. import deps

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "search_engine_loaded": deps.search_engine is not None,
        "vector_engine_loaded": deps.vector_engine is not None,
        "database_connected": deps.supabase_client is not None,
    }

