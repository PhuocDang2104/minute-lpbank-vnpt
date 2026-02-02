from typing import Any, Dict, Optional

from pydantic import BaseModel


class GoMeetJoinUrlRequest(BaseModel):
    session_id: str
    audio_ingest_token: str
    meeting_secret_key: Optional[str] = None
    access_code: Optional[str] = None
    platform_meeting_ref: Optional[str] = None
    idempotency_key: Optional[str] = None


class GoMeetJoinUrlResponse(BaseModel):
    join_url: str
    full_join_url: str
    host_join_url: Optional[str] = None
    start_raw: Optional[Dict[str, Any]] = None
    join_raw: Optional[Dict[str, Any]] = None
