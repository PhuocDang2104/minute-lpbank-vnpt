from pydantic import BaseModel


class TranscriptEvent(BaseModel):
    meeting_id: str
    speaker: str
    text: str
    timestamp: float


class ActionEvent(BaseModel):
    meeting_id: str
    task: str
    owner: str
    due_date: str | None = None
    confidence: float | None = None