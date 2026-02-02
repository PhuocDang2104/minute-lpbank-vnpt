from pydantic import BaseModel


class TranscriptEvent(BaseModel):
    speaker: str
    text: str
    timestamp: float


class ActionEvent(BaseModel):
    task: str
    owner: str
    due_date: str | None = None
    confidence: float | None = None