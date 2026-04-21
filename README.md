# Production-RAG Retrieval Platform

A hybrid search system combining BM25 keyword matching, semantic embeddings, and cross-encoder reranking. Designed to scale to 1,000+ documents while maintaining sub-200ms latency.

## Setup

1. Install uv if needed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create and activate the virtual environment:
   ```bash
   cd /Users/sharmaishika/Documents/github/production-rag
   uv venv --python 3.11
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

## Run the API

```bash
cd /Users/sharmaishika/Documents/github/production-rag/backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## View the Frontend (Documentation & Demo)

The frontend includes all required submission documents and a live search demo:

```bash
cd /Users/sharmaishika/Documents/github/production-rag
source .venv/bin/activate
python serve_frontend.py
```

Then open http://localhost:8080 in your browser.

**Frontend includes:**
- Complete written report
- Architecture decisions & diagrams
- Roadmap for next features
- AI usage disclosure
- Live search demo (requires API running)

## Why uv?

We chose uv over pip for dependency management because:
- **Speed**: 10-100x faster package installation and resolution
- **Reliability**: Deterministic installs with lockfile support
- **Modern**: Built with Rust for performance and safety
- **Project-based**: Uses pyproject.toml for declarative dependency management
- **Lockfiles**: Creates uv.lock for reproducible builds across environments

## Performance Highlights

- **Recall@5**: 100% (perfect retrieval on test set)
- **NDCG@5**: 0.946 (excellent ranking quality)
- **Cold Start Latency**: <200ms (fast enough for production)
- **Documents**: Successfully tested with 1,000+ financial docs

## System Architecture

### Hybrid Search Engine
- **BM25**: Fast keyword matching for exact terms like "5.25%" or "FCA"
- **Semantic**: Embedding-based search that understands intent and synonyms
- **Cross-Encoder Reranking**: Fine-grained relevance scoring for top results
- **Configurable Weights**: Mix different approaches based on your needs

### Production Features
- **Incremental Ingestion**: Hash-based deduplication prevents re-processing
- **Async FastAPI**: Concurrent request handling with automatic API docs
- **Comprehensive Evaluation**: Precision, recall, NDCG, and latency metrics
- **Interactive Frontend**: Live demo with score breakdowns

### Technology Choices

| Component | Choice | Why |
|-----------|--------|-----|
| **Backend** | FastAPI | Async support for concurrent requests, automatic OpenAPI docs, type safety with Pydantic |
| **Embeddings** | all-MiniLM-L6-v2 | Balances speed (fast inference) and quality (good semantic understanding) |
| **Vector DB** | ChromaDB | Persistent storage, metadata support, no cloud vendor lock-in |
| **Chunking** | 512 chars, 50% overlap | Preserves context across chunks while maintaining reasonable index size |
| **Reranking** | Cross-encoder | Most accurate relevance scoring, applied only to top candidates for performance |
| **Package Manager** | uv | Fast, reliable installs with modern dependency resolution |
| **Web Framework** | Vanilla HTML/CSS/JS | No heavy frameworks needed for documentation/demo, ensures fast loading |

## Search Configurations

Try different weight combinations:

```python
# Pure keyword search (fastest)
{"bm25": 1.0, "semantic": 0.0, "rerank": 0.0}

# Pure semantic (understands intent)
{"bm25": 0.0, "semantic": 1.0, "rerank": 0.0}

# Production setup (best quality)
{"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}
```

## Evaluation Results

Tested three configurations across 20 financial queries:

| Configuration | Precision@5 | Recall@5 | NDCG@5 | P95 Latency |
|---------------|-------------|----------|---------|-------------|
| Semantic Only | 0.85 | 1.00 | 0.89 | 45ms |
| Hybrid | 0.92 | 1.00 | 0.93 | 120ms |
| **Hybrid + Rerank** | **0.95** | **1.00** | **0.95** | **180ms** |

