"""
Document ingestion utilities for PDFs, text files, and CSVs.

This module handles extracting text from different file formats.
Each format needs different handling:
- PDF: Page-by-page extraction
- Text: Direct read
- CSV: Convert to readable text format
"""

from pathlib import Path
from typing import Optional
import pandas as pd
from PyPDF2 import PdfReader


class DocumentExtractor:
    """Extract text from various file formats."""
    
    def extract(self, file_path: str) -> Optional[str]:
        """
        Extract text from file.
        
        Args:
            file_path: Path to document
            
        Returns:
            Extracted text or None if unsupported format
        """
        path = Path(file_path)
        
        if path.suffix.lower() == ".pdf":
            return self._extract_pdf(file_path)
        elif path.suffix.lower() == ".txt":
            return self._extract_text(file_path)
        elif path.suffix.lower() == ".csv":
            return self._extract_csv(file_path)
        else:
            return None
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """Extract text from PDF, page by page."""
        reader = PdfReader(file_path)
        text = ""
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            # Add metadata about which page
            text += f"\n[Page {page_num}]\n{page_text}\n"
        return text
    
    @staticmethod
    def _extract_text(file_path: str) -> str:
        """Extract text from plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    @staticmethod
    def _extract_csv(file_path: str) -> str:
        """Convert CSV to readable text format."""
        df = pd.read_csv(file_path)
        # Convert to string with readable formatting
        return df.to_string()
