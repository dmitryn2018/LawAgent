from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.analysis import SavedAnalysis
from app.schemas.analysis import (
    DocumentAnalysisRequest, DocumentAnalysisResponse,
    ClauseSuggestionRequest, ClauseSuggestionResponse,
    ClientLetterRequest, ClientLetterResponse,
    SavedAnalysisCreate, SavedAnalysisResponse, ReviewerInfo
)
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze document text and return summary, risks, and recommendations."""
    if not request.text or len(request.text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="Document text must be at least 100 characters"
        )
    
    result = await AnalysisService.analyze_document(
        text=request.text,
        document_type=request.document_type,
        jurisdiction=request.jurisdiction,
        db=db
    )
    
    return result


@router.post("/client-letter", response_model=ClientLetterResponse)
async def generate_client_letter(
    request: ClientLetterRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Generate a client letter based on analysis results."""
    letter_text = await AnalysisService.generate_client_letter(
        summary=request.summary,
        risks=request.risks,
        deal_impact=request.deal_impact,
        language=request.language
    )
    
    return ClientLetterResponse(letter_text=letter_text)


@router.post("/suggest-clauses", response_model=ClauseSuggestionResponse)
async def suggest_clauses(
    request: ClauseSuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Suggest relevant clauses based on context."""
    result = await AnalysisService.suggest_clauses(
        context=request.context,
        category=request.category,
        jurisdiction=request.jurisdiction,
        practice_area=request.practice_area,
        db=db
    )
    
    return result


@router.post("/save", response_model=SavedAnalysisResponse)
async def save_analysis(
    request: SavedAnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save analysis results for later review."""
    # Check if analysis with same hash exists
    existing = db.query(SavedAnalysis).filter(
        SavedAnalysis.document_text_hash == request.document_text_hash
    ).first()
    
    if existing:
        # Update existing analysis
        existing.analysis_data = request.analysis_data
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        saved = existing
    else:
        # Create new saved analysis
        saved = SavedAnalysis(
            document_text_hash=request.document_text_hash,
            analysis_data=request.analysis_data,
            review_status="unreviewed"
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)
    
    return _format_saved_analysis_response(saved, db)


@router.get("/saved/{analysis_id}", response_model=SavedAnalysisResponse)
async def get_saved_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a saved analysis by ID."""
    saved = db.query(SavedAnalysis).filter(SavedAnalysis.id == analysis_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return _format_saved_analysis_response(saved, db)


@router.get("/saved/by-hash/{document_hash}", response_model=SavedAnalysisResponse)
async def get_saved_analysis_by_hash(
    document_hash: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a saved analysis by document text hash."""
    saved = db.query(SavedAnalysis).filter(
        SavedAnalysis.document_text_hash == document_hash
    ).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return _format_saved_analysis_response(saved, db)


@router.post("/saved/{analysis_id}/review", response_model=SavedAnalysisResponse)
async def mark_analysis_reviewed(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark an analysis as reviewed by the current user."""
    saved = db.query(SavedAnalysis).filter(SavedAnalysis.id == analysis_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    saved.review_status = "reviewed"
    saved.reviewed_by_id = current_user.id
    saved.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(saved)
    
    return _format_saved_analysis_response(saved, db)


def _format_saved_analysis_response(saved: SavedAnalysis, db: Session) -> SavedAnalysisResponse:
    """Format SavedAnalysis model to response schema."""
    reviewed_by = None
    if saved.reviewed_by_id:
        reviewer = db.query(User).filter(User.id == saved.reviewed_by_id).first()
        if reviewer:
            reviewed_by = ReviewerInfo(
                id=reviewer.id,
                full_name=reviewer.full_name,
                email=reviewer.email
            )
    
    return SavedAnalysisResponse(
        id=saved.id,
        document_text_hash=saved.document_text_hash,
        analysis_data=saved.analysis_data,
        review_status=saved.review_status,
        reviewed_by=reviewed_by,
        reviewed_at=saved.reviewed_at,
        created_at=saved.created_at,
        updated_at=saved.updated_at
    )

