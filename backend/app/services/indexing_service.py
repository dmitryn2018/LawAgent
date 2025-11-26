from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.document_service import DocumentService
from app.providers.embedding_provider import get_embedding_provider


class IndexingService:
    """Service for document indexing operations."""
    
    @staticmethod
    async def index_document(document_id: int):
        """Index a document by creating chunks and embeddings."""
        db = SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                return
            
            # Update status
            document.indexing_status = "processing"
            db.commit()
            
            # Get text content
            text = document.content
            if not text and document.file_path:
                text = DocumentService.extract_text(document.file_path, document.file_type)
                document.content = text
            
            if not text:
                document.indexing_status = "failed"
                db.commit()
                logger.error(f"No content to index for document {document_id}")
                return
            
            # Delete existing chunks
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            
            # Create chunks
            chunks = DocumentService.chunk_text(text)
            
            if not chunks:
                document.indexing_status = "indexed"
                db.commit()
                logger.info(f"Document {document_id} has no chunks to index")
                return
            
            # Get embedding provider
            embedding_provider = get_embedding_provider()
            
            # Generate embeddings in batch
            texts = [chunk["text"] for chunk in chunks]
            embeddings = await embedding_provider.embed_batch(texts)
            
            # Create chunk records
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    text=chunk["text"],
                    start_char=chunk["start_char"],
                    end_char=chunk["end_char"],
                    embedding=embedding,
                    token_count=len(chunk["text"]) // 4  # Rough estimate
                )
                db.add(db_chunk)
            
            document.indexing_status = "indexed"
            db.commit()
            
            logger.info(f"Successfully indexed document {document_id} with {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {e}")
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.indexing_status = "failed"
                    db.commit()
            except:
                pass
        finally:
            db.close()

