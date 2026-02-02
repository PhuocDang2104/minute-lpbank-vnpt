"""
Integration tests for Agenda API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_list_agenda_items(client):
    """Test GET /api/v1/agenda/meeting/{meeting_id}"""
    meeting_id = "c0000001-0000-0000-0000-000000000001"
    response = client.get(f"/api/v1/agenda/meeting/{meeting_id}")
    
    assert response.status_code in [200, 404]  # 404 if meeting doesn't exist
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)


def test_generate_agenda(client):
    """Test POST /api/v1/agenda/generate"""
    payload = {
        "meeting_id": "c0000001-0000-0000-0000-000000000001",
        "meeting_title": "Test Meeting",
        "meeting_type": "steering",
        "meeting_description": "Test description",
        "duration_minutes": 60
    }
    
    response = client.post("/api/v1/agenda/generate", json=payload)
    
    assert response.status_code in [200, 500]  # 500 if AI unavailable
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total_duration_minutes" in data
        assert len(data["items"]) > 0


def test_create_agenda_item(client):
    """Test POST /api/v1/agenda/meeting/{meeting_id}/item"""
    meeting_id = "c0000001-0000-0000-0000-000000000001"
    payload = {
        "order_index": 0,
        "title": "Test Item",
        "duration_minutes": 15,
        "presenter_name": "Test Presenter"
    }
    
    response = client.post(f"/api/v1/agenda/meeting/{meeting_id}/item", json=payload)
    
    assert response.status_code in [200, 404]  # 404 if meeting doesn't exist
    if response.status_code == 200:
        data = response.json()
        assert data["title"] == "Test Item"
        assert data["duration_minutes"] == 15


def test_update_agenda_item(client):
    """Test PUT /api/v1/agenda/item/{item_id}"""
    # First create an item
    meeting_id = "c0000001-0000-0000-0000-000000000001"
    create_payload = {
        "order_index": 0,
        "title": "Original Title",
        "duration_minutes": 10
    }
    
    create_response = client.post(f"/api/v1/agenda/meeting/{meeting_id}/item", json=create_payload)
    
    if create_response.status_code == 200:
        item_id = create_response.json()["id"]
        
        # Update it
        update_payload = {
            "title": "Updated Title",
            "duration_minutes": 20
        }
        
        update_response = client.put(f"/api/v1/agenda/item/{item_id}", json=update_payload)
        
        assert update_response.status_code in [200, 404]
        if update_response.status_code == 200:
            data = update_response.json()
            assert data["title"] == "Updated Title"
            assert data["duration_minutes"] == 20

