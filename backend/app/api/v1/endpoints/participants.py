"""
Meeting Participants API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.schemas.participant import (
    ParticipantAdd, ParticipantUpdate,
    ParticipantResponse, ParticipantList
)
from app.services import participant_service

router = APIRouter()


@router.get('/{meeting_id}', response_model=ParticipantList)
def list_participants(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """List all participants for a meeting"""
    return participant_service.list_participants(db, meeting_id)


@router.get('/{meeting_id}/user/{user_id}', response_model=ParticipantResponse)
def get_participant(
    meeting_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific participant"""
    participant = participant_service.get_participant(db, meeting_id, user_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@router.post('/{meeting_id}', response_model=ParticipantResponse)
def add_participant(
    meeting_id: str,
    data: ParticipantAdd,
    db: Session = Depends(get_db)
):
    """Add a participant to a meeting"""
    participant = participant_service.add_participant(db, meeting_id, data)
    if not participant:
        raise HTTPException(status_code=400, detail="Failed to add participant")
    return participant


@router.put('/{meeting_id}/user/{user_id}', response_model=ParticipantResponse)
def update_participant(
    meeting_id: str,
    user_id: str,
    data: ParticipantUpdate,
    db: Session = Depends(get_db)
):
    """Update a participant"""
    participant = participant_service.update_participant(db, meeting_id, user_id, data)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@router.delete('/{meeting_id}/user/{user_id}')
def remove_participant(
    meeting_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Remove a participant from a meeting"""
    removed = participant_service.remove_participant(db, meeting_id, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Participant not found")
    return {'status': 'removed'}


@router.post('/{meeting_id}/user/{user_id}/attendance', response_model=ParticipantResponse)
def mark_attendance(
    meeting_id: str,
    user_id: str,
    attended: bool = True,
    db: Session = Depends(get_db)
):
    """Mark attendance for a participant"""
    participant = participant_service.mark_attendance(
        db, meeting_id, user_id, attended,
        joined_at=datetime.utcnow() if attended else None
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@router.post('/{meeting_id}/user/{user_id}/join', response_model=ParticipantResponse)
def mark_join(
    meeting_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Mark participant as joined the meeting"""
    participant = participant_service.mark_attendance(
        db, meeting_id, user_id, 
        attended=True, 
        joined_at=datetime.utcnow()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@router.post('/{meeting_id}/user/{user_id}/leave', response_model=ParticipantResponse)
def mark_leave(
    meeting_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Mark participant as left the meeting"""
    participant = participant_service.mark_attendance(
        db, meeting_id, user_id,
        attended=True,
        left_at=datetime.utcnow()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant

