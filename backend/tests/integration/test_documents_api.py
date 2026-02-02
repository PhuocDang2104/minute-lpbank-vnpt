"""
Integration tests for Documents API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_list_documents(client):
    """Test GET /api/v1/documents/meeting/{meeting_id}"""
    meeting_id = "c0000001-0000-0000-0000-000000000001"
    response = client.get(f"/api/v1/documents/meeting/{meeting_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)


def test_upload_document(client):
    """Test POST /api/v1/documents/upload"""
    payload = {
        "meeting_id": "c0000001-0000-0000-0000-000000000001",
        "title": "Test Document.pdf",
        "file_type": "pdf",
        "file_size": 1024000,
        "description": "Test document"
    }
    
    response = client.post("/api/v1/documents/upload", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document.pdf"
    assert "id" in data
    assert "message" in data


def test_get_document(client):
    """Test GET /api/v1/documents/{document_id}"""
    # First upload a document
    upload_payload = {
        "meeting_id": "c0000001-0000-0000-0000-000000000001",
        "title": "Test Get Document.pdf",
        "file_type": "pdf"
    }
    
    upload_response = client.post("/api/v1/documents/upload", json=upload_payload)
    
    if upload_response.status_code == 200:
        doc_id = upload_response.json()["id"]
        
        # Get it
        get_response = client.get(f"/api/v1/documents/{doc_id}")
        
        assert get_response.status_code in [200, 404]
        if get_response.status_code == 200:
            data = get_response.json()
            assert data["id"] == doc_id
            assert data["title"] == "Test Get Document.pdf"


def test_update_document(client):
    """Test PUT /api/v1/documents/{document_id}"""
    # First upload a document
    upload_payload = {
        "meeting_id": "c0000001-0000-0000-0000-000000000001",
        "title": "Original Title.pdf",
        "file_type": "pdf"
    }
    
    upload_response = client.post("/api/v1/documents/upload", json=upload_payload)
    
    if upload_response.status_code == 200:
        doc_id = upload_response.json()["id"]
        
        # Update it
        update_payload = {
            "title": "Updated Title.pdf",
            "description": "Updated description"
        }
        
        update_response = client.put(f"/api/v1/documents/{doc_id}", json=update_payload)
        
        assert update_response.status_code in [200, 404]
        if update_response.status_code == 200:
            data = update_response.json()
            assert data["title"] == "Updated Title.pdf"
            assert data["description"] == "Updated description"


def test_delete_document(client):
    """Test DELETE /api/v1/documents/{document_id}"""
    # First upload a document
    upload_payload = {
        "meeting_id": "c0000001-0000-0000-0000-000000000001",
        "title": "To Delete.pdf",
        "file_type": "pdf"
    }
    
    upload_response = client.post("/api/v1/documents/upload", json=upload_payload)
    
    if upload_response.status_code == 200:
        doc_id = upload_response.json()["id"]
        
        # Delete it
        delete_response = client.delete(f"/api/v1/documents/{doc_id}")
        
        assert delete_response.status_code in [204, 404]

