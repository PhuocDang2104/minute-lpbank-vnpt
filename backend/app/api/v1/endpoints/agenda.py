"""
Agenda API endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agenda import (
    AgendaItem,
    AgendaItemCreate,
    AgendaItemUpdate,
    AgendaList,
    AgendaGenerateRequest,
    AgendaGenerateResponse,
    AgendaSaveRequest,
)
from app.services import agenda_service

router = APIRouter(tags=["agenda"])


@router.get("/meeting/{meeting_id}", response_model=AgendaList)
async def list_agenda_items(
    meeting_id: UUID,
    db: Session = Depends(get_db),
):
    """List all agenda items for a meeting"""
    return await agenda_service.list_agenda_items(db, meeting_id)


@router.get("/item/{item_id}", response_model=AgendaItem)
async def get_agenda_item(
    item_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single agenda item by ID"""
    item = await agenda_service.get_agenda_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agenda item not found",
        )
    return item


@router.post("/meeting/{meeting_id}/item", response_model=AgendaItem)
async def create_agenda_item(
    meeting_id: UUID,
    data: AgendaItemCreate,
    db: Session = Depends(get_db),
):
    """Create a new agenda item"""
    return await agenda_service.create_agenda_item(db, meeting_id, data)


@router.put("/item/{item_id}", response_model=AgendaItem)
async def update_agenda_item(
    item_id: UUID,
    data: AgendaItemUpdate,
    db: Session = Depends(get_db),
):
    """Update an agenda item"""
    item = await agenda_service.update_agenda_item(db, item_id, data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agenda item not found",
        )
    return item


@router.delete("/item/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agenda_item(
    item_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete an agenda item"""
    success = await agenda_service.delete_agenda_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agenda item not found",
        )
    return None


@router.post("/generate", response_model=AgendaGenerateResponse)
async def generate_agenda(
    request: AgendaGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate agenda using AI.
    
    Uses Gemini to create a smart agenda based on meeting details.
    Returns suggested agenda items that can be edited before saving.
    """
    return await agenda_service.generate_agenda_ai(db, request)


@router.post("/save", response_model=AgendaList)
async def save_agenda(
    data: AgendaSaveRequest,
    db: Session = Depends(get_db),
):
    """
    Save a complete agenda for a meeting.
    
    Replaces all existing agenda items with the new ones.
    Use this after generating/editing the agenda.
    """
    return await agenda_service.save_agenda(db, data)


@router.post("/meeting/{meeting_id}/reorder", response_model=AgendaList)
async def reorder_agenda(
    meeting_id: UUID,
    item_ids: list[UUID],
    db: Session = Depends(get_db),
):
    """
    Reorder agenda items.
    
    Accepts a list of item IDs in the new order.
    """
    # Get all items for this meeting
    current = await agenda_service.list_agenda_items(db, meeting_id)
    
    # Validate all IDs are present
    current_ids = {str(item.id) for item in current.items}
    provided_ids = {str(id) for id in item_ids}
    
    if current_ids != provided_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided item IDs don't match existing agenda items",
        )
    
    # Update order
    for new_index, item_id in enumerate(item_ids):
        await agenda_service.update_agenda_item(
            db, item_id, 
            AgendaItemUpdate(order_index=new_index)
        )
    
    return await agenda_service.list_agenda_items(db, meeting_id)

