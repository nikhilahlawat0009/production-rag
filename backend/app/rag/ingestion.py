"""
Document ingestion pipeline with incremental processing.

INCREMENTAL PROCESSING EXPLANATION:
- Hash each file (MD5) when ingested
- Store hash in database
- On re-run, skip files with matching hash
- Prevents re-embedding 1000 documents when only 5 are new

This is critical for production: you don't want to re-embed everything 
just because you added one new file.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.core.extractors import DocumentExtractor
from app.core.chunking import ChunkingStrategy

logger = logging.getLogger(__name__)


class IncrementalIngestionPipeline:
    """Ingest documents with smart incremental processing."""
    
    def __init__(self, data_dir: str, db_dir: str = "./chroma_db"):
        """
        Initialize ingestion pipeline.
        
        Args:
            data_dir: Directory containing documents
            db_dir: Directory for metadata storage
        """
        self.data_dir = Path(data_dir)
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(exist_ok=True)
        
        self.extractor = DocumentExtractor()
        self.chunker = ChunkingStrategy(chunk_size=512, chunk_overlap=50)
        self.metadata_file = self.db_dir / "ingestion_metadata.json"
        
        # Load existing metadata
        self.processed_files = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, str]:
        """Load existing file hashes from previous ingestions."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Persist processed file hashes."""
        with open(self.metadata_file, "w") as f:
            json.dump(self.processed_files, f, indent=2)
    
    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """Compute MD5 hash of file content."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def ingest(self, supported_extensions: List[str] = [".pdf", ".txt", ".csv"]) -> Dict:
        """
        Ingest all documents from data_dir.
        
        Returns:
            {
                "new_files": 3,
                "skipped_files": 2,
                "total_chunks": 45,
                "processing_time": 12.3
            }
        """
        start_time = datetime.now()
        
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return {"error": "Data directory not found"}
        
        # Find all documents
        all_files = []
        for ext in supported_extensions:
            all_files.extend(self.data_dir.rglob(f"*{ext}"))
        
        new_files = []
        skipped_files = []
        total_chunks = 0
        
        logger.info(f"Found {len(all_files)} documents")
        
        for file_path in all_files:
            file_path_str = str(file_path)
            file_hash = self._compute_file_hash(file_path_str)
            
            # Check if already processed
            if file_path_str in self.processed_files:
                if self.processed_files[file_path_str] == file_hash:
                    skipped_files.append(file_path_str)
                    logger.info(f"Skipping unchanged: {file_path.name}")
                    continue
            
            # Process new or modified file
            logger.info(f"Processing: {file_path.name}")
            text = self.extractor.extract(file_path_str)
            
            if text is None:
                logger.warning(f"Unsupported format: {file_path.name}")
                continue
            
            chunks = self.chunker.chunk(text)
            total_chunks += len(chunks)
            
            # Store chunks and metadata (to be saved to vector DB in next step)
            new_files.append({
                "file_path": file_path_str,
                "file_name": file_path.name,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "file_hash": file_hash,
                "ingestion_time": datetime.now().isoformat()
            })
            
            # Update metadata
            self.processed_files[file_path_str] = file_hash
        
        # Persist metadata
        self._save_metadata()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        result = {
            "new_files_processed": len(new_files),
            "skipped_files": len(skipped_files),
            "total_chunks_created": total_chunks,
            "processing_time_seconds": elapsed,
            "new_file_details": new_files
        }
        
        logger.info(f"Ingestion complete: {result}")
        return result
