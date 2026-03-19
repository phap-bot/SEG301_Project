import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from . import deps
from .routers.compare_v1 import router as compare_v1_router
from .routers.health import router as health_router
from .routers.products_v1 import router as products_v1_router
from .routers.search_simple import router as search_simple_router
from .routers.search_v1 import router as search_v1_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:
    - init Supabase client
    - load BM25 + Vector indices into RAM
    """
    logger.info("Starting up application lifespan...")

    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    load_dotenv(env_path)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if supabase_url and supabase_key:
        try:
            deps.supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
    else:
        logger.warning("SUPABASE_URL or SUPABASE_KEY is missing. Database hydration will fail.")

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
    deps.supabase_client = None


app = FastAPI(
    title="Price Comparison Search API",
    description="High-performance backend bridging BM25 Search Engine with Supabase.",
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
