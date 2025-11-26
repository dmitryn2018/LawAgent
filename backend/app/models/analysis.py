from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class SavedAnalysis(Base):
    """Model for storing document analysis results with review status."""
    __tablename__ = "saved_analyses"

    id = Column(Integer, primary_key=True, index=True)
    
    # Hash of document text for deduplication/lookup
    document_text_hash = Column(String(64), index=True, nullable=False)
    
    # Full analysis data as JSON
    analysis_data = Column(JSON, nullable=False)
    
    # Review status
    review_status = Column(String(20), default="unreviewed")  # unreviewed, reviewed
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<SavedAnalysis(id={self.id}, hash={self.document_text_hash[:8]}..., status={self.review_status})>"
