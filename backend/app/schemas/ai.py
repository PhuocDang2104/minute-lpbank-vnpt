from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ============================================
# AGENDA GENERATION
# ============================================

class AgendaItem(BaseModel):
    order: int
    title: str
    duration_minutes: int
    presenter: Optional[str] = None
    description: Optional[str] = None


class AgendaProposal(BaseModel):
    id: str
    meeting_id: str
    items: List[AgendaItem]
    status: str = 'draft'  # draft / approved
    generated_at: datetime
    approved_at: Optional[datetime] = None


class GenerateAgendaRequest(BaseModel):
    meeting_id: str
    context: Optional[str] = None  # Additional context for AI


class GenerateAgendaResponse(BaseModel):
    agenda: AgendaProposal
    confidence: float


# ============================================
# PRE-READ DOCUMENTS
# ============================================

class PrereadDocument(BaseModel):
    id: str
    meeting_id: str
    title: str
    source: str  # SharePoint / LOffice / Wiki / Upload
    url: str
    snippet: str
    relevance_score: float
    status: str = 'suggested'  # suggested / accepted / ignored
    created_at: Optional[datetime] = None


class PrereadDocumentList(BaseModel):
    documents: List[PrereadDocument]
    total: int


class SuggestDocumentsRequest(BaseModel):
    meeting_id: str
    keywords: Optional[List[str]] = None


# ============================================
# RAG Q&A
# ============================================

class Citation(BaseModel):
    title: str
    source: str
    page: Optional[int] = None
    snippet: str
    url: Optional[str] = None


class RAGQuery(BaseModel):
    query: str
    meeting_id: Optional[str] = None
    include_meeting_context: bool = True


class RAGResponse(BaseModel):
    id: str
    query: str
    answer: str
    citations: List[Citation]
    confidence: float
    created_at: datetime


class RAGHistory(BaseModel):
    queries: List[RAGResponse]
    total: int


# ============================================
# MEETING SUGGESTIONS (People, Documents)
# ============================================

class MeetingSuggestion(BaseModel):
    id: str
    meeting_id: str
    suggestion_type: str  # document / person
    title: str
    description: Optional[str] = None
    reference_url: Optional[str] = None
    score: float
    status: str = 'pending'  # pending / accepted / ignored
    reason: Optional[str] = None


class SuggestionList(BaseModel):
    suggestions: List[MeetingSuggestion]
    total: int

