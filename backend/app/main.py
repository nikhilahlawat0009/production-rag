from fastapi import FastAPI
from app.rag.retrieval import HybridRetriever
from app.api import search as search_api
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Production-RAG API",
    version="1.0.0",
    description="Production-grade retrieval platform with hybrid search"
)

# Initialize retriever
retriever = HybridRetriever()

# Sample documents for demo
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
    """Initialize retriever on startup."""
    logger.info("Initializing retriever...")
    retriever.index(SAMPLE_DOCS)
    search_api.init_retriever(retriever)
    logger.info(f"✓ Indexed {len(SAMPLE_DOCS)} documents")

# Include search routes
app.include_router(search_api.router)

@app.get("/")
async def root():
    return {
        "message": "Production-RAG API",
        "docs": "/docs",
        "search_endpoint": "/api/v1/search"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}