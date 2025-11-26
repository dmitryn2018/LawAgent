from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index, Boolean
from datetime import datetime

from app.core.database import Base


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    
    # Clause title/name
    title = Column(String(255), nullable=False)
    
    # Full text of the clause
    body = Column(Text, nullable=False)
    
    # Category: arbitration, force_majeure, confidentiality, liability, termination, etc.
    category = Column(String(100), nullable=False, index=True)
    
    # Tags for search and filtering
    # Example: ["standard", "buyer_friendly", "seller_friendly", "aggressive", "balanced"]
    tags = Column(JSON, nullable=True)
    
    # Jurisdiction
    jurisdiction = Column(String(50), nullable=True, index=True)
    
    # Practice area: M&A, Corporate, Labor, IP, etc.
    practice_area = Column(String(100), nullable=True, index=True)
    
    # Language: ru, en
    language = Column(String(10), default="ru")
    
    # Description/notes about when to use this clause
    notes = Column(Text, nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_clause_category_jurisdiction', 'category', 'jurisdiction'),
    )

    def __repr__(self):
        return f"<Clause(id={self.id}, title={self.title}, category={self.category})>"

