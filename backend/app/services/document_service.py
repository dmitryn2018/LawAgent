import os
from typing import Optional
from loguru import logger


class DocumentService:
    """Service for document processing operations."""
    
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> Optional[str]:
        """Extract text content from a document file."""
        try:
            if file_type == "txt":
                return DocumentService._extract_txt(file_path)
            elif file_type == "docx":
                return DocumentService._extract_docx(file_path)
            elif file_type == "pdf":
                return DocumentService._extract_pdf(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return None
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    @staticmethod
    def _extract_txt(file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        from docx import Document
        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        return "\n\n".join(paragraphs)
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence ending within last 20% of chunk
                search_start = end - int(chunk_size * 0.2)
                best_break = end
                
                for sep in [". ", ".\n", "!\n", "?\n", "\n\n"]:
                    pos = text.rfind(sep, search_start, end)
                    if pos > search_start:
                        best_break = pos + len(sep)
                        break
                
                end = best_break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": min(end, text_length)
                })
            
            start = end - overlap if end < text_length else text_length
        
        return chunks

