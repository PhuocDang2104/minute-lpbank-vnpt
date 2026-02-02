"""
Action Items, Decisions, Risks API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.action_item import (
    ActionItemCreate, ActionItemUpdate, ActionItemConfirm,
    ActionItemResponse, ActionItemList,
    DecisionItemCreate, DecisionItemUpdate, DecisionItemConfirm,
    DecisionItemResponse, DecisionItemList,
    RiskItemCreate, RiskItemUpdate,
    RiskItemResponse, RiskItemList,
)
from app.services import action_item_service

router = APIRouter()


# ============================================
# ACTION ITEMS
# ============================================

@router.get('/actions', response_model=ActionItemList)
def list_all_action_items(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    owner_user_id: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all action items with optional filters"""
    return action_item_service.list_all_action_items(
        db, 
        status=status,
        priority=priority,
        owner_user_id=owner_user_id,
        overdue_only=overdue_only
    )


@router.get('/actions/{meeting_id}', response_model=ActionItemList)
def list_action_items(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """List all action items for a meeting"""
    return action_item_service.list_action_items(db, meeting_id)


@router.get('/actions/item/{item_id}', response_model=ActionItemResponse)
def get_action_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """Get a single action item"""
    item = action_item_service.get_action_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


@router.post('/actions', response_model=ActionItemResponse)
def create_action_item(
    data: ActionItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new action item"""
    return action_item_service.create_action_item(db, data)


@router.put('/actions/{item_id}', response_model=ActionItemResponse)
def update_action_item(
    item_id: str,
    data: ActionItemUpdate,
    db: Session = Depends(get_db)
):
    """Update an action item"""
    item = action_item_service.update_action_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


@router.post('/actions/{item_id}/confirm', response_model=ActionItemResponse)
def confirm_action_item(
    item_id: str,
    data: ActionItemConfirm,
    db: Session = Depends(get_db)
):
    """Confirm an action item"""
    item = action_item_service.confirm_action_item(db, item_id, data.confirmed_by)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


@router.delete('/actions/{item_id}')
def delete_action_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """Delete an action item"""
    deleted = action_item_service.delete_action_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Action item not found")
    return {'status': 'deleted'}


# ============================================
# DECISIONS
# ============================================

@router.get('/decisions/{meeting_id}', response_model=DecisionItemList)
def list_decisions(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """List all decisions for a meeting"""
    return action_item_service.list_decision_items(db, meeting_id)


@router.post('/decisions', response_model=DecisionItemResponse)
def create_decision(
    data: DecisionItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new decision"""
    return action_item_service.create_decision_item(db, data)


@router.put('/decisions/{item_id}', response_model=DecisionItemResponse)
def update_decision(
    item_id: str,
    data: DecisionItemUpdate,
    db: Session = Depends(get_db)
):
    """Update a decision"""
    item = action_item_service.update_decision_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Decision not found")
    return item


@router.delete('/decisions/{item_id}')
def delete_decision(
    item_id: str,
    db: Session = Depends(get_db)
):
    """Delete a decision"""
    deleted = action_item_service.delete_decision_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {'status': 'deleted'}


# ============================================
# RISKS
# ============================================

@router.get('/risks/{meeting_id}', response_model=RiskItemList)
def list_risks(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """List all risks for a meeting"""
    return action_item_service.list_risk_items(db, meeting_id)


@router.post('/risks', response_model=RiskItemResponse)
def create_risk(
    data: RiskItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new risk"""
    return action_item_service.create_risk_item(db, data)


@router.put('/risks/{item_id}', response_model=RiskItemResponse)
def update_risk(
    item_id: str,
    data: RiskItemUpdate,
    db: Session = Depends(get_db)
):
    """Update a risk"""
    item = action_item_service.update_risk_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Risk not found")
    return item


@router.delete('/risks/{item_id}')
def delete_risk(
    item_id: str,
    db: Session = Depends(get_db)
):
    """Delete a risk"""
    deleted = action_item_service.delete_risk_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Risk not found")
    return {'status': 'deleted'}