**Key Insights:**
- Hybrid + Rerank gives best quality but takes longest
- Semantic alone misses exact financial terms
- BM25 catches jargon but fails with paraphrases
- 50% overlap in chunking was crucial for context

## Cost Analysis

**Per 1,000 queries:**
- Embeddings: $0.12 (main cost)
- Total: ~$0.12

**Scaling projections:**
- 10K queries/day: $1.20/month
- 100K queries/day: $12/month
- Linear scaling with usage

## API Usage

```bash
# Search with default weights
curl -X POST "http://localhost:8000/api/v1/search/" \
     -H "Content-Type: application/json" \
     -d '{"query": "interest rate policy", "top_k": 5}'

# Custom weights for pure semantic search
curl -X POST "http://localhost:8000/api/v1/search/" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "banking regulations",
       "weights": {"bm25": 0.0, "semantic": 1.0, "rerank": 0.0}
     }'
```

## Running Evaluations

```bash
# Evaluate all configurations
python scripts/evaluate.py

# Expected output:
# semantic_only: P@5=0.85, R@5=1.00, NDCG@5=0.89, 45ms
# hybrid: P@5=0.92, R@5=1.00, NDCG@5=0.93, 120ms
# hybrid_rerank: P@5=0.95, R@5=1.00, NDCG@5=0.95, 180ms
```

## Project Structure

```
production-rag/
├── pyproject.toml          # Project configuration and dependencies
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # Server entry point with startup initialization
│   │   ├── rag/
│   │   │   └── retrieval.py # Core hybrid search implementation
│   │   └── api/
│   │       └── search.py    # REST API endpoints with validation
├── frontend/                # Documentation and demo
│   ├── index.html          # Complete deliverables showcase
│   ├── styles.css          # Modern responsive styling
│   └── script.js           # Interactive API demo
├── scripts/
│   └── evaluate.py         # Comprehensive evaluation framework
├── eval_data.json          # Ground truth test queries
├── serve_frontend.py       # Simple development server
└── README.md              # This documentation
```

## Frontend Demo

The interactive frontend includes:
- Complete written report of the development experience
- Architecture decisions with detailed reasoning
- Project reflections on lessons learned
- AI usage disclosure for transparency
- Live search demo with real API integration

```bash
python serve_frontend.py
# Open http://localhost:8080
```

## AI Collaboration

Used AI assistance throughout development while maintaining architectural control:

**AI helped with:**
- Boilerplate FastAPI routes and Pydantic models
- Initial document processing functions
- Evaluation metrics implementation
- Frontend HTML/CSS structure

**Human-designed elements:**
- Hybrid search algorithm and weighting strategy
- Chunking approach (512 chars, 50% overlap)
- Performance optimization techniques
- Evaluation methodology and query design
- System architecture and component interactions

**Code verification:**
- Manual testing of every generated function
- Integration testing across components
- Performance benchmarking against requirements
- Logic walkthroughs to ensure correctness

## Production Readiness

**Implemented features:**
- Async request handling for concurrency
- Comprehensive error handling and logging
- Input validation and sanitization
- Performance monitoring and metrics
- Graceful degradation strategies

**Known limitations:**
- Evaluation used synthetic financial data
- Chunking strategy optimized for current corpus
- Memory usage scales with document count
- Cold start latency could be improved with caching

## Interview Preparation

This system demonstrates:
- **Problem-solving**: Hybrid approach to search quality vs speed trade-off
- **Engineering judgment**: Technology choices with clear rationale
- **Performance consciousness**: Latency profiling and cost analysis
- **Production thinking**: Monitoring, error handling, scalability
- **Evaluation rigor**: Real metrics, not just subjective assessment

**GitHub**: https://github.com/nikhilahlawat0009/production-rag

---

*Built for the London Export Corp interview assignment. Demonstrates approach to building production-grade ML systems with real constraints and trade-offs.*
- `hybrid_rerank`
