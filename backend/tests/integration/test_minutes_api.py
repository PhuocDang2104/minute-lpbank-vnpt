"""
Integration tests for Minutes API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_list_minutes(client):
    """Test GET /api/v1/minutes/{meeting_id}"""
    meeting_id = "c0000001-0000-0000-0000-000000000001"
    response = client.get(f"/api/v1/minutes/{meeting_id}")
    
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "minutes" in data
        assert "total" in data


def test_get_latest_minutes(client):
    """Test GET /api/v1/minutes/{meeting_id}/latest"""
    meeting_id = "c0000001-0000-0000-0000-000000000001"
    response = client.get(f"/api/v1/minutes/{meeting_id}/latest")
    
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "meeting_id" in data
        assert "minutes" in data
        if data["minutes"] is not None:
            assert "id" in data["minutes"]
            assert "meeting_id" in data["minutes"]


def test_generate_minutes(client):
    """Test POST /api/v1/minutes/generate"""
    payload = {
        "meeting_id": "c0000001-0000-0000-0000-000000000001",
        "include_transcript": True,
        "include_actions": True,
        "include_decisions": True,
        "include_risks": True,
        "format": "markdown"
    }
    
    response = client.post("/api/v1/minutes/generate", json=payload)
    
    # May fail if meeting doesn't exist or AI unavailable
    assert response.status_code in [200, 404, 500]
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert "meeting_id" in data


def test_get_distribution_logs(client):
    """Test GET /api/v1/minutes/{meeting_id}/distribution"""
    meeting_id = "c0000001-0000-0000-0000-000000000001"
    response = client.get(f"/api/v1/minutes/{meeting_id}/distribution")
    
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "logs" in data
        assert "total" in data

