from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TextSpan(BaseModel):
    start_char: int
    end_char: int


class DocumentRisk(BaseModel):
    id: str
    title: str
    description: str
    severity: str  # low, medium, high
    spans: List[TextSpan]
    recommendation: Optional[str] = None
    impact_on_deal: Optional[str] = None  # deal_breaker, negotiable, cosmetic


class DealImpact(BaseModel):
    """Impact of document analysis on deal terms."""
    price: str  # Impact on price/valuation
    structure: str  # Impact on deal structure
    control: str  # Impact on control/governance


class DocumentAnalysisRequest(BaseModel):
    text: str
    document_type: Optional[str] = None
    jurisdiction: Optional[str] = None


class DocumentAnalysisResponse(BaseModel):
    summary: str
    risks: List[DocumentRisk]
    recommendations: List[str]
    key_terms: Optional[List[str]] = None
    parties: Optional[List[str]] = None
    overall_risk_level: str = "medium"  # low, medium, high
    deal_impact: Optional[DealImpact] = None


# Saved Analysis with Review Status
class SavedAnalysisCreate(BaseModel):
    document_text_hash: str
    analysis_data: dict


class ReviewerInfo(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: str


class SavedAnalysisResponse(BaseModel):
    id: int
    document_text_hash: str
    analysis_data: dict
    review_status: str  # unreviewed, reviewed
    reviewed_by: Optional[ReviewerInfo] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Client Letter Generation
class ClientLetterRequest(BaseModel):
    summary: str
    risks: List[dict]
    deal_impact: Optional[dict] = None
    language: str = "ru"  # ru, en


class ClientLetterResponse(BaseModel):
    letter_text: str


class ClauseSuggestionRequest(BaseModel):
    context: str  # Current text or cursor context
    category: Optional[str] = None  # Filter by category
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None


class SuggestedClause(BaseModel):
    id: int
    title: str
    body: str
    category: str
    relevance: float


class ClauseSuggestionResponse(BaseModel):
    suggestions: List[SuggestedClause]

