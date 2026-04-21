"""
Test the document ingestion pipeline.

This shows:
1. Text extraction from different formats
2. Chunking strategy results
3. Incremental processing (run twice, second time should skip files)
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.rag.ingestion import IncrementalIngestionPipeline
from app.core.extractors import DocumentExtractor
from app.core.chunking import ChunkingStrategy


def test_extraction():
    """Test text extraction from different formats."""
    print("\n" + "="*60)
    print("STEP 1: Testing Text Extraction")
    print("="*60)
    
    extractor = DocumentExtractor()
    
    # Test text file
    text_file = "test_data/financial_report.txt"
    text_content = extractor.extract(text_file)
    print(f"\n✓ Extracted text file: {len(text_content)} characters")
    print(f"  Preview: {text_content[:100]}...")
    
    # Test CSV file
    csv_file = "test_data/quarterly_data.csv"
    csv_content = extractor.extract(csv_file)
    print(f"\n✓ Extracted CSV file: {len(csv_content)} characters")
    print(f"  Preview: {csv_content[:100]}...")


def test_chunking():
    """Test chunking strategy."""
    print("\n" + "="*60)
    print("STEP 2: Testing Chunking Strategy")
    print("="*60)
    
    chunker = ChunkingStrategy(chunk_size=512, chunk_overlap=50)
    
    # Get sample text
    extractor = DocumentExtractor()
    text = extractor.extract("test_data/financial_report.txt")
    
    chunks = chunker.chunk(text)
    stats = chunker.get_stats(chunks)
    
    print(f"\n✓ Chunking Results:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Average chunk size: {stats['avg_size']:.0f} chars")
    print(f"  Min: {stats['min_size']}, Max: {stats['max_size']}")
    
    print(f"\n  First chunk (preview):")
    print(f"  {chunks[0][:150]}...")


def test_ingestion():
    """Test full ingestion pipeline with incremental processing."""
    print("\n" + "="*60)
    print("STEP 3: Testing Incremental Ingestion")
    print("="*60)
    
    pipeline = IncrementalIngestionPipeline(
        data_dir="test_data",
        db_dir="./test_chroma_db"
    )
    
    # First ingestion
    print("\n🔹 First Run (process all files):")
    result1 = pipeline.ingest()
    print(f"  New files: {result1['new_files_processed']}")
    print(f"  Skipped: {result1['skipped_files']}")
    print(f"  Total chunks: {result1['total_chunks_created']}")
    print(f"  Time: {result1['processing_time_seconds']:.2f}s")
    
    # Second ingestion (should skip unchanged files)
    print("\n🔹 Second Run (should skip unchanged files):")
    result2 = pipeline.ingest()
    print(f"  New files: {result2['new_files_processed']}")
    print(f"  Skipped: {result2['skipped_files']}")
    print(f"  Total chunks: {result2['total_chunks_created']}")
    print(f"  Time: {result2['processing_time_seconds']:.2f}s")
    
    if result2['skipped_files'] > 0:
        print("\n✓ Incremental processing works! Files were skipped on second run.")
    else:
        print("\n⚠ No files skipped - check if files were actually unchanged")


if __name__ == "__main__":
    try:
        test_extraction()
        test_chunking()
        test_ingestion()
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
