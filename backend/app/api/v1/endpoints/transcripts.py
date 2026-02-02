"""
Transcript API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.schemas.transcript import (
    TranscriptChunkCreate, TranscriptChunkUpdate, TranscriptChunkBatchInput,
    TranscriptChunkResponse, TranscriptChunkList,
    LiveRecapSnapshot, LiveRecapRequest
)
from app.services import transcript_service
from app.llm.gemini_client import MeetingAIAssistant

router = APIRouter()


@router.get('/{meeting_id}', response_model=TranscriptChunkList)
def list_transcript_chunks(
    meeting_id: str,
    from_index: Optional[int] = None,
    to_index: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List transcript chunks for a meeting"""
    return transcript_service.list_transcript_chunks(
        db, meeting_id, from_index, to_index, limit
    )


@router.get('/{meeting_id}/full', response_model=dict)
def get_full_transcript(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get full transcript text for a meeting"""
    transcript = transcript_service.get_full_transcript(db, meeting_id)
    return {'meeting_id': meeting_id, 'transcript': transcript}


@router.post('/{meeting_id}/chunks', response_model=TranscriptChunkResponse)
def create_transcript_chunk(
    meeting_id: str,
    data: TranscriptChunkCreate,
    db: Session = Depends(get_db)
):
    """Create a new transcript chunk"""
    data.meeting_id = meeting_id
    return transcript_service.create_transcript_chunk(db, data)


@router.post('/{meeting_id}/chunks/batch', response_model=TranscriptChunkList)
def create_batch_chunks(
    meeting_id: str,
    chunks: List[TranscriptChunkBatchInput],
    db: Session = Depends(get_db)
):
    """Create multiple transcript chunks at once"""
    # Convert batch input to full TranscriptChunkCreate with meeting_id
    full_chunks = [
        TranscriptChunkCreate(
            meeting_id=meeting_id,
            chunk_index=c.chunk_index,
            start_time=c.start_time,
            end_time=c.end_time,
            speaker=c.speaker,
            text=c.text,
            confidence=c.confidence,
            language=c.language,
            speaker_user_id=c.speaker_user_id,
        )
        for c in chunks
    ]
    return transcript_service.create_batch_transcript_chunks(db, meeting_id, full_chunks)


@router.put('/chunks/{chunk_id}', response_model=TranscriptChunkResponse)
def update_transcript_chunk(
    chunk_id: str,
    data: TranscriptChunkUpdate,
    db: Session = Depends(get_db)
):
    """Update a transcript chunk"""
    chunk = transcript_service.update_transcript_chunk(db, chunk_id, data)
    if not chunk:
        raise HTTPException(status_code=404, detail="Transcript chunk not found")
    return chunk


@router.delete('/{meeting_id}')
def delete_transcript(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Delete all transcript chunks for a meeting"""
    count = transcript_service.delete_transcript_chunks(db, meeting_id)
    return {'status': 'deleted', 'count': count}


# ============================================
# Live Recap
# ============================================

@router.get('/{meeting_id}/recap', response_model=dict)
def get_live_recap(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get the latest live recap for a meeting"""
    recap = transcript_service.get_live_recap(db, meeting_id)
    if recap:
        return recap.model_dump()
    return {'meeting_id': meeting_id, 'summary': None, 'message': 'No recap available'}


@router.post('/{meeting_id}/recap/generate', response_model=dict)
async def generate_live_recap(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Generate a live recap using AI"""
    # Get transcript
    transcript = transcript_service.get_full_transcript(db, meeting_id)
    
    if not transcript:
        return {'meeting_id': meeting_id, 'summary': 'No transcript available', 'key_points': []}
    
    # Use AI to generate recap
    assistant = MeetingAIAssistant(meeting_id)
    result = await assistant.generate_summary(transcript)
    
    # Save recap
    recap = transcript_service.create_live_recap(
        db, meeting_id,
        summary=result.get('summary', ''),
        key_points=result.get('key_points', [])
    )
    
    return recap.model_dump()


# ============================================
# AI Extraction from Transcript
# ============================================

@router.post('/{meeting_id}/extract/actions', response_model=dict)
async def extract_actions_from_transcript(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Extract action items from transcript using AI"""
    transcript = transcript_service.get_full_transcript(db, meeting_id)
    
    if not transcript:
        return {'meeting_id': meeting_id, 'actions': [], 'message': 'No transcript available'}
    
    assistant = MeetingAIAssistant(meeting_id)
    result = await assistant.extract_action_items(transcript)
    
    return {'meeting_id': meeting_id, 'actions': result.get('actions', [])}


@router.post('/{meeting_id}/extract/decisions', response_model=dict)
async def extract_decisions_from_transcript(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Extract decisions from transcript using AI"""
    transcript = transcript_service.get_full_transcript(db, meeting_id)
    
    if not transcript:
        return {'meeting_id': meeting_id, 'decisions': [], 'message': 'No transcript available'}
    
    assistant = MeetingAIAssistant(meeting_id)
    result = await assistant.extract_decisions(transcript)
    
    return {'meeting_id': meeting_id, 'decisions': result.get('decisions', [])}


@router.post('/{meeting_id}/extract/risks', response_model=dict)
async def extract_risks_from_transcript(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Extract risks from transcript using AI"""
    transcript = transcript_service.get_full_transcript(db, meeting_id)
    
    if not transcript:
        return {'meeting_id': meeting_id, 'risks': [], 'message': 'No transcript available'}
    
    assistant = MeetingAIAssistant(meeting_id)
    result = await assistant.extract_risks(transcript)
    
    return {'meeting_id': meeting_id, 'risks': result.get('risks', [])}

