"""
Knowledge Hub API endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.knowledge import (
    KnowledgeDocument,
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentList,
    KnowledgeDocumentUploadResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
)
from app.services import knowledge_service

router = APIRouter(tags=["knowledge"])


@router.get("/documents", response_model=KnowledgeDocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    document_type: Optional[str] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    meeting_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    """List all knowledge documents with optional filters"""
    return await knowledge_service.list_documents(
        db, skip, limit, document_type, source, category, meeting_id, project_id
    )


@router.get("/documents/{document_id}", response_model=KnowledgeDocument)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single document by ID"""
    doc = await knowledge_service.get_document(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.post("/documents/upload", response_model=KnowledgeDocumentUploadResponse)
async def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    document_type: str = Form("document"),
    source: str = Form("Uploaded"),
    file_type: str = Form("pdf"),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    uploaded_by: Optional[UUID] = Form(None),
    meeting_id: Optional[UUID] = Form(None),
    project_id: Optional[UUID] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Upload a new knowledge document.
    
    In production, this would handle actual file upload and storage.
    Currently just stores metadata (mock implementation).
    """
    # Parse tags
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Get file size if file provided
    file_size = None
    if file:
        file_size = file.size if hasattr(file, 'size') else None
    
    data = KnowledgeDocumentCreate(
        title=title,
        description=description,
        document_type=document_type,
        source=source,
        file_type=file_type,
        file_size=file_size,
        category=category,
        tags=tag_list,
        uploaded_by=uploaded_by,
        meeting_id=meeting_id,
        project_id=project_id,
    )
    
    return await knowledge_service.upload_document(db, data, file)


@router.put("/documents/{document_id}", response_model=KnowledgeDocument)
async def update_document(
    document_id: UUID,
    data: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
):
    """Update a document's metadata"""
    doc = await knowledge_service.update_document(db, document_id, data)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a document"""
    success = await knowledge_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return None


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_documents(
    request: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
):
    """Search documents by query string"""
    return await knowledge_service.search_documents(db, request)


@router.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(
    request: KnowledgeQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Query knowledge base using AI.
    
    Uses Gemini to search and answer questions based on knowledge documents.
    """
    return await knowledge_service.query_knowledge_ai(db, request)


@router.post("/ingest/{document_id}")
async def ingest_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Trigger ingestion + embedding for a document (stub implementation).
    """
    result = await knowledge_service.ingest_document(db, document_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return {"status": result["status"]}


@router.get("/recent-queries")
async def get_recent_queries(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get recent search queries (mock - would come from database)"""
    # In production, this would query a search_history table
    return {
        "queries": [
            {"query": "Data retention policy theo NHNN", "timestamp": "10 phút trước"},
            {"query": "CR-2024-015 API Gateway status", "timestamp": "1 giờ trước"},
            {"query": "KYC requirements for remote onboarding", "timestamp": "2 giờ trước"},
            {"query": "Security requirements cho Core Banking", "timestamp": "3 giờ trước"},
            {"query": "Risk assessment template", "timestamp": "5 giờ trước"},
        ],
        "total": 5,
    }
