"""
Document schemas for pre-read documents
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class DocumentBase(BaseModel):
    """Base document schema"""
    title: str
    file_type: str = Field(description="pdf, docx, xlsx, pptx, etc.")
    file_size: Optional[int] = None
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    visibility: Optional[str] = Field(default=None, description="project|meeting|private|share")
    tags: Optional[List[str]] = None
    storage_key: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Create document request (metadata)"""
    meeting_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    # For mock or manual upload
    file_url: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Update document request"""
    title: Optional[str] = None
    description: Optional[str] = None


class Document(DocumentBase):
    """Document response"""
    id: UUID
    meeting_id: UUID
    uploaded_by: Optional[UUID] = None
    file_url: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """List of documents response"""
    documents: List[Document]
    total: int


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    id: UUID
    title: str
    file_url: str
    storage_key: Optional[str] = None
    message: str = "Tài liệu đã được tải lên thành công"
