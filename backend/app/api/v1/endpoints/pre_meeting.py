from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import ai_service
from app.schemas.ai import (
    GenerateAgendaRequest, GenerateAgendaResponse, AgendaItem,
    SuggestDocumentsRequest, PrereadDocumentList,
    SuggestionList
)
from typing import List

router = APIRouter()


@router.post('/agenda/generate', response_model=GenerateAgendaResponse)
def generate_agenda(
    request: GenerateAgendaRequest,
    db: Session = Depends(get_db)
):
    """Generate agenda using AI based on meeting context"""
    return ai_service.generate_agenda(db, request.meeting_id, request.context)


@router.post('/agenda/{meeting_id}/save')
def save_agenda(
    meeting_id: str,
    items: List[AgendaItem],
    db: Session = Depends(get_db)
):
    """Save/update agenda for a meeting"""
    return ai_service.save_agenda(db, meeting_id, items)


@router.post('/documents/suggest', response_model=PrereadDocumentList)
def suggest_documents(
    request: SuggestDocumentsRequest,
    db: Session = Depends(get_db)
):
    """Suggest pre-read documents using AI"""
    return ai_service.suggest_documents(db, request.meeting_id, request.keywords)


@router.get('/suggestions/{meeting_id}', response_model=SuggestionList)
def get_suggestions(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get AI suggestions (documents, people) for a meeting"""
    return ai_service.get_meeting_suggestions(db, meeting_id)
