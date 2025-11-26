from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class DocumentCreate(BaseModel):
    title: str
    document_type: str
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    content: Optional[str] = None
    doc_metadata: Optional[dict] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    document_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    content: Optional[str] = None
    doc_metadata: Optional[dict] = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    document_type: str
    jurisdiction: Optional[str]
    practice_area: Optional[str]
    file_name: Optional[str]
    file_type: Optional[str]
    indexing_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    content: Optional[str]
    doc_metadata: Optional[dict]
    chunk_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    text: str
    start_char: Optional[int]
    end_char: Optional[int]

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    document_type: Optional[str] = None
    top_k: int = 10


class SearchResultItem(BaseModel):
    document_id: int
    chunk_id: int
    document_title: str
    document_type: str
    jurisdiction: Optional[str]
    text: str
    relevance: float


class SearchResult(BaseModel):
    query: str
    results: List[SearchResultItem]
    total: int

