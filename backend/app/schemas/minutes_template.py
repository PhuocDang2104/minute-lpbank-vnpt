"""
Minutes Template Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class TemplateField(BaseModel):
    """Template field structure"""
    id: str
    label: str
    type: str  # text, datetime, array, signature, etc.
    required: bool = False
    source: str  # meeting.title, meeting.participants, ai_generated
    structure: Optional[Dict[str, Any]] = None  # For array/object types


class TemplateSection(BaseModel):
    """Template section structure"""
    id: str
    title: str
    order: int
    required: bool = True
    fields: List[TemplateField]


class TemplateStructure(BaseModel):
    """Template structure"""
    sections: List[TemplateSection]
    formatting: Optional[Dict[str, Any]] = None


class MinutesTemplateBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    structure: Dict[str, Any]  # JSONB structure
    sample_data: Optional[Dict[str, Any]] = None
    meeting_types: Optional[List[str]] = None
    is_default: bool = False
    is_active: bool = True


class MinutesTemplateCreate(MinutesTemplateBase):
    created_by: Optional[str] = None


class MinutesTemplateUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    sample_data: Optional[Dict[str, Any]] = None
    meeting_types: Optional[List[str]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    updated_by: Optional[str] = None


class MinutesTemplateResponse(MinutesTemplateBase):
    id: str
    version: int
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    parent_template_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class MinutesTemplateList(BaseModel):
    templates: List[MinutesTemplateResponse]
    total: int


# Update GenerateMinutesRequest to include template_id
class GenerateMinutesRequestWithTemplate(BaseModel):
    meeting_id: str
    template_id: Optional[str] = None  # Template ID to use
    include_transcript: bool = True
    format: str = "markdown"  # markdown / html / text

