from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
import json

from app.core.database import get_db
from app.core.security import get_current_active_user, get_admin_user
from app.core.config import settings
from app.models.user import User
from app.models.template import Template
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse,
    TemplateRenderRequest, TemplateRenderResponse
)
from app.services.template_service import TemplateService

router = APIRouter()


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List available templates."""
    query = db.query(Template).filter(Template.is_active == True)
    
    if category:
        query = query.filter(Template.category == category)
    if jurisdiction:
        query = query.filter(Template.jurisdiction == jurisdiction)
    
    templates = query.order_by(Template.name).all()
    
    return TemplateListResponse(
        items=templates,
        total=len(templates)
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get template details."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new template (admin only)."""
    template = Template(
        name=template_data.name,
        description=template_data.description,
        category=template_data.category,
        jurisdiction=template_data.jurisdiction,
        file_path="",  # Will be set on upload
        form_schema=template_data.form_schema,
        optional_sections=template_data.optional_sections
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.post("/upload", response_model=TemplateResponse)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    jurisdiction: Optional[str] = Form(None),
    form_schema: str = Form(...),  # JSON string
    optional_sections: Optional[str] = Form(None),  # JSON string
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Upload a template file (admin only)."""
    # Validate file type
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    # Save file
    file_name = f"{uuid.uuid4()}.docx"
    file_path = os.path.join(settings.templates_path, file_name)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Parse form schema
    try:
        schema = json.loads(form_schema)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid form_schema JSON")
    
    # Parse optional sections
    sections = None
    if optional_sections:
        try:
            sections = json.loads(optional_sections)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid optional_sections JSON")
    
    # Create template record
    template = Template(
        name=name,
        description=description,
        category=category,
        jurisdiction=jurisdiction,
        file_path=file_path,
        form_schema=schema,
        optional_sections=sections
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update template (admin only)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete template (admin only)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Delete file if exists
    if template.file_path and os.path.exists(template.file_path):
        os.remove(template.file_path)
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}


@router.post("/{template_id}/render", response_model=TemplateRenderResponse)
async def render_template(
    template_id: int,
    request: TemplateRenderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Render a template with form data."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    result = await TemplateService.render_template(
        template=template,
        form_data=request.form_data,
        include_sections=request.include_sections,
        use_ai=request.use_ai_generation
    )
    
    return result


@router.get("/{template_id}/download/{file_id}")
async def download_rendered_document(
    template_id: int,
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download rendered DOCX document."""
    file_path = os.path.join(settings.storage_path, "rendered", f"{file_id}.docx")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=document_{file_id}.docx"}
    )

