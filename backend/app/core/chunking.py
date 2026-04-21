"""
Intelligent text chunking strategy.

WHY THIS MATTERS:
- Too small chunks (256 chars): Loss of context, retrieval returns fragments
- Too large chunks (2000+ chars): Latency spikes, embedding becomes noisy
- 512 chars with 50% overlap: Sweet spot for financial documents

OVERLAP REASONING:
- No overlap: Semantic boundaries get split
- 50% overlap: Preserves context across chunk boundaries
- Example: "Company X revenue is $100M. Profit margin is 20%" 
  - Without overlap: First chunk misses profit info
  - With overlap: Both chunks have revenue + profit context
"""

from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter


class ChunkingStrategy:
    """Chunk documents with size=512, overlap=50."""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # RecursiveCharacterTextSplitter tries to split at sentence boundaries first
        # Falls back to smaller boundaries if needed
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",      # Paragraph breaks (best)
                "\n",        # Line breaks
                ". ",        # Sentence breaks
                " ",         # Word breaks
                ""           # Character breaks (last resort)
            ],
            length_function=len
        )
    
    def chunk(self, text: str) -> List[str]:
        """
        Chunk text into overlapping segments.
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or len(text) < 10:
            return []
        
        chunks = self.splitter.split_text(text)
        return chunks
    
    def get_stats(self, chunks: List[str]) -> dict:
        """Get chunking statistics for debugging."""
        if not chunks:
            return {"total_chunks": 0, "avg_size": 0, "min_size": 0, "max_size": 0}
        
        sizes = [len(chunk) for chunk in chunks]
        return {
            "total_chunks": len(chunks),
            "avg_size": sum(sizes) / len(sizes),
            "min_size": min(sizes),
            "max_size": max(sizes)
        }
