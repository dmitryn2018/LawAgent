from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid

from app.core.database import get_db
from app.core.security import get_current_active_user, get_admin_user
from app.core.config import settings
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentDetailResponse,
    DocumentListResponse, SearchQuery, SearchResult, SearchResultItem
)
from app.services.document_service import DocumentService
from app.services.indexing_service import IndexingService

router = APIRouter()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    document_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    practice_area: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List documents with filtering."""
    query = db.query(Document)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if jurisdiction:
        query = query.filter(Document.jurisdiction == jurisdiction)
    if practice_area:
        query = query.filter(Document.practice_area == practice_area)
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return DocumentListResponse(
        items=documents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document details."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
    
    response = DocumentDetailResponse.model_validate(document)
    response.chunk_count = chunk_count
    return response


@router.post("/", response_model=DocumentResponse)
async def create_document(
    document_data: DocumentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new document (admin only)."""
    document = Document(
        title=document_data.title,
        document_type=document_data.document_type,
        jurisdiction=document_data.jurisdiction,
        practice_area=document_data.practice_area,
        content=document_data.content,
        doc_metadata=document_data.doc_metadata,
        uploaded_by=current_user.id,
        indexing_status="pending" if document_data.content else "indexed"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Index document in background if has content
    if document_data.content:
        background_tasks.add_task(IndexingService.index_document, document.id)
    
    return document


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    jurisdiction: Optional[str] = Form(None),
    practice_area: Optional[str] = Form(None),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Upload a document file (admin only)."""
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")
    
    # Save file
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(settings.storage_path, "documents", file_name)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Extract text content
    text_content = DocumentService.extract_text(file_path, file_ext)
    
    # Create document record
    document = Document(
        title=title,
        document_type=document_type,
        jurisdiction=jurisdiction,
        practice_area=practice_area,
        file_path=file_path,
        file_name=file.filename,
        file_type=file_ext,
        content=text_content,
        uploaded_by=current_user.id,
        indexing_status="pending"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Index document in background
    background_tasks.add_task(IndexingService.index_document, document.id)
    
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update document (admin only)."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = document_data.model_dump(exclude_unset=True)
    content_changed = "content" in update_data and update_data["content"] != document.content
    
    for field, value in update_data.items():
        setattr(document, field, value)
    
    if content_changed:
        document.indexing_status = "pending"
    
    db.commit()
    db.refresh(document)
    
    # Re-index if content changed
    if content_changed:
        background_tasks.add_task(IndexingService.index_document, document.id)
    
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete document (admin only)."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file if exists
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    db.delete(document)
    db.commit()
    return {"message": "Document deleted"}


@router.post("/{document_id}/reindex")
async def reindex_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Re-index document (admin only)."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.indexing_status = "pending"
    db.commit()
    
    background_tasks.add_task(IndexingService.index_document, document.id)
    
    return {"message": "Document queued for re-indexing"}


@router.post("/search", response_model=SearchResult)
async def search_documents(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Semantic search across documents."""
    from app.services.search_service import SearchService
    
    results = await SearchService.search(
        query=search_query.query,
        jurisdiction=search_query.jurisdiction,
        practice_area=search_query.practice_area,
        document_type=search_query.document_type,
        top_k=search_query.top_k,
        db=db
    )
    
    return SearchResult(
        query=search_query.query,
        results=results,
        total=len(results)
    )

