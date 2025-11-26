from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from datetime import datetime

from app.core.database import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template category: nda, spa, employment, loan, service, etc.
    category = Column(String(100), nullable=True, index=True)
    
    # Jurisdiction
    jurisdiction = Column(String(50), nullable=True, index=True)
    
    # Path to DOCX template file
    file_path = Column(String(500), nullable=False)
    
    # JSON schema for form fields
    # Example: {
    #   "fields": [
    #     {"name": "party1", "type": "text", "label": "Party 1 Name", "required": true},
    #     {"name": "governing_law", "type": "select", "label": "Governing Law", "options": ["RU", "UK", "US"]},
    #     {"name": "include_arbitration", "type": "checkbox", "label": "Include arbitration clause"}
    #   ]
    # }
    form_schema = Column(JSON, nullable=False)
    
    # Optional sections that can be included/excluded
    # Example: ["arbitration_clause", "non_compete", "liquidated_damages"]
    optional_sections = Column(JSON, nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Template(id={self.id}, name={self.name}, category={self.category})>"

