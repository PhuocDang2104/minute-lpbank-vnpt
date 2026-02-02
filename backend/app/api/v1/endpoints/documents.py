"""
Documents API endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentList,
    DocumentUploadResponse,
)
from app.services import document_service

router = APIRouter(tags=["documents"])


@router.get("/meeting/{meeting_id}", response_model=DocumentList)
async def list_meeting_documents(
    meeting_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all documents for a meeting"""
    return await document_service.list_documents(db, meeting_id, skip, limit)


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single document by ID"""
    doc = await document_service.get_document(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
):
    """
    Upload a new document (mock implementation).
    
    In production, this would handle actual file upload.
    Currently just stores metadata.
    """
    return await document_service.upload_document(db, data)


@router.post("/upload-file", response_model=DocumentUploadResponse)
async def upload_document_file(
    meeting_id: str | None = Form(default=None),
    project_id: str | None = Form(default=None),
    uploaded_by: str | None = Form(default=None),
    description: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a real file to server storage and register metadata (still mock DB).
    """
    meeting_uuid = None
    uploaded_by_uuid = None
    if meeting_id:
        try:
            meeting_uuid = UUID(meeting_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid meeting_id")
    if project_id:
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project_id")
    if uploaded_by:
        try:
            uploaded_by_uuid = UUID(uploaded_by)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid uploaded_by")

    return await document_service.upload_document_file(
        db=db,
        file=file,
        meeting_id=meeting_uuid,
        project_id=project_uuid,
        uploaded_by=uploaded_by_uuid,
        description=description,
    )


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
):
    """Update a document's metadata"""
    doc = await document_service.update_document(db, document_id, data)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a document"""
    success = await document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return None
