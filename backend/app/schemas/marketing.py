from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class MarketingLeadBase(BaseModel):
    email: EmailStr


class MarketingLeadCreate(MarketingLeadBase):
    pass


class MarketingLead(MarketingLeadBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BroadcastPitchMinutesRequest(BaseModel):
    token: Optional[str] = None


class BroadcastPitchMinutesResponse(BaseModel):
    total: int
    sent: int
    failed: List[EmailStr] = Field(default_factory=list)
