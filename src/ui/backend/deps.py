from __future__ import annotations

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Globals initialized by lifespan
search_engine = None
vector_engine = None
mongo_client: Optional[Any] = None
products_col: Optional[Any] = None
vouchers_col: Optional[Any] = None
search_logs_col: Optional[Any] = None
profile_user_info_col: Optional[Any] = None
user_tracking_col: Optional[Any] = None

try:
    # When running from `SEG301_Project/src` on sys.path, import path is `ranking.*`.
    from ranking.bm25 import BM25Ranker  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    try:
        # Fallback: when project root is on sys.path, import path can be `src.ranking.*`.
        from src.ranking.bm25 import BM25Ranker  # type: ignore  # noqa: F401
    except Exception as e:
        logger.error(f"Failed to import BM25Ranker: {e}")
        BM25Ranker = None  # type: ignore

try:
    from ranking.vector import VectorRanker  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    try:
        from src.ranking.vector import VectorRanker  # type: ignore  # noqa: F401
    except Exception as e:
        logger.error(f"Failed to import VectorRanker: {e}")
        VectorRanker = None  # type: ignore

try:
    from ranking.hybrid import HybridRanker  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    try:
        from src.ranking.hybrid import HybridRanker  # type: ignore  # noqa: F401
    except Exception as e:
        logger.error(f"Failed to import HybridRanker: {e}")
        HybridRanker = None  # type: ignore

