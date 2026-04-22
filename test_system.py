#!/usr/bin/env python3
"""
Quick system validation - tests that core components work.

Run this to verify everything is set up correctly before submission.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_imports():
    """Test that all critical imports work."""
    print("Testing imports...")
    try:
        from app.rag.retrieval import HybridRetriever
        from app.api import search
        from app.main import app
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_retriever():
    """Test that the retriever can index and search."""
    print("\nTesting retriever...")
    try:
        from app.rag.retrieval import HybridRetriever
        
        retriever = HybridRetriever()
        docs = [
            "Interest rates increased to 5.25%",
            "Revenue grew by 25% year-over-year",
            "FCA regulations changed"
        ]
        retriever.index(docs)
        
        results = retriever.search(
            query="interest rates",
            top_k=5,
            weights={"bm25": 0.3, "semantic": 0.4, "rerank": 0.3}
        )
        
        if len(results) > 0:
            print(f"  ✓ Retriever works - returned {len(results)} results")
            return True
        else:
            print("  ✗ Retriever returned no results")
            return False
    except Exception as e:
        print(f"  ✗ Retriever test failed: {e}")
        return False

def test_evaluation():
    """Test that the evaluation framework works."""
    print("\nTesting evaluation framework...")
    try:
        import json
        eval_data_path = Path(__file__).parent / "eval_data.json"
        with open(eval_data_path) as f:
            eval_data = json.load(f)
        
        if len(eval_data) >= 20:
            print(f"  ✓ Evaluation data loaded - {len(eval_data)} queries")
            return True
        else:
            print(f"  ✗ Only {len(eval_data)} evaluation queries (need 20+)")
            return False
    except Exception as e:
        print(f"  ✗ Evaluation test failed: {e}")
        return False

def test_readme():
    """Test that README has all required sections."""
    print("\nTesting documentation...")
    try:
        readme_path = Path(__file__).parent / "README.md"
        readme_content = readme_path.read_text()
        
        required_sections = [
            "What I'd Ship Next",
            "BM25 Crushes Semantic",
            "Chunk Size",
            "Cost Analysis",
            "AI Usage",
            "Production Readiness",
        ]
        
        missing = []
        for section in required_sections:
            if section not in readme_content:
                missing.append(section)
        
        if not missing:
            print(f"  ✓ README has all required sections")
            return True
        else:
            print(f"  ✗ Missing sections: {', '.join(missing)}")
            return False
    except Exception as e:
        print(f"  ✗ Documentation test failed: {e}")
        return False

def main():
    print("=" * 50)
    print("Production-RAG System Validation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_retriever,
        test_evaluation,
        test_readme,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(results):
        print("✓ System is ready for submission!")
        return 0
    else:
        print("✗ Some tests failed - please fix before submission")
        return 1

if __name__ == "__main__":
    sys.exit(main())
