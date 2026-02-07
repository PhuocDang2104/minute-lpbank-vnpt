from pydantic import BaseModel, Field
from typing import Optional, Literal


LlmProvider = Literal["gemini", "groq"]


class LlmSettings(BaseModel):
    provider: LlmProvider
    model: str
    api_key_set: bool = False
    api_key_last4: Optional[str] = None


class LlmSettingsUpdate(BaseModel):
    provider: LlmProvider
    model: str
    api_key: Optional[str] = Field(default=None, min_length=1)
    clear_api_key: bool = False
