from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ClauseCreate(BaseModel):
    title: str
    body: str
    category: str
    tags: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    language: str = "ru"
    notes: Optional[str] = None


class ClauseUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    language: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ClauseResponse(BaseModel):
    id: int
    title: str
    body: str
    category: str
    tags: Optional[List[str]]
    jurisdiction: Optional[str]
    practice_area: Optional[str]
    language: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClauseListResponse(BaseModel):
    items: List[ClauseResponse]
    total: int
    page: int
    page_size: int

