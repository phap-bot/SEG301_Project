import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import deps
from .routers.compare_v1 import router as compare_v1_router
from .routers.health import router as health_router
from .routers.products_v1 import router as products_v1_router
from .routers.search_simple import router as search_simple_router
from .routers.search_v1 import router as search_v1_router
from .routers.log_search_v1 import router as log_search_router
from .routers.profile_user_info_v1 import router as profile_user_info_router
from .routers.user_tracking_v1 import router as user_tracking_router
from .routers.auth_v1 import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:
    - init MongoDB client
    - load BM25 + Vector indices into RAM
    """
    logger.info("Starting up application lifespan...")

    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    load_dotenv(env_path)

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGODB_DB", "seg301")

    try:
        # Import lazily so the module still imports even if `pymongo` isn't installed yet.
        from pymongo import MongoClient  # type: ignore

        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")

        collection_products = os.getenv("COLLECTION_PRODUCTS", "products")
        deps.mongo_client = mongo_client
        deps.products_col = mongo_client[mongo_db][collection_products]
        deps.vouchers_col = mongo_client[mongo_db]["vouchers"]
        deps.search_logs_col = mongo_client[mongo_db]["search_logs"]
        deps.profile_user_info_col = mongo_client[mongo_db]["profile_user_info"]
        deps.user_tracking_col = mongo_client[mongo_db]["user_tracking"]

        logger.info("MongoDB connected successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB client: {e}")
        deps.mongo_client = None
        deps.products_col = None
        deps.vouchers_col = None
        deps.search_logs_col = None

    index_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "index"))

    if deps.BM25Ranker:
        try:
            logger.info(f"Loading BM25 Index from {index_dir} into RAM...")
            deps.search_engine = deps.BM25Ranker(index_dir=index_dir)
            logger.info("BM25 Index loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load BM25 engine from {index_dir}: {e}")
    else:
        logger.error("BM25Ranker module not available.")

    if deps.VectorRanker:
        try:
            logger.info(f"Loading Vector Index from {index_dir} into RAM...")
            deps.vector_engine = deps.VectorRanker(index_dir=index_dir)
            logger.info("Vector Index loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Vector engine from {index_dir}: {e}")
    else:
        logger.error("VectorRanker module not available.")

    yield

    logger.info("Shutting down application lifespan. Clearing resources...")
    deps.search_engine = None
    deps.vector_engine = None
    deps.mongo_client = None
    deps.products_col = None
    deps.vouchers_col = None
    deps.search_logs_col = None
    deps.profile_user_info_col = None
    deps.user_tracking_col = None


app = FastAPI(
    title="Price Comparison Search API",
    description="High-performance backend bridging BM25 Search Engine with MongoDB.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(search_simple_router)  # /api/search
app.include_router(search_v1_router)      # /api/v1/search
app.include_router(products_v1_router)    # /api/v1/products/{id}
app.include_router(compare_v1_router)     # /api/v1/compare
app.include_router(log_search_router)     # /api/v1/log_search
app.include_router(profile_user_info_router)  # /api/v1/profile_user_info/{user_id}
app.include_router(user_tracking_router)  # /api/v1/user/{user_id}
app.include_router(auth_router)           # /api/v1/auth
