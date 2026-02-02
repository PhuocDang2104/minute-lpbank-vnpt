"""
Agenda schemas for meeting agendas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class AgendaItemBase(BaseModel):
    """Base agenda item schema"""
    order_index: int = Field(ge=0, description="Order of the item in agenda")
    title: str
    duration_minutes: Optional[int] = Field(default=15, ge=1)
    presenter_id: Optional[UUID] = None
    presenter_name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class AgendaItemCreate(AgendaItemBase):
    """Create agenda item request"""
    pass


class AgendaItemUpdate(BaseModel):
    """Update agenda item request"""
    order_index: Optional[int] = None
    title: Optional[str] = None
    duration_minutes: Optional[int] = None
    presenter_id: Optional[UUID] = None
    presenter_name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed


class AgendaItem(AgendaItemBase):
    """Agenda item response"""
    id: UUID
    meeting_id: UUID
    status: str = "pending"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgendaList(BaseModel):
    """List of agenda items response"""
    items: List[AgendaItem]
    total: int
    total_duration_minutes: int


class AgendaCreate(BaseModel):
    """Create full agenda request"""
    meeting_id: UUID
    items: List[AgendaItemCreate]


class AgendaGenerateRequest(BaseModel):
    """Request to generate agenda using AI"""
    meeting_id: UUID
    meeting_title: str
    meeting_type: Optional[str] = None
    meeting_description: Optional[str] = None
    duration_minutes: Optional[int] = 60
    participants: Optional[List[str]] = None
    context: Optional[str] = None  # Additional context for AI


class AgendaGenerateResponse(BaseModel):
    """Response from AI agenda generation"""
    items: List[AgendaItemCreate]
    total_duration_minutes: int
    ai_notes: Optional[str] = None
    is_saved: bool = False


class AgendaSaveRequest(BaseModel):
    """Request to save generated agenda"""
    meeting_id: UUID
    items: List[AgendaItemCreate]

