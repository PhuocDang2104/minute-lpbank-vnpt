"""
Action Item Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


class ActionItemBase(BaseModel):
    description: str
    deadline: Optional[date] = None
    priority: str = "medium"  # low / medium / high / critical
    status: str = "proposed"  # proposed / confirmed / in_progress / completed / cancelled
    source_text: Optional[str] = None
    external_task_link: Optional[str] = None


class ActionItemCreate(ActionItemBase):
    meeting_id: str
    owner_user_id: Optional[str] = None


class ActionItemUpdate(BaseModel):
    description: Optional[str] = None
    owner_user_id: Optional[str] = None
    deadline: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    external_task_link: Optional[str] = None
    external_task_id: Optional[str] = None


class ActionItemConfirm(BaseModel):
    confirmed_by: str


class ActionItemResponse(ActionItemBase):
    id: str
    meeting_id: str
    owner_user_id: Optional[str] = None
    owner_name: Optional[str] = None
    meeting_title: Optional[str] = None  # For list all items
    source_chunk_id: Optional[str] = None
    external_task_id: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActionItemList(BaseModel):
    items: List[ActionItemResponse]
    total: int


# ============================================
# Decision Item Schemas
# ============================================

class DecisionItemBase(BaseModel):
    description: str
    rationale: Optional[str] = None
    status: str = "proposed"  # proposed / confirmed / revised
    source_text: Optional[str] = None


class DecisionItemCreate(DecisionItemBase):
    meeting_id: str


class DecisionItemUpdate(BaseModel):
    description: Optional[str] = None
    rationale: Optional[str] = None
    status: Optional[str] = None


class DecisionItemConfirm(BaseModel):
    confirmed_by: str


class DecisionItemResponse(DecisionItemBase):
    id: str
    meeting_id: str
    source_chunk_id: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionItemList(BaseModel):
    items: List[DecisionItemResponse]
    total: int


# ============================================
# Risk Item Schemas
# ============================================

class RiskItemBase(BaseModel):
    description: str
    severity: str = "medium"  # low / medium / high / critical
    mitigation: Optional[str] = None
    status: str = "proposed"  # proposed / confirmed / mitigated / closed
    source_text: Optional[str] = None


class RiskItemCreate(RiskItemBase):
    meeting_id: str
    owner_user_id: Optional[str] = None


class RiskItemUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[str] = None
    mitigation: Optional[str] = None
    status: Optional[str] = None
    owner_user_id: Optional[str] = None


class RiskItemResponse(RiskItemBase):
    id: str
    meeting_id: str
    owner_user_id: Optional[str] = None
    owner_name: Optional[str] = None
    source_chunk_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RiskItemList(BaseModel):
    items: List[RiskItemResponse]
    total: int

