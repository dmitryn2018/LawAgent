from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class DueDiligenceCheck(Base):
    __tablename__ = "due_diligence_checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Company being checked
    company_name = Column(String(500), nullable=False)
    
    # Check type: ma_dd (M&A Due Diligence), compliance (Compliance/Sanctions)
    check_type = Column(String(50), nullable=False, index=True)
    
    # Jurisdiction: RU, EU, UK
    jurisdiction = Column(String(50), nullable=False, index=True)
    
    # Status: pending, processing, completed, failed
    status = Column(String(50), default="pending", index=True)
    
    # Raw data collected from sources (JSON)
    # Example structure:
    # {
    #   "company_info": {...},
    #   "court_cases": [...],
    #   "debts": [...],
    #   "regions": [...],
    #   "sanctions_flags": [...],
    #   "beneficial_owners": [...]
    # }
    raw_data = Column(JSON, nullable=True)
    
    # AI-generated summary and analysis
    ai_summary = Column(Text, nullable=True)
    
    # Risk indicators
    # Example: {"overall": "medium", "legal": "high", "financial": "low", "regulatory": "medium"}
    risk_indicators = Column(JSON, nullable=True)
    
    # Detailed risk items
    # Example: [{"category": "legal", "severity": "high", "title": "...", "description": "..."}]
    risk_items = Column(JSON, nullable=True)
    
    # Error message if failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="dd_checks")

    def __repr__(self):
        return f"<DueDiligenceCheck(id={self.id}, company={self.company_name}, status={self.status})>"

