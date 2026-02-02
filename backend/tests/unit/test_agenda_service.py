"""
Unit tests for agenda_service
"""
import pytest
from uuid import UUID
from datetime import datetime

from app.services import agenda_service
from app.schemas.agenda import AgendaItemCreate, AgendaGenerateRequest


@pytest.mark.asyncio
async def test_list_agenda_items(db_session):
    """Test listing agenda items for a meeting"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    
    result = await agenda_service.list_agenda_items(db_session, meeting_id)
    
    assert result is not None
    assert result.total >= 0
    assert isinstance(result.items, list)


@pytest.mark.asyncio
async def test_create_agenda_item(db_session):
    """Test creating a new agenda item"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    item_data = AgendaItemCreate(
        order_index=0,
        title="Test Agenda Item",
        duration_minutes=15,
        presenter_name="Test Presenter",
        description="Test description"
    )
    
    item = await agenda_service.create_agenda_item(db_session, meeting_id, item_data)
    
    assert item is not None
    assert item.title == "Test Agenda Item"
    assert item.duration_minutes == 15
    assert item.meeting_id == meeting_id


@pytest.mark.asyncio
async def test_update_agenda_item(db_session):
    """Test updating an agenda item"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    item_data = AgendaItemCreate(
        order_index=0,
        title="Original Title",
        duration_minutes=10,
    )
    
    # Create item
    item = await agenda_service.create_agenda_item(db_session, meeting_id, item_data)
    
    # Update item
    from app.schemas.agenda import AgendaItemUpdate
    update_data = AgendaItemUpdate(title="Updated Title", duration_minutes=20)
    updated = await agenda_service.update_agenda_item(db_session, item.id, update_data)
    
    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.duration_minutes == 20


@pytest.mark.asyncio
async def test_delete_agenda_item(db_session):
    """Test deleting an agenda item"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    item_data = AgendaItemCreate(
        order_index=0,
        title="To Delete",
        duration_minutes=5,
    )
    
    # Create item
    item = await agenda_service.create_agenda_item(db_session, meeting_id, item_data)
    item_id = item.id
    
    # Delete item
    success = await agenda_service.delete_agenda_item(db_session, item_id)
    assert success is True
    
    # Verify deleted
    deleted_item = await agenda_service.get_agenda_item(db_session, item_id)
    assert deleted_item is None


@pytest.mark.asyncio
async def test_generate_agenda_ai(db_session):
    """Test AI agenda generation"""
    request = AgendaGenerateRequest(
        meeting_id=UUID("c0000001-0000-0000-0000-000000000001"),
        meeting_title="Test Meeting",
        meeting_type="steering",
        meeting_description="Test description",
        duration_minutes=60,
    )
    
    result = await agenda_service.generate_agenda_ai(db_session, request)
    
    assert result is not None
    assert len(result.items) > 0
    assert result.total_duration_minutes > 0
    assert all(item.title for item in result.items)


@pytest.mark.asyncio
async def test_save_agenda(db_session):
    """Test saving a complete agenda"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    items = [
        AgendaItemCreate(order_index=0, title="Item 1", duration_minutes=10),
        AgendaItemCreate(order_index=1, title="Item 2", duration_minutes=20),
        AgendaItemCreate(order_index=2, title="Item 3", duration_minutes=15),
    ]
    
    from app.schemas.agenda import AgendaSaveRequest
    save_request = AgendaSaveRequest(meeting_id=meeting_id, items=items)
    
    result = await agenda_service.save_agenda(db_session, save_request)
    
    assert result is not None
    assert result.total == 3
    assert result.total_duration_minutes == 45

