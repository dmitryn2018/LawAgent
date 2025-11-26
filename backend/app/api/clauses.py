from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_active_user, get_admin_user
from app.models.user import User
from app.models.clause import Clause
from app.schemas.clause import ClauseCreate, ClauseUpdate, ClauseResponse, ClauseListResponse

router = APIRouter()


@router.get("/", response_model=ClauseListResponse)
async def list_clauses(
    page: int = 1,
    page_size: int = 50,
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    practice_area: Optional[str] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List clauses with filtering."""
    query = db.query(Clause).filter(Clause.is_active == True)
    
    if category:
        query = query.filter(Clause.category == category)
    if jurisdiction:
        query = query.filter(Clause.jurisdiction == jurisdiction)
    if practice_area:
        query = query.filter(Clause.practice_area == practice_area)
    if language:
        query = query.filter(Clause.language == language)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Clause.title.ilike(search_term)) | (Clause.body.ilike(search_term))
        )
    
    total = query.count()
    clauses = query.order_by(Clause.category, Clause.title).offset((page - 1) * page_size).limit(page_size).all()
    
    return ClauseListResponse(
        items=clauses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List unique clause categories."""
    categories = db.query(Clause.category).distinct().all()
    return [c[0] for c in categories if c[0]]


@router.get("/{clause_id}", response_model=ClauseResponse)
async def get_clause(
    clause_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get clause details."""
    clause = db.query(Clause).filter(Clause.id == clause_id).first()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    return clause


@router.post("/", response_model=ClauseResponse)
async def create_clause(
    clause_data: ClauseCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new clause (admin only)."""
    clause = Clause(
        title=clause_data.title,
        body=clause_data.body,
        category=clause_data.category,
        tags=clause_data.tags,
        jurisdiction=clause_data.jurisdiction,
        practice_area=clause_data.practice_area,
        language=clause_data.language,
        notes=clause_data.notes
    )
    db.add(clause)
    db.commit()
    db.refresh(clause)
    return clause


@router.put("/{clause_id}", response_model=ClauseResponse)
async def update_clause(
    clause_id: int,
    clause_data: ClauseUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update clause (admin only)."""
    clause = db.query(Clause).filter(Clause.id == clause_id).first()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    update_data = clause_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clause, field, value)
    
    db.commit()
    db.refresh(clause)
    return clause


@router.delete("/{clause_id}")
async def delete_clause(
    clause_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete clause (admin only)."""
    clause = db.query(Clause).filter(Clause.id == clause_id).first()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    db.delete(clause)
    db.commit()
    return {"message": "Clause deleted"}

