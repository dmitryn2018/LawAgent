from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.due_diligence import DueDiligenceCheck
from app.schemas.due_diligence import DDCheckCreate, DDCheckResponse, DDCheckListResponse
from app.services.dd_service import DueDiligenceService

router = APIRouter()


@router.get("/", response_model=DDCheckListResponse)
async def list_checks(
    page: int = 1,
    page_size: int = 20,
    check_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's due diligence checks."""
    query = db.query(DueDiligenceCheck).filter(
        DueDiligenceCheck.user_id == current_user.id
    )
    
    if check_type:
        query = query.filter(DueDiligenceCheck.check_type == check_type)
    if status:
        query = query.filter(DueDiligenceCheck.status == status)
    
    total = query.count()
    checks = query.order_by(DueDiligenceCheck.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return DDCheckListResponse(
        items=checks,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{check_id}", response_model=DDCheckResponse)
async def get_check(
    check_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get due diligence check details."""
    check = db.query(DueDiligenceCheck).filter(
        DueDiligenceCheck.id == check_id,
        DueDiligenceCheck.user_id == current_user.id
    ).first()
    
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    return check


@router.post("/", response_model=DDCheckResponse)
async def create_check(
    check_data: DDCheckCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new due diligence check."""
    # Validate check type
    valid_types = ["ma_dd", "compliance"]
    if check_data.check_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid check type. Must be one of: {valid_types}"
        )
    
    # Validate jurisdiction
    valid_jurisdictions = ["RU", "EU", "UK"]
    if check_data.jurisdiction not in valid_jurisdictions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid jurisdiction. Must be one of: {valid_jurisdictions}"
        )
    
    # Create check record
    check = DueDiligenceCheck(
        user_id=current_user.id,
        company_name=check_data.company_name,
        check_type=check_data.check_type,
        jurisdiction=check_data.jurisdiction,
        status="pending"
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    
    # Run check in background
    background_tasks.add_task(DueDiligenceService.run_check, check.id)
    
    return check


@router.delete("/{check_id}")
async def delete_check(
    check_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete due diligence check."""
    check = db.query(DueDiligenceCheck).filter(
        DueDiligenceCheck.id == check_id,
        DueDiligenceCheck.user_id == current_user.id
    ).first()
    
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    db.delete(check)
    db.commit()
    return {"message": "Check deleted"}

