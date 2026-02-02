"""
Transcript Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TranscriptChunkBase(BaseModel):
    chunk_index: int
    start_time: float
    end_time: float
    speaker: Optional[str] = None
    text: str
    confidence: float = 0.0
    language: str = "vi"


class TranscriptChunkCreate(TranscriptChunkBase):
    meeting_id: str
    speaker_user_id: Optional[str] = None


# Schema for batch input - meeting_id comes from URL path
class TranscriptChunkBatchInput(TranscriptChunkBase):
    speaker_user_id: Optional[str] = None



class TranscriptChunkUpdate(BaseModel):
    text: Optional[str] = None
    speaker: Optional[str] = None
    speaker_user_id: Optional[str] = None


class TranscriptChunkResponse(TranscriptChunkBase):
    id: str
    meeting_id: str
    speaker_user_id: Optional[str] = None
    speaker_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptChunkList(BaseModel):
    chunks: List[TranscriptChunkResponse]
    total: int


# ============================================
# Live Recap Schemas
# ============================================

class LiveRecapSnapshot(BaseModel):
    id: str
    meeting_id: str
    snapshot_time: datetime
    summary: str
    key_points: Optional[List[str]] = None
    created_at: datetime


class LiveRecapRequest(BaseModel):
    meeting_id: str
    from_chunk_index: Optional[int] = None
    to_chunk_index: Optional[int] = None

