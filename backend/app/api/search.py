"""
FastAPI endpoints for search functionality.

This exposes the hybrid retrieval system with:
- Query endpoint
- Metadata filtering
- Composable weights
- Score breakdown
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging

# Will be initialized in app startup
router = APIRouter(prefix="/api/v1/search", tags=["search"])
retriever = None

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Search request with optional configuration."""
    query: str
    top_k: Optional[int] = 5
    weights: Optional[Dict[str, float]] = {
        "bm25": 0.3,
        "semantic": 0.4,
        "rerank": 0.3
    }


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown for each result."""
    bm25: float
    semantic: float
    rerank: float
    final: float


class SearchResult(BaseModel):
    """Single search result with document and scores."""
    index: int
    document: str
    scores: ScoreBreakdown


class SearchResponse(BaseModel):
    """Full search response."""
    query: str
    results: List[SearchResult]
    count: int
    latency_ms: float


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Hybrid search endpoint.
    
    Query with any combination of:
    - Pure BM25: {"bm25": 1.0, "semantic": 0.0, "rerank": 0.0}
    - Pure Semantic: {"bm25": 0.0, "semantic": 1.0, "rerank": 0.0}
    - Hybrid: {"bm25": 0.5, "semantic": 0.5, "rerank": 0.0}
    - Hybrid + Rerank: {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}
    """
    if retriever is None:
        raise HTTPException(status_code=503, detail="Retriever not initialized")
    
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if request.top_k < 1 or request.top_k > 100:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 100")
    
    # Validate weights
    weights = request.weights or {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}
    total_weight = sum(weights.values())
    if total_weight < 0.99 or total_weight > 1.01:
        logger.warning(f"Weights sum to {total_weight}, should be 1.0")
    
    try:
        import time
        start = time.time()
        
        results = retriever.search(
            query=request.query,
            top_k=request.top_k,
            weights=weights
        )
        
        latency = (time.time() - start) * 1000  # ms
        
        # Format response
        formatted_results = [
            SearchResult(
                index=r["index"],
                document=r["document"],
                scores=ScoreBreakdown(**r["scores"])
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            count=len(formatted_results),
            latency_ms=latency
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def stats() -> Dict[str, Any]:
    """Get retriever statistics."""
    if retriever is None:
        return {"status": "not initialized"}
    
    return {
        "status": "ready",
        "documents_indexed": len(retriever.documents) if retriever.documents else 0,
        "embedding_model": "all-MiniLM-L6-v2",
        "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
    }


def init_retriever(ret):
    """Initialize the retriever instance (called from main.py)."""
    global retriever
    retriever = ret
