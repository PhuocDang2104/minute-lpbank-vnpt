"""
Unit tests for document_service
"""
import pytest
from uuid import UUID

from app.services import document_service
from app.schemas.document import DocumentCreate, DocumentUpdate


@pytest.mark.asyncio
async def test_list_documents(db_session):
    """Test listing documents for a meeting"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    
    result = await document_service.list_documents(db_session, meeting_id)
    
    assert result is not None
    assert result.total >= 0
    assert isinstance(result.documents, list)


@pytest.mark.asyncio
async def test_upload_document(db_session):
    """Test uploading a document"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    doc_data = DocumentCreate(
        meeting_id=meeting_id,
        title="Test Document.pdf",
        file_type="pdf",
        file_size=1024000,
        description="Test document description"
    )
    
    result = await document_service.upload_document(db_session, doc_data)
    
    assert result is not None
    assert result.id is not None
    assert result.title == "Test Document.pdf"
    assert "success" in result.message.lower()


@pytest.mark.asyncio
async def test_get_document(db_session):
    """Test getting a document by ID"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    doc_data = DocumentCreate(
        meeting_id=meeting_id,
        title="Test Document.pdf",
        file_type="pdf",
    )
    
    # Upload first
    uploaded = await document_service.upload_document(db_session, doc_data)
    
    # Get it
    doc = await document_service.get_document(db_session, uploaded.id)
    
    assert doc is not None
    assert doc.id == uploaded.id
    assert doc.title == "Test Document.pdf"


@pytest.mark.asyncio
async def test_update_document(db_session):
    """Test updating document metadata"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    doc_data = DocumentCreate(
        meeting_id=meeting_id,
        title="Original Title.pdf",
        file_type="pdf",
    )
    
    # Upload first
    uploaded = await document_service.upload_document(db_session, doc_data)
    
    # Update
    update_data = DocumentUpdate(title="Updated Title.pdf", description="Updated description")
    updated = await document_service.update_document(db_session, uploaded.id, update_data)
    
    assert updated is not None
    assert updated.title == "Updated Title.pdf"
    assert updated.description == "Updated description"


@pytest.mark.asyncio
async def test_delete_document(db_session):
    """Test deleting a document"""
    meeting_id = UUID("c0000001-0000-0000-0000-000000000001")
    doc_data = DocumentCreate(
        meeting_id=meeting_id,
        title="To Delete.pdf",
        file_type="pdf",
    )
    
    # Upload first
    uploaded = await document_service.upload_document(db_session, doc_data)
    doc_id = uploaded.id
    
    # Delete
    success = await document_service.delete_document(db_session, doc_id)
    assert success is True
    
    # Verify deleted
    deleted_doc = await document_service.get_document(db_session, doc_id)
    assert deleted_doc is None

