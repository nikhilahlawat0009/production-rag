"""
Test hybrid search with different configurations.

This demonstrates:
1. Why single-strategy search fails
2. How different strategies complement each other
3. When to use different weight configurations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.rag.retrieval import HybridRetriever
import time

# Sample financial documents
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
    "Stock market volatility increased amid macroeconomic uncertainty.",
]

# Test queries
QUERIES = [
    # Query 1: Exact phrase (BM25 should excel)
    {
        "query": "interest rates",
        "expectation": "BM25 should rank high (exact phrase match)"
    },
    # Query 2: Semantic paraphrase (Semantic should excel)
    {
        "query": "how do banks adjust borrowing costs",
        "expectation": "Semantic should rank high (meaning match, not exact words)"
    },
    # Query 3: Domain jargon (BM25 good, semantic helps)
    {
        "query": "FCA regulatory requirements",
        "expectation": "Both should work well (specific terms)"
    },
]


def test_retrieval():
    """Test hybrid retrieval with different configurations."""
    print("\n" + "="*80)
    print("STEP 3: Testing Hybrid Retrieval Pipeline")
    print("="*80)
    
    # Initialize retriever
    print("\n🔹 Initializing retriever...")
    retriever = HybridRetriever()
    
    # Index documents
    print(f"🔹 Indexing {len(DOCUMENTS)} documents...")
    start = time.time()
    retriever.index(DOCUMENTS)
    index_time = time.time() - start
    print(f"   ✓ Indexing took {index_time*1000:.1f}ms")
    
    # Test different weight configurations
    configs = {
        "BM25 Only (no semantic)": {"bm25": 1.0, "semantic": 0.0, "rerank": 0.0},
        "Semantic Only (no BM25)": {"bm25": 0.0, "semantic": 1.0, "rerank": 0.0},
        "Hybrid (BM25 + Semantic)": {"bm25": 0.5, "semantic": 0.5, "rerank": 0.0},
        "Hybrid + Rerank": {"bm25": 0.3, "semantic": 0.4, "rerank": 0.3},
    }
    
    for query_test in QUERIES:
        query = query_test["query"]
        expectation = query_test["expectation"]
        
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"Expectation: {expectation}")
        print(f"{'='*80}")
        
        for config_name, weights in configs.items():
            print(f"\n📊 {config_name}:")
            print(f"   Weights: BM25={weights['bm25']:.1f}, Semantic={weights['semantic']:.1f}, Rerank={weights['rerank']:.1f}")
            
            start = time.time()
            results = retriever.search(query, top_k=3, weights=weights)
            search_time = time.time() - start
            
            print(f"   Latency: {search_time*1000:.1f}ms\n")
            
            for i, result in enumerate(results, 1):
                doc = result["document"][:60] + "..." if len(result["document"]) > 60 else result["document"]
                final_score = result["scores"]["final"]
                
                print(f"   {i}. [{final_score:.3f}] {doc}")
                print(f"      BM25={result['scores']['bm25']:.3f}, " +
                      f"Semantic={result['scores']['semantic']:.3f}, " +
                      f"Rerank={result['scores']['rerank']:.3f}")


def analyze_strategy_differences():
    """Show when each strategy wins."""
    print("\n" + "="*80)
    print("ANALYSIS: When Does Each Strategy Win?")
    print("="*80)
    
    analysis = """
    
    🎯 BM25 (Keyword Search) Excels At:
    ├─ Exact phrase matches: "interest rates" finds "interest rates"
    ├─ Domain-specific jargon: "FCA", "EPS", "P/E ratio"
    ├─ Financial numbers: "5.25%", "$500M"
    └─ FAILURE MODE: Paraphrases. Query "how do banks adjust costs" won't match
                     "interest rate increases affect borrowing costs"
    
    🧠 Semantic (Embeddings) Excels At:
    ├─ Paraphrases: "how do banks adjust costs" matches "interest rate changes"
    ├─ Synonyms: "revenue growth" matches "sales increase"
    ├─ Conceptual similarity: "profit margin" understood in context of efficiency
    └─ FAILURE MODE: Domain jargon. "FCA" might not embed distinctly from generic
                     financial terms. Pure numbers (5.25%) lose meaning.
    
    ✨ Hybrid (BM25 + Semantic) Wins By:
    ├─ Combining both strengths
    ├─ BM25 catches exact terms, Semantic catches intent
    ├─ Redundancy: If one misses, the other might catch it
    └─ Tunable: Adjust weights based on your domain
    
    🎖️ Cross-Encoder Reranking Adds:
    ├─ Fine-grained relevance judgment
    ├─ Understands full context (not just word pairs)
    ├─ Expensive (~30-50ms) so only used for top-20 from first stage
    └─ Improves precision for high-stakes retrieval (legal, medical)
    
    📊 COST vs ACCURACY:
    - BM25 Only:          Fast (1-5ms), Lower precision
    - Semantic Only:      Medium (50-100ms), Good precision
    - Hybrid:             Medium (50-100ms), Better precision
    - Hybrid + Rerank:    Slower (80-150ms), Best precision
    
    💡 RECOMMENDATION:
    Start with Hybrid (0.5/0.5). Measure precision@5 on your data.
    If you need 99.9% accuracy (legal/financial): Add reranking.
    If you need <100ms latency: Use BM25 only or lower rerank threshold.
    """
    
    print(analysis)


if __name__ == "__main__":
    try:
        test_retrieval()
        analyze_strategy_differences()
        
        print("\n" + "="*80)
        print("✓ Retrieval tests complete!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
