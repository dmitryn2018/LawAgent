from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class DDCheckCreate(BaseModel):
    company_name: str
    check_type: str  # ma_dd, compliance
    jurisdiction: str  # RU, EU, UK


class RiskItem(BaseModel):
    category: str  # legal, financial, regulatory, reputational
    severity: str  # low, medium, high
    title: str
    description: str
    impact_on_deal: Optional[str] = None  # deal_breaker, negotiable, cosmetic


class RiskIndicators(BaseModel):
    overall: str  # low, medium, high
    legal: str
    financial: str
    regulatory: str


class DDCheckResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    check_type: str
    jurisdiction: str
    status: str
    raw_data: Optional[dict]
    ai_summary: Optional[str]
    risk_indicators: Optional[dict]
    risk_items: Optional[List[dict]]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DDCheckListResponse(BaseModel):
    items: List[DDCheckResponse]
    total: int
    page: int
    page_size: int

