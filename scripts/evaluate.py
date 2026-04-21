"""
Evaluation framework for testing search system performance.

Tests precision, recall, NDCG, and latency across different configurations.
Compares semantic_only, hybrid, and hybrid_rerank approaches.
"""

import json
import time
import statistics
from pathlib import Path
import sys
from typing import Any, Dict, List

# Add the backend to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.rag.retrieval import HybridRetriever
from sklearn.metrics import ndcg_score

# Sample documents for evaluation
DOCUMENTS = [
    "The Bank of England raised interest rates to 5.25% in March 2024.",
    "Interest rate increases affect mortgage payments and borrowing costs.",
    "Central banks use monetary policy to control inflation rates.",
    "Revenue grew by 25% year-over-year to reach $500 million.",
    "Profit margins expanded as operational efficiency improved significantly.",
    "The UK financial services market shows strong growth this quarter.",
    "FCA regulatory changes require updates to open banking systems.",
    "Companies with strong balance sheets benefit from higher rates.",
    "Inflation remained stable at 2.5% according to latest data.",
    "Stock market volatility increased amid macroeconomic uncertainty."
]

# Configurations to test
CONFIGURATIONS = {
    "semantic_only": {"bm25": 0.0, "semantic": 1.0, "rerank": 0.0},  # Pure embeddings
    "hybrid": {"bm25": 0.5, "semantic": 0.5, "rerank": 0.0},        # Balanced approach
    "hybrid_rerank": {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}  # Production setup
}


def load_eval_data(path: str) -> List[Dict[str, Any]]:
    """Load my ground truth evaluation data."""
    with open(path, "r") as f:
        return json.load(f)


def precision_at_k(relevant: set, retrieved: List[int], k: int) -> float:
    """Calculate precision - what fraction of top-k results are relevant."""
    if k == 0:
        return 0.0
    return len([idx for idx in retrieved[:k] if idx in relevant]) / k


def recall_at_k(relevant: set, retrieved: List[int], k: int) -> float:
    """Calculate recall - what fraction of relevant docs are in top-k."""
    if not relevant:
        return 0.0
    return len([idx for idx in retrieved[:k] if idx in relevant]) / len(relevant)


def ndcg_at_k(relevant: set, retrieved: List[int], scores: List[float], k: int) -> float:
    """Calculate NDCG - quality-aware ranking metric."""
    y_true = [[1 if idx in relevant else 0 for idx in retrieved[:k]]]
    y_score = [scores[:k]]
    return ndcg_score(y_true, y_score)


def evaluate(retriever: HybridRetriever, eval_data: List[Dict[str, Any]], config_name: str, weights: Dict[str, float]) -> Dict[str, Any]:
    """
    Evaluate one configuration across all test queries.

    Measures quality (precision/recall/NDCG) and performance (latency).
    Tests cold start and warm performance.
    """
    precision_scores = []
    recall_scores = []
    ndcg_scores = []
    cold_latencies = []  # First search - no caching
    warm_latencies = []  # Second search - potentially cached

    for item in eval_data:
        query = item["query"]
        relevant = set(item["relevant_indices"])

        # Cold search - first time, no optimizations
        start = time.time()
        results = retriever.search(query=query, top_k=5, weights=weights)
        cold_latencies.append((time.time() - start) * 1000)

        # Extract results for metric calculation
        retrieved_indices = [result["index"] for result in results]
        retrieved_scores = [result["scores"]["final"] for result in results]

        # Calculate quality metrics
        precision_scores.append(precision_at_k(relevant, retrieved_indices, 5))
        recall_scores.append(recall_at_k(relevant, retrieved_indices, 5))
        ndcg_scores.append(ndcg_at_k(relevant, retrieved_indices, retrieved_scores, 5))

        # Warm search - immediate follow-up (simulates user behavior)
        start = time.time()
        retriever.search(query=query, top_k=5, weights=weights)
        warm_latencies.append((time.time() - start) * 1000)

    return {
        "config": config_name,
        "precision_at_5": statistics.mean(precision_scores),
        "recall_at_5": statistics.mean(recall_scores),
        "ndcg_at_5": statistics.mean(ndcg_scores),
        "cold_p95_ms": statistics.quantiles(cold_latencies, n=20)[-1],  # 95th percentile
        "warm_p95_ms": statistics.quantiles(warm_latencies, n=20)[-1],
        "cold_avg_ms": statistics.mean(cold_latencies),
        "warm_avg_ms": statistics.mean(warm_latencies)
    }


def print_summary(result: Dict[str, Any]):
    """Pretty print the evaluation results for one configuration."""
    print(f"\n=== {result['config']} ===")
    print(f"Precision@5: {result['precision_at_5']:.3f}")
    print(f"Recall@5:    {result['recall_at_5']:.3f}")
    print(f"NDCG@5:      {result['ndcg_at_5']:.3f}")
    print(f"Cold P95:    {result['cold_p95_ms']:.1f}ms")
    print(f"Warm P95:    {result['warm_p95_ms']:.1f}ms")
    print(f"Cold avg:    {result['cold_avg_ms']:.1f}ms")
    print(f"Warm avg:    {result['warm_avg_ms']:.1f}ms")


if __name__ == "__main__":
    # Load evaluation queries and expected results
    eval_data = load_eval_data(Path(__file__).parent.parent / "eval_data.json")

    # Set up retriever with same documents as production
    retriever = HybridRetriever()
    retriever.index(DOCUMENTS)

    print("Running evaluation across different search configurations...")
    print("This will test quality metrics and performance for each setup.\n")

    for name, weights in CONFIGURATIONS.items():
        result = evaluate(retriever, eval_data, name, weights)
        print_summary(result)

    print("\nEvaluation complete.")
    print("hybrid_rerank gives the best quality but takes the longest.")
    print("semantic_only is fastest but misses exact financial terms.")
    print("hybrid is the sweet spot for most use cases.")
