import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path for absolute imports of src.ranking.bm25
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.ranking.bm25 import BM25Ranker
except ImportError as e:
    logger.error(f"Failed to import BM25Ranker: {e}")
    BM25Ranker = None

load_dotenv()

# Global variables for caching the search engine and DB client
search_engine = None
supabase_client: Client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan context manager:
    Executes BEFORE the server starts receiving requests.
    Loads BM25 inverted index & doc offsets globally to RAM.
    Initializes Supabase connection.
    """
    global search_engine, supabase_client
    
    logger.info("Starting up application lifespan...")
    
    # 1. Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        try:
            supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
    else:
        logger.warning("SUPABASE_URL or SUPABASE_KEY is missing. Database hydration will fail.")

    # 2. Load BM25 Engine
    # The default directory is expected to be ../index/ 
    # Adjust this path if the index is located elsewhere.
    index_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "index"))
    
    if BM25Ranker:
        try:
            logger.info(f"Loading BM25 Index from {index_dir} into RAM...")
            # We initialize the ranker once. It loads inverted_index.pkl, doc_offsets.pkl, etc.
            search_engine = BM25Ranker(index_dir=index_dir)
            logger.info("BM25 Index loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load BM25 engine from {index_dir}: {e}")
    else:
        logger.error("BM25Ranker module not available.")

    yield
    
    # Clean up (if any) when shutting down
    logger.info("Shutting down application lifespan. Clearing resources...")
    search_engine = None


app = FastAPI(
    title="Price Comparison Search API",
    description="High-performance backend bridging BM25 Search Engine with Supabase.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ProductResponse(BaseModel):
    id: int  # Matching the BM25 doc_id as requested
    platform: str
    product_id: str
    product_name: str
    price: float
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    product_url: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None

class SearchResponse(BaseModel):
    total_results: int
    page: int
    limit: int
    results: List[ProductResponse]


# --- Dummy Tokenizer for Pre-processing ---
def dummy_tokenize(query: str) -> str:
    """
    Dummy tokenizer logic. 
    To be replaced with the exact SPIMI/BM25 tokenization logic from you later.
    """
    return query.strip().lower()


# --- Routes ---
@app.get("/api/v1/search", response_model=SearchResponse)
async def search_endpoint(
    query: str = Query(..., min_length=1, description="Search query string"),
    min_price: Optional[int] = Query(None, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, description="Maximum price filter"),
    platforms: List[str] = Query(default=[], description="List of platforms to filter by"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Search workflow:
    1. Pre-processing: Tokenize query
    2. BM25 Scoring: Fetch top K doc_ids
    3. Db Hydration: Fetch records from Supabase
    4. Post-processing: Filter, sort by relevance, paginate
    """
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine is not initialized or failed to load.")
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")

    try:
        # 1. Pre-processing
        tokenized_query = dummy_tokenize(query)
        
        # 2. BM25 Scoring (RAM/Disk)
        # Fetch a reasonable K (e.g., 200) to allow for price & platform filtering drop-offs
        top_k = 200 
        bm25_results = search_engine.search(tokenized_query, top_k=top_k)
        
        if not bm25_results:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])
            
        # bm25_results is expected to be a list of tuples: (doc_id, score, text_snippet) based on your BM25 implementation
        top_doc_ids = [res[0] for res in bm25_results]
        
        # Store relevance map to easily restore the original order later
        relevance_map = {doc_id: idx for idx, doc_id in enumerate(top_doc_ids)}

        # 3. Database Hydration (Supabase)
        req = supabase_client.table("products").select("*").in_("id", top_doc_ids)
        
        if min_price is not None:
            req = req.gte("price", min_price)
        if max_price is not None:
            req = req.lte("price", max_price)
        if platforms:
            req = req.in_("platform", platforms)

        # Execute network call
        db_response = req.execute()
        products_data = db_response.data
        
        if not products_data:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])

        # 4. Post-processing & Pagination
        # The database returns rows out of order. Re-order them using relevance_map.
        # Fallback to float('inf') if doc_id somehow isn't found
        sorted_products = sorted(products_data, key=lambda p: relevance_map.get(p.get("id"), float('inf')))

        # Apply Pagination
        total_results = len(sorted_products)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_slice = sorted_products[start_idx:end_idx]

        return SearchResponse(
            total_results=total_results,
            page=page,
            limit=limit,
            results=paginated_slice
        )
        
    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during search processing.")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "search_engine_loaded": search_engine is not None,
        "database_connected": supabase_client is not None
    }
