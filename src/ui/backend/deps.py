from __future__ import annotations

import logging
from typing import Optional

from supabase import Client

logger = logging.getLogger(__name__)

# Globals initialized by lifespan
search_engine = None
vector_engine = None
supabase_client: Optional[Client] = None

try:
    from src.ranking.bm25 import BM25Ranker  # noqa: F401
except Exception as e:  # pragma: no cover
    logger.error(f"Failed to import BM25Ranker: {e}")
    BM25Ranker = None  # type: ignore

try:
    from src.ranking.vector import VectorRanker  # noqa: F401
except Exception as e:  # pragma: no cover
    logger.error(f"Failed to import VectorRanker: {e}")
    VectorRanker = None  # type: ignore

try:
    from src.ranking.hybrid import HybridRanker  # noqa: F401
except Exception as e:  # pragma: no cover
    logger.error(f"Failed to import HybridRanker: {e}")
    HybridRanker = None  # type: ignore

