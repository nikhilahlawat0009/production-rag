"""
Hybrid search combining BM25, semantic search, and cross-encoder reranking.

HYBRID SEARCH EXPLAINED:

1. BM25 (Keyword search):
   - Fast, deterministic keyword matching
   - Good at: exact phrases, financial terms
   - Bad at: paraphrases, synonyms
   - Speed: ~1-5ms for 1000 docs

2. Semantic (Embeddings):
   - Captures meaning, handles synonyms
   - Good at: understanding intent, paraphrases
   - Bad at: domain-specific jargon, exact numbers
   - Speed: ~50-100ms (including embedding time)

3. Cross-Encoder (Reranking):
   - Fine-grained relevance scoring
   - Re-ranks top results from hybrid search
   - Speed: ~30-50ms for top-20 results

WEIGHTING STRATEGY:
- weights = {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}
- This is data-dependent. You'd test 3+ configs with real queries.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import logging

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid search with BM25 + Semantic + Reranking."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2",
                 rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize retriever with embedding and reranking models.
        
        Args:
            embedding_model: HuggingFace model for embeddings (fast, small)
            rerank_model: Cross-encoder for reranking (accurate, slower)
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.rerank_model = CrossEncoder(rerank_model)
        self.bm25 = None
        self.documents = []
        self.embeddings = None
        
        logger.info(f"Initialized embedder: {embedding_model}")
        logger.info(f"Initialized reranker: {rerank_model}")
    
    def index(self, documents: List[str]):
        """
        Index documents for search.
        
        Args:
            documents: List of document texts to index
        """
        logger.info(f"Indexing {len(documents)} documents...")
        
        self.documents = documents
        
        # BM25: tokenize and build index
        tokenized = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)
        
        # Semantic: encode all documents
        self.embeddings = self.embedding_model.encode(documents, convert_to_numpy=True)
        
        logger.info(f"✓ Indexing complete. Embeddings shape: {self.embeddings.shape}")
    
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
        Hybrid search with optional reranking.
        
        Args:
            query: Search query
            top_k: Number of results to return
            weights: {"bm25": w1, "semantic": w2, "rerank": w3}
                     Weights should sum to 1.0
        
        Returns:
            List of results with scores breakdown
        """
        if weights is None:
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
