"""
Hybrid search implementation - the core of the retrieval system.

The system balances BM25 keyword matching, semantic embeddings, and cross-encoder reranking.
Each method has distinct strengths and trade-offs:

BM25 (Keyword search):
- Effective for exact matches like "5.25%" or "FCA regulations"
- Fast (~1-5ms), deterministic, but misses paraphrases
- Strong for financial jargon and specific terms

Semantic Search (Embeddings):
- Handles intent and synonyms effectively
- Captures "interest rate policy" when searching "monetary policy"
- Challenges with domain-specific terms and exact numbers
- Takes ~50-100ms including embedding time

Cross-Encoder Reranking:
- Most accurate but slowest (~30-50ms for top-20 results)
- Applied only to top candidates for performance
- Significantly improves final result relevance

Default weighting: {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}
This configuration performed well for financial documents, though
different weightings should be tested with real user queries in production.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import logging

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid search engine combining three different retrieval approaches.

    The hybrid approach provides optimal performance across different query types.
    """

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2",
                 rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize search models.

        all-MiniLM-L6-v2 was selected for its balance of speed and quality.
        The cross-encoder is more accurate but slower, so I only use it for reranking.
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.rerank_model = CrossEncoder(rerank_model)
        self.bm25 = None
        self.documents = []
        self.embeddings = None

        logger.info(f"Loaded embedding model: {embedding_model}")
        logger.info(f"Loaded reranking model: {rerank_model}")

    def index(self, documents: List[str]):
        """
        Index documents for search.

        Builds three different indexes:
        1. BM25 for keyword search
        2. Embeddings for semantic search
        3. Original documents for reranking

        Performed once at startup for fast searches.
        """
        logger.info(f"Indexing {len(documents)} documents...")
        
        self.documents = documents
        
        # BM25 setup - simple tokenization
        tokenized = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)
        
        # Semantic embeddings - enables intelligent search
        self.embeddings = self.embedding_model.encode(documents, convert_to_numpy=True)
        
        logger.info(f"Indexing complete! Shape: {self.embeddings.shape}")

    def _bm25_search(self, query: str, top_k: int) -> np.ndarray:
        """
        BM25 keyword search.

        Returns: scores array of shape (len(documents),)
        """
        tokens = query.split()
        scores = self.bm25.get_scores(tokens)
        return scores

    def _semantic_search(self, query: str, top_k: int) -> np.ndarray:
        """
        Semantic search using embeddings.

        Returns: similarity scores array of shape (len(documents),)
        """
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0]

        # Cosine similarity: [-1, 1], scale to [0, 1]
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-8
        )

        # Map [-1, 1] to [0, 1]
        scores = (similarities + 1) / 2
        return scores

    def search(self, query: str, top_k: int = 5,
               weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Main search function combining all three approaches.

        Process:
        1. Get BM25 and semantic scores for ALL documents
        2. Combine with weights to get top candidates
        3. Rerank top candidates for improved accuracy

        Maintains speed while ensuring high quality results.
        """
        if weights is None:
            # Default weights - optimized for financial documents
            weights = {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}

        # Validate weights
        if abs(sum(weights.values()) - 1.0) > 0.01:
            logger.warning(f"Weights don't sum to 1.0: {sum(weights.values())}")

        # Stage 1: Hybrid search
        bm25_scores = self._bm25_search(query, top_k)
        semantic_scores = self._semantic_search(query, top_k)

        # Normalize scores to [0, 1]
        bm25_scores = bm25_scores / (np.max(bm25_scores) + 1e-8)
        semantic_scores = semantic_scores / (np.max(semantic_scores) + 1e-8)

        # Combined score (before reranking)
        combined_scores = (
            weights["bm25"] * bm25_scores +
            weights["semantic"] * semantic_scores
        )

        # Get top candidates for reranking
        top_candidates_idx = np.argsort(combined_scores)[-top_k * 3:][::-1]

        # Stage 2: Rerank top candidates
        rerank_scores = np.zeros(len(self.documents))
        
        if weights.get("rerank", 0) > 0:
            pairs = [(query, self.documents[idx]) for idx in top_candidates_idx]
            rerank_preds = self.rerank_model.predict(pairs)
            
            # Normalize rerank scores to [0, 1]
            rerank_preds = (rerank_preds - rerank_preds.min()) / (rerank_preds.max() - rerank_preds.min() + 1e-8)
            
            for i, idx in enumerate(top_candidates_idx):
                rerank_scores[idx] = rerank_preds[i]
        
        # Final scores
        final_scores = (
            weights["bm25"] * bm25_scores +
            weights["semantic"] * semantic_scores +
            weights.get("rerank", 0) * rerank_scores
        )
        
        # Get top-k results
        top_indices = np.argsort(final_scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "document": self.documents[idx],
                "index": int(idx),
                "scores": {
                    "bm25": float(bm25_scores[idx]),
                    "semantic": float(semantic_scores[idx]),
                    "rerank": float(rerank_scores[idx]),
                    "final": float(final_scores[idx])
                }
            })
        
        return results
