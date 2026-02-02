"""
Meeting Participant Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ParticipantBase(BaseModel):
    role: str = "attendee"  # organizer / required / optional / attendee
    response_status: str = "pending"  # accepted / declined / tentative / pending


class ParticipantAdd(ParticipantBase):
    user_id: str


class ParticipantUpdate(BaseModel):
    role: Optional[str] = None
    response_status: Optional[str] = None
    attended: Optional[bool] = None


class ParticipantResponse(ParticipantBase):
    meeting_id: str
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None
    attended: bool = False
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParticipantList(BaseModel):
    participants: List[ParticipantResponse]
    total: int

