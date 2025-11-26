from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=True)
    
    # Session settings
    jurisdiction = Column(String(50), nullable=True)  # RU, EU, UK, US, INTERNAL
    mode = Column(String(50), default="question")  # question, case_review, case_search
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title={self.title})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Message role: user, assistant, system
    role = Column(String(50), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    
    # Sources used for this message (for assistant messages)
    sources = Column(JSON, nullable=True)  # List of {document_id, chunk_id, title, snippet, relevance}
    
    # Token usage
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"

