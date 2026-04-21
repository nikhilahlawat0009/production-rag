# Production-RAG Retrieval Platform

A production-grade retrieval system for financial documents.

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
   uv pip install -r backend/requirements.txt
   ```

## Run the API

```bash
cd /Users/sharmaishika/Documents/github/production-rag/backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## API

- POST `/api/v1/search/` - Search with query, weights, top_k
- GET `/api/v1/search/stats` - Retriever status
- GET `/health` - Health check

## Evaluation

Run the evaluation framework:

```bash
cd /Users/sharmaishika/Documents/github/production-rag
source .venv/bin/activate
python scripts/evaluate.py
```

The evaluation reports precision@5, recall@5, NDCG@5, and cold/warm latency for:
- `semantic_only`
- `hybrid`
- `hybrid_rerank`
