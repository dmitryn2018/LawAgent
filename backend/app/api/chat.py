from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionListResponse,
    ChatMessageResponse, ChatCompletionRequest, ChatCompletionResponse,
    SourceReference
)
from app.services.chat_service import ChatService

router = APIRouter()


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's chat sessions."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return ChatSessionListResponse(
        items=sessions,
        total=len(sessions)
    )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title,
        jurisdiction=session_data.jurisdiction,
        mode=session_data.mode
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat session details."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get messages from a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()
    
    return messages


@router.post("/sessions/{session_id}/completions", response_model=ChatCompletionResponse)
async def create_completion(
    session_id: int,
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send message and get AI response."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session settings if provided
    if request.jurisdiction:
        session.jurisdiction = request.jurisdiction
    if request.mode:
        session.mode = request.mode
    
    # Generate response using chat service
    response = await ChatService.generate_response(
        session_id=session_id,
        message=request.message,
        jurisdiction=session.jurisdiction,
        mode=session.mode,
        db=db
    )
    
    return response

