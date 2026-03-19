import os
import sys
import time
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Any, cast

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from src.ranking.bm25 import BM25Ranker
except ImportError as e:
    logger.error(f"Failed to import BM25Ranker: {e}")
    BM25Ranker = None

try:
    from src.ranking.vector import VectorRanker
except ImportError as e:
    logger.error(f"Failed to import VectorRanker: {e}")
    VectorRanker = None
    
try:
    from src.ranking.hybrid import HybridRanker
except ImportError as e:
    logger.error(f"Failed to import HybridRanker: {e}")
    HybridRanker = None

load_dotenv()

# Global variables for caching the search engine and DB client
search_engine = None
vector_engine = None
supabase_client: Optional[Client] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan context manager:
    Executes BEFORE the server starts receiving requests.
    Loads BM25 inverted index & doc offsets globally to RAM.
    Initializes Supabase connection.
    """
    global search_engine, vector_engine, supabase_client
    
    logger.info("Starting up application lifespan...")
    
    # 1. Initialize Supabase
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    load_dotenv(env_path)
    
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
    index_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "index"))
    
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

    if VectorRanker:
        try:
            logger.info(f"Loading Vector Index from {index_dir} into RAM...")
            vector_engine = VectorRanker(index_dir=index_dir)
            logger.info("Vector Index loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Vector engine from {index_dir}: {e}")
    else:
        logger.error("VectorRanker module not available.")

    yield
    
    # Clean up (if any) when shutting down
    logger.info("Shutting down application lifespan. Clearing resources...")
    search_engine = None
    vector_engine = None


app = FastAPI(
    title="Price Comparison Search API",
    description="High-performance backend bridging BM25 Search Engine with Supabase.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS config — allow React dev servers and any other origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default
        "http://localhost:3000",   # CRA / Next.js default
        "*",                       # Fallback for other origins
    ],
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

# --- New schemas for /api/search ---
class Product(BaseModel):
    """Lightweight product schema for the new search endpoint."""
    id: int
    product_name: str
    price: Optional[float] = None
    platform: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None

class HybridSearchResponse(BaseModel):
    """Response for the /api/search endpoint."""
    query: str
    total: int
    search_type: str           # 'hybrid' or 'bm25' (fallback)
    processing_time_ms: float  # End-to-end latency in milliseconds
    results: List[Product]


# --- Dummy Tokenizer for Pre-processing ---
def dummy_tokenize(query: str) -> str:
    """
    Dummy tokenizer logic. 
    To be replaced with the exact SPIMI/BM25 tokenization logic from you later.
    """
    return query.strip().lower()

def normalize_platform_filter(values: List[str]) -> List[str]:
    """
    Frontend uses human-friendly platform labels, while crawlers/DB often store canonical keys.
    Normalize incoming filter values so platform filtering matches DB values.
    """
    if not values:
        return []

    # Map display labels (and common variants) -> canonical DB keys
    mapping = {
        # UI labels
        "lazada": "lazada",
        "Lazada": "lazada",
        "cellphones": "cellphones",
        "CellphoneS": "cellphones",
        "tiki": "tiki",
        "Tiki": "tiki",
        "chotot": "Chotot",
        "Chotot": "Chotot",
        "Chợ Tốt": "Chotot",
        "dienmayxanh": "DienMayXanh",
        "DienMayXanh": "DienMayXanh",
        "Điện Máy Xanh": "DienMayXanh",
        "fptshop": "FPTShop",
        "FPTShop": "FPTShop",
        "FPT Shop": "FPTShop",
        "ebay": "ebay",
        "eBay": "ebay",
    }

    normalized: List[str] = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        normalized.append(mapping.get(s, mapping.get(s.lower(), s)))

    # Deduplicate while preserving order
    deduped: List[str] = []
    seen = set()
    for s in normalized:
        if s in seen:
            continue
        seen.add(s)
        deduped.append(s)
    return deduped


# --- Logging Workflow ---
async def log_search_query(
    client: Client, 
    query_text: str, 
    bm25_res: list, 
    vector_res: list, 
    hybrid_res: list
) -> None:
    """
    Trích xuất top 10 IDs từ các thuật toán và ghi log vào Supabase.
    """
    if not client:
        return
        
    try:
        bm25_top10 = [str(item[0]) for item in bm25_res[:10]] if bm25_res else []
        vector_top10 = [str(item[0]) for item in vector_res[:10]] if vector_res else []
        hybrid_top10 = [str(item[0]) for item in hybrid_res[:10]] if hybrid_res else []
        
        payload = {
            "query_text": query_text,
            "bm25_top10": bm25_top10,
            "vector_top10": vector_top10,
            "hybrid_top10": hybrid_top10
        }
        
        client.table("search_logs").insert(payload).execute()
    except Exception as e:
        logger.error(f"Error logging search query to Supabase: {repr(e)}")


# --- Routes ---
@app.get("/api/v1/search", response_model=SearchResponse)
async def search_endpoint(
    background_tasks: BackgroundTasks,
    query: str = Query(..., min_length=1, description="Search query string"),
    min_price: Optional[int] = Query(None, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, description="Maximum price filter"),
    platforms: List[str] = Query(default=[], description="List of platforms to filter by"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search_type: str = Query("hybrid", description="Type of search: 'bm25', 'vector', or 'hybrid'")
):
    """
    Search workflow:
    1. Pre-processing: Tokenize query
    2. Scouting: Fetch top K doc_ids via chosen Search Type
    3. Db Hydration: Fetch records from Supabase
    4. Post-processing: Filter, sort by relevance, paginate
    """
    global search_engine, vector_engine
    
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")

    try:
        # Pre-processing
        tokenized_query = dummy_tokenize(query)
        top_k = 200 
        
        final_results = []
        
        # Stores for logging
        bm25_res_for_log = []
        vec_res_for_log = []
        hybrid_res_for_log = []

        # Dispatch based on search_type
        if search_type == "bm25":
            if not search_engine:
                raise HTTPException(status_code=500, detail="BM25 Search engine is not initialized.")
            final_results = search_engine.search(tokenized_query, top_k=top_k)
            bm25_res_for_log = final_results
            
        elif search_type == "vector":
            if not vector_engine:
                raise HTTPException(status_code=500, detail="Vector Search engine is not initialized.")
            final_results = vector_engine.search(query, top_k=top_k)
            vec_res_for_log = final_results
            
        elif search_type == "hybrid":
            if not search_engine or not vector_engine or not HybridRanker:
                raise HTTPException(status_code=500, detail="Engines for Hybrid search not fully initialized.")
            
            # Run both
            bm25_res = search_engine.search(tokenized_query, top_k=top_k)
            vec_res = vector_engine.search(query, top_k=top_k)
            
            # Combine
            final_results = HybridRanker.search(bm25_res, vec_res, top_k=top_k)
            
            bm25_res_for_log = bm25_res
            vec_res_for_log = vec_res
            hybrid_res_for_log = final_results
        else:
            raise HTTPException(status_code=400, detail=f"Invalid search_type: {search_type}")

        # Add logging task to background
        background_tasks.add_task(
            log_search_query,
            client=supabase_client,
            query_text=query,
            bm25_res=bm25_res_for_log,
            vector_res=vec_res_for_log,
            hybrid_res=hybrid_res_for_log
        )

        if not final_results:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])
            
        # final_results is expected to be a list of tuples: (doc_id, score, text_snippet)
        top_doc_ids = [res[0] for res in final_results]
        
        # Store relevance map to easily restore the original order later
        relevance_map = {str(doc_id): idx for idx, doc_id in enumerate(top_doc_ids)}

        # 3. Database Hydration (Supabase)
        # BM25 returns string product_ids; Supabase "id" column is integer.
        # Convert to int where possible so the .in_() filter works correctly.
        def to_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return val
        top_doc_ids_for_db = [to_int(doc_id) for doc_id in top_doc_ids]
        req = supabase_client.table("products").select("*").in_("id", top_doc_ids_for_db)
        
        if min_price is not None:
            req = req.gte("price", min_price)
        if max_price is not None:
            req = req.lte("price", max_price)
        if platforms:
            normalized_platforms = normalize_platform_filter(platforms)
            req = req.in_("platform", normalized_platforms)

        # Execute network call
        db_response = req.execute()
        products_data = db_response.data
        
        if not products_data:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])

        # 4. Post-processing & Pagination
        # The database returns rows out of order. Re-order them using relevance_map.
        # Supabase client types this as generic JSON; normalize to dict rows for safer access.
        product_rows: List[dict[str, Any]] = []
        for item in cast(List[Any], products_data):
            if isinstance(item, dict):
                product_rows.append(cast(dict[str, Any], item))

        if not product_rows:
            return SearchResponse(total_results=0, page=page, limit=limit, results=[])

        # Ensure we stringify ID from DB for matching
        sorted_products = sorted(
            product_rows,
            key=lambda p: relevance_map.get(str(p.get("id", "")), float("inf")),
        )

        # Apply Pagination
        total_results = len(sorted_products)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_slice = sorted_products[start_idx:end_idx]

        # Convert raw DB rows -> response model for type safety (and FastAPI validation)
        typed_results: List[ProductResponse] = []
        for row in paginated_slice:
            try:
                typed_results.append(ProductResponse(**row))
            except Exception as e:
                logger.warning(f"Skipping invalid product row: {e}")

        return SearchResponse(
            total_results=total_results,
            page=page,
            limit=limit,
            results=typed_results
        )
        
    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/products/{product_id}", response_model=ProductResponse)
async def get_product_endpoint(product_id: int):
    """
    Fetch a single product's details from Supabase by its ID.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")
        
    try:
        req = supabase_client.table("products").select("*").eq("id", product_id).single()
        db_response = req.execute()
        
        if not db_response.data:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return db_response.data
    except Exception as e:
        logger.error(f"Get product endpoint error: {str(e)}", exc_info=True)
        if "JSON object requested, multiple (or no) rows returned" in str(e):
             raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(status_code=500, detail="Internal server error during fetch product.")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "search_engine_loaded": search_engine is not None,
        "vector_engine_loaded": vector_engine is not None,
        "database_connected": supabase_client is not None
    }


