from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    
    # Document type: internal_case, template, external_law, case_law, memo, contract
    document_type = Column(String(50), nullable=False, index=True)
    
    # Jurisdiction: RU, EU, UK, US, CN, INTERNAL
    jurisdiction = Column(String(50), nullable=True, index=True)
    
    # Practice area: M&A, Litigation, Bankruptcy, Compliance, Corporate, Labor, IP, etc.
    practice_area = Column(String(100), nullable=True, index=True)
    
    # File storage
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)  # docx, pdf, txt
    
    # Full text content
    content = Column(Text, nullable=True)
    
    # Metadata
    doc_metadata = Column(JSON, nullable=True)
    
    # Indexing status: pending, processing, indexed, failed
    indexing_status = Column(String(50), default="pending")
    
    # User who uploaded
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    uploaded_by_user = relationship("User", back_populates="uploaded_documents")

    __table_args__ = (
        Index('idx_document_type_jurisdiction', 'document_type', 'jurisdiction'),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, type={self.document_type})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Text content of the chunk
    text = Column(Text, nullable=False)
    
    # Character positions in original document
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    
    # Vector embedding (1536 dimensions for OpenAI, adjust as needed)
    embedding = Column(Vector(1536), nullable=True)
    
    # Token count
    token_count = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index('idx_chunk_document', 'document_id', 'chunk_index'),
    )

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"

