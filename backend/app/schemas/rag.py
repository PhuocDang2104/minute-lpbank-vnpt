from pydantic import BaseModel


class RagQuery(BaseModel):
    query: str
    meeting_id: str | None = None
    scopes: list[str] | None = None


class RagCitation(BaseModel):
    source: str
    snippet: str


class RagResponse(BaseModel):
    answer: str
    citations: list[RagCitation] = []