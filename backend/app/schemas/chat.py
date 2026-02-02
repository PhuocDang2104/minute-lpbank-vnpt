from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    meeting_id: Optional[str] = None
    session_id: Optional[str] = None
    include_context: bool = True


class HomeAskRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    id: str
    message: str
    role: str = 'assistant'
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    created_at: datetime


class ChatSession(BaseModel):
    id: str
    meeting_id: Optional[str] = None
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


class ChatSessionList(BaseModel):
    sessions: List[ChatSession]
    total: int


# AI Generation requests
class GenerateAgendaRequest(BaseModel):
    meeting_id: str
    meeting_type: str
    context: Optional[str] = None


class ExtractItemsRequest(BaseModel):
    meeting_id: str
    transcript: str
    item_type: str  # 'actions' | 'decisions' | 'risks'


class GenerateSummaryRequest(BaseModel):
    meeting_id: str
    transcript: str


class AIGenerationResponse(BaseModel):
    id: str
    result: str
    confidence: float
    created_at: datetime
