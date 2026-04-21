"""
FastAPI search endpoints - the public interface to the retrieval system.

Exposes hybrid search with flexible configuration:
- Different weight combinations for BM25/semantic/reranking
- Configurable result counts
- Detailed score breakdowns for transparency
- Performance metrics

Designed to be both powerful for advanced users and simple for basic searches.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging

# Global retriever instance - initialized at startup
router = APIRouter(prefix="/api/v1/search", tags=["search"])
retriever = None

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Request model for search queries."""
    query: str
    top_k: Optional[int] = 5
    weights: Optional[Dict[str, float]] = {
        "bm25": 0.3,  # Tuned defaults for financial documents
        "semantic": 0.4,
        "rerank": 0.3
    }


class ScoreBreakdown(BaseModel):
    """Detailed scores for result transparency."""
    bm25: float      # Keyword matching score
    semantic: float  # Meaning similarity score
    rerank: float    # Reranking refinement score
    final: float     # Combined final score


class SearchResult(BaseModel):
    """Search result with document and scoring information."""
    index: int
    document: str
    scores: ScoreBreakdown


class SearchResponse(BaseModel):
    """What users get back from their search."""
    query: str
    results: List[SearchResult]
    count: int
    latency_ms: float
    query: str
    results: List[SearchResult]
    count: int
    latency_ms: float


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    My main search endpoint - handles all the different search configurations.

    Users can search with:
    - Pure BM25: {"bm25": 1.0, "semantic": 0.0, "rerank": 0.0} - fast, exact matches
    - Pure Semantic: {"bm25": 0.0, "semantic": 1.0, "rerank": 0.0} - smart, understands intent
    - Hybrid: {"bm25": 0.5, "semantic": 0.5, "rerank": 0.0} - balanced approach
    - Hybrid + Rerank: {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3} - my default, best quality
    """
    if retriever is None:
        raise HTTPException(status_code=503, detail="Search system not ready yet")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Please provide a search query")

    if request.top_k < 1 or request.top_k > 100:
        raise HTTPException(status_code=400, detail="Number of results must be between 1 and 100")

    # Use provided weights or my defaults
    weights = request.weights or {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}
    total_weight = sum(weights.values())
    if total_weight < 0.99 or total_weight > 1.01:
        logger.warning(f"Weights sum to {total_weight}, should be 1.0 - using anyway")

    try:
        import time
        start_time = time.time()

        # Do the actual search
        raw_results = retriever.search(
            query=request.query,
            top_k=request.top_k,
            weights=weights
        )

        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Format the results for the API response
        formatted_results = [
            SearchResult(
                index=result["index"],
                document=result["document"],
                scores=ScoreBreakdown(**result["scores"])
            )
            for result in raw_results
        ]

        return SearchResponse(
            query=request.query,
            results=formatted_results,
            count=len(formatted_results),
            latency_ms=search_time
        )

    except Exception as e:
        logger.error(f"Search failed for query '{request.query}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def stats() -> Dict[str, Any]:
    """Get information about my search system status."""
    if retriever is None:
        return {"status": "not ready", "message": "System still starting up"}

    return {
        "status": "ready",
        "documents_indexed": len(retriever.documents) if retriever.documents else 0,
        "embedding_model": "all-MiniLM-L6-v2",
        "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "search_methods": ["BM25", "Semantic", "Cross-Encoder Reranking"]
    }


def init_retriever(ret):
    """Connect my search API to the retriever (called during app startup)."""
    global retriever
    retriever = ret
    logger.info("🔗 Search API connected to retriever")
