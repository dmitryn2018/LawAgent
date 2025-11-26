from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class FormField(BaseModel):
    name: str
    type: str  # text, textarea, select, checkbox, date
    label: str
    required: bool = False
    default: Optional[Any] = None
    options: Optional[List[str]] = None  # For select fields
    placeholder: Optional[str] = None


class FormSchema(BaseModel):
    fields: List[FormField]


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    form_schema: dict
    optional_sections: Optional[List[str]] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    form_schema: Optional[dict] = None
    optional_sections: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    jurisdiction: Optional[str]
    form_schema: dict
    optional_sections: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    items: List[TemplateResponse]
    total: int


class TemplateRenderRequest(BaseModel):
    form_data: dict  # Key-value pairs matching form_schema fields
    include_sections: Optional[List[str]] = None  # Optional sections to include
    use_ai_generation: bool = False  # Whether to use LLM for descriptive parts


class TemplateRenderResponse(BaseModel):
    rendered_text: str
    file_id: Optional[str] = None  # ID for downloading DOCX
    download_url: Optional[str] = None

