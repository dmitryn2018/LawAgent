from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    jurisdiction: Optional[str] = None
    mode: str = "question"  # question, case_review, case_search


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    jurisdiction: Optional[str] = None
    mode: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    jurisdiction: Optional[str]
    mode: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    items: List[ChatSessionResponse]
    total: int


class SourceReference(BaseModel):
    document_id: int
    chunk_id: int
    title: str
    snippet: str
    relevance: float


class ChatMessageCreate(BaseModel):
    role: str
    content: str
    sources: Optional[List[SourceReference]] = None


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[List[dict]]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatCompletionRequest(BaseModel):
    message: str
    jurisdiction: Optional[str] = None
    mode: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    message: ChatMessageResponse
    sources: List[SourceReference]

