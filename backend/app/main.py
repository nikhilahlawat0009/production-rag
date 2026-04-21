"""
Production RAG API - FastAPI backend for hybrid search retrieval.

This is the main entry point for the retrieval system. FastAPI was chosen for
async support, automatic API documentation, and type safety with Pydantic.
The system indexes sample financial documents on startup and provides
search endpoints for the frontend.
"""

from fastapi import FastAPI
from app.rag.retrieval import HybridRetriever
from app.api import search as search_api
import logging

# Set up logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with project details
app = FastAPI(
    title="Production-RAG API",
    version="1.0.0",
    description="Production-grade retrieval platform with hybrid search"
)

# Initialize the retriever - handles all search logic
retriever = HybridRetriever()

# Sample financial documents for testing and demonstration
# These represent the type of content the system would search through
SAMPLE_DOCS = [
    "The Bank of England raised interest rates to 5.25% in March 2024.",
    "Interest rate increases affect mortgage payments and borrowing costs.",
    "Central banks use monetary policy to control inflation rates.",
    "Revenue grew by 25% year-over-year to reach $500 million.",
    "Profit margins expanded as operational efficiency improved significantly.",
    "The UK financial services market shows strong growth this quarter.",
    "FCA regulatory changes require updates to open banking systems.",
    "Companies with strong balance sheets benefit from higher rates.",
    "Inflation remained stable at 2.5% according to latest data.",
    "Stock market volatility increased amid macroeconomic uncertainty.",
]

@app.on_event("startup")
async def startup():
    """
    Initialize components when the server starts.

    Indexing is performed on startup to catch any issues immediately
    rather than during the first user search.
    """
    logger.info("Starting up retrieval system...")
    retriever.index(SAMPLE_DOCS)
    search_api.init_retriever(retriever)
    logger.info(f"Indexed {len(SAMPLE_DOCS)} documents - ready to search!")

# Wire up search API routes
app.include_router(search_api.router)

@app.get("/")
async def root():
    """
    Root endpoint providing API usage information.

    Useful for testing and API discovery.
    """
    return {
        "message": "Production-RAG API is running!",
        "docs": "/docs",  # FastAPI auto-generates this
        "search_endpoint": "/api/v1/search",
        "status": "Ready to search financial documents"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}