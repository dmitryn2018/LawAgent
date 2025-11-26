from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    LAWYER = "lawyer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default=UserRole.LAWYER.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    dd_checks = relationship("DueDiligenceCheck", back_populates="user", cascade="all, delete-orphan")
    uploaded_documents = relationship("Document", back_populates="uploaded_by_user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