# =============================================================
# NEW ENDPOINT: /api/search — Hybrid Search (BM25 + Vector RRF)
# =============================================================
@app.get("/api/search", response_model=HybridSearchResponse)
async def hybrid_search_endpoint(
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="Search query string"),
    top_k: int = Query(20, ge=1, le=200, description="Number of results to return"),
):
    """
    Simplified search endpoint for the React frontend.
    1. Runs BM25 + Vector search, fuses with RRF (HybridRanker).
       Falls back to BM25-only if vector engine is unavailable.
    2. Fetches product metadata from Supabase.
    3. Re-sorts DB rows to preserve the ranking order.
    4. Logs query + top-10 IDs via BackgroundTasks (non-blocking).
    """
    start_time = time.perf_counter()
    global search_engine, vector_engine

    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database connection is not initialized.")
    if not search_engine:
        raise HTTPException(status_code=500, detail="BM25 Search engine is not initialized.")

    try:
        # --- Step 1: Run search algorithms ---
        bm25_res = search_engine.search(q, top_k=top_k)
        vec_res = []
        hybrid_res = []
        actual_search_type = "bm25"  # default / fallback

        if vector_engine and HybridRanker:
            # Vector engine is available → run full hybrid
            vec_res = vector_engine.search(q, top_k=top_k)
            hybrid_res = HybridRanker.search(bm25_res, vec_res, top_k=top_k)
            final_ranked = hybrid_res
            actual_search_type = "hybrid"
        else:
            # Fallback: BM25 only
            logger.warning("Vector engine unavailable — falling back to BM25-only.")
            final_ranked = bm25_res

        # --- Step 2: Log to Supabase (non-blocking via BackgroundTasks) ---
        background_tasks.add_task(
            log_search_query,
            client=supabase_client,
            query_text=q,
            bm25_res=bm25_res,
            vector_res=vec_res,
            hybrid_res=hybrid_res,
        )

        if not final_ranked:
            elapsed = (time.perf_counter() - start_time) * 1000
            return HybridSearchResponse(
                query=q, total=0, search_type=actual_search_type,
                processing_time_ms=round(elapsed, 2), results=[]
            )

        # --- Step 3: Supabase hydration ---
        # Extract ranked doc_ids (the first element of each result tuple)
        ranked_doc_ids = [res[0] for res in final_ranked]

        # Build a rank-order map:  { "doc_id_str" : rank_position }
        # This will be used AFTER the DB fetch to restore ranking order,
        # because Supabase .in_() does NOT guarantee any particular order.
        rank_map = {str(doc_id): rank for rank, doc_id in enumerate(ranked_doc_ids)}

        # Convert IDs to int for the Supabase .in_() filter (DB column is BIGINT)
        int_ids = []
        for did in ranked_doc_ids:
            try:
                int_ids.append(int(did))
            except (ValueError, TypeError):
                int_ids.append(did)

        db_response = (
            supabase_client
            .table("products")
            .select("*")
            .in_("id", int_ids)
            .execute()
        )
        products_data = db_response.data or []

        # --- Step 4: Re-sort to match the original ranking order ---
        # Supabase returns rows in arbitrary order; we use rank_map to
        # place each product back into its correct ranked position.
        product_rows: List[dict[str, Any]] = []
        for item in cast(List[Any], products_data):
            if isinstance(item, dict):
                product_rows.append(cast(dict[str, Any], item))

        sorted_products = sorted(
            product_rows,
            key=lambda p: rank_map.get(str(p.get("id", "")), float("inf")),
        )

        typed_results: List[Product] = []
        for row in sorted_products:
            try:
                typed_results.append(Product(**row))
            except Exception as e:
                logger.warning(f"Skipping invalid product row: {e}")

        elapsed = (time.perf_counter() - start_time) * 1000
        return HybridSearchResponse(
            query=q,
            total=len(typed_results),
            search_type=actual_search_type,
            processing_time_ms=round(elapsed, 2),
            results=typed_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/api/search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
