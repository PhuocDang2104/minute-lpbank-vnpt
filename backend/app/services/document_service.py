"""
Document Service - Mock implementation for document management
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import logging
import os
from fastapi import UploadFile

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.storage_client import (
    build_object_key,
    generate_presigned_get_url,
    is_storage_configured,
    upload_bytes_to_storage,
)
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentList,
    DocumentUploadResponse,
)

logger = logging.getLogger(__name__)

# In-memory storage for mock documents (simulating database)
_mock_documents: dict[str, Document] = {}


def _init_mock_documents():
    """Initialize with some mock documents"""
    mock_data = [
        {
            "id": UUID("e0000001-0000-0000-0000-000000000001"),
            "meeting_id": UUID("c0000001-0000-0000-0000-000000000001"),
            "project_id": None,
            "title": "Core Banking Q4 2024 - Project Status Report.pdf",
            "file_type": "pdf",
            "file_size": 2048000,
            "description": "Báo cáo tiến độ dự án Core Banking Q4 2024",
            "file_url": "/mock/docs/project-status-q4.pdf",
            "uploaded_by": UUID("b0000001-0000-0000-0000-000000000001"),
            "uploaded_at": datetime.now(),
        },
        {
            "id": UUID("e0000002-0000-0000-0000-000000000002"),
            "meeting_id": UUID("c0000001-0000-0000-0000-000000000001"),
            "project_id": None,
            "title": "Budget Review - Core Banking.xlsx",
            "file_type": "xlsx",
            "file_size": 512000,
            "description": "Bảng theo dõi ngân sách dự án",
            "file_url": "/mock/docs/budget-review.xlsx",
            "uploaded_by": UUID("b0000001-0000-0000-0000-000000000001"),
            "uploaded_at": datetime.now(),
        },
        {
            "id": UUID("e0000003-0000-0000-0000-000000000003"),
            "meeting_id": UUID("c0000001-0000-0000-0000-000000000001"),
            "project_id": None,
            "title": "Risk Assessment Matrix.pptx",
            "file_type": "pptx",
            "file_size": 1024000,
            "description": "Ma trận đánh giá rủi ro dự án",
            "file_url": "/mock/docs/risk-matrix.pptx",
            "uploaded_by": UUID("b0000009-0000-0000-0000-000000000009"),
            "uploaded_at": datetime.now(),
        },
        {
            "id": UUID("e0000004-0000-0000-0000-000000000004"),
            "meeting_id": UUID("c0000002-0000-0000-0000-000000000002"),
            "project_id": None,
            "title": "Sprint 23 - User Stories.pdf",
            "file_type": "pdf",
            "file_size": 768000,
            "description": "Danh sách User Stories cho Sprint 23",
            "file_url": "/mock/docs/sprint23-stories.pdf",
            "uploaded_by": UUID("b0000002-0000-0000-0000-000000000002"),
            "uploaded_at": datetime.now(),
        },
        {
            "id": UUID("e0000005-0000-0000-0000-000000000005"),
            "meeting_id": UUID("c0000002-0000-0000-0000-000000000002"),
            "project_id": None,
            "title": "Mobile App Wireframes v2.3.pdf",
            "file_type": "pdf",
            "file_size": 3072000,
            "description": "Wireframes cho Mobile Banking App phiên bản mới",
            "file_url": "/mock/docs/wireframes-v2.3.pdf",
            "uploaded_by": UUID("b0000006-0000-0000-0000-000000000006"),
            "uploaded_at": datetime.now(),
        },
    ]
    
    for doc_data in mock_data:
        doc = Document(**doc_data)
        _mock_documents[str(doc.id)] = doc


# Initialize mock data
_init_mock_documents()


def _with_presigned_url(doc: Document) -> Document:
    """Attach presigned URL if stored in S3."""
    if getattr(doc, "storage_key", None) and is_storage_configured():
        url = generate_presigned_get_url(doc.storage_key, expires_in=3600)
        if url:
            doc_dict = doc.model_dump()
            doc_dict["file_url"] = url
            return Document(**doc_dict)
    return doc


async def list_documents(
    db: Session,
    meeting_id: UUID,
    skip: int = 0,
    limit: int = 50,
) -> DocumentList:
    """List all documents for a meeting"""
    docs = [
        doc for doc in _mock_documents.values()
        if doc.meeting_id == meeting_id
    ]
    docs.sort(key=lambda x: x.uploaded_at, reverse=True)

    docs = [_with_presigned_url(d) for d in docs]
    
    return DocumentList(
        documents=docs[skip:skip + limit],
        total=len(docs),
    )


async def list_all_documents(
    db: Session,
    meeting_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> DocumentList:
    """List all documents (mock) with optional meeting filter"""
    docs = list(_mock_documents.values())
    if meeting_id:
        docs = [d for d in docs if d.meeting_id == meeting_id]
    if project_id:
        docs = [d for d in docs if getattr(d, "project_id", None) == project_id]
    docs.sort(key=lambda x: x.uploaded_at, reverse=True)
    docs = [_with_presigned_url(d) for d in docs]
    return DocumentList(documents=docs[skip:skip + limit], total=len(docs))


async def get_document(db: Session, document_id: UUID) -> Optional[Document]:
    """Get a single document by ID"""
    doc = _mock_documents.get(str(document_id))
    if doc:
        return _with_presigned_url(doc)
    return None


async def upload_document(
    db: Session,
    data: DocumentCreate,
) -> DocumentUploadResponse:
    """Upload a new document (mock - just stores metadata)"""
    doc_id = uuid4()
    project_id = data.project_id

    # If meeting_id provided but project_id missing, inherit from meeting
    if data.meeting_id and not project_id:
        res = db.execute(
            text("SELECT project_id::text FROM meeting WHERE id = :mid"),
            {'mid': data.meeting_id}
        )
        row = res.fetchone()
        if row:
            project_id = UUID(row[0]) if row[0] else None
    
    # Generate mock file URL
    file_ext = data.file_type.lower()
    file_url = data.file_url or f"/mock/docs/{doc_id}.{file_ext}"
    
    doc = Document(
        id=doc_id,
        meeting_id=data.meeting_id,
        project_id=project_id,
        title=data.title,
        file_type=data.file_type,
        file_size=data.file_size or 1024000,  # Default 1MB
        description=data.description,
        file_url=file_url,
        uploaded_by=data.uploaded_by,
        uploaded_at=datetime.now(),
    )
    
    _mock_documents[str(doc_id)] = doc
    logger.info(f"[Mock] Uploaded document: {doc.title}")
    
    return DocumentUploadResponse(
        id=doc_id,
        title=doc.title,
        file_url=file_url,
        message="Tài liệu đã được tải lên thành công (mock)",
    )


async def upload_document_file(
    db: Session,
    file: UploadFile,
    meeting_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    uploaded_by: Optional[UUID] = None,
    description: Optional[str] = None,
) -> DocumentUploadResponse:
    """Upload a real file to Supabase S3 when configured, else local."""

    doc_id = uuid4()
    filename = file.filename or f"{doc_id}"
    file_ext = filename.split(".")[-1] if "." in filename else "bin"

    content = await file.read()
    file_size = len(content)
    storage_key = None
    file_url = None

    if is_storage_configured():
        try:
            object_key = build_object_key(filename, prefix="documents")
            upload_bytes_to_storage(content, object_key, content_type=file.content_type)
            storage_key = object_key
            file_url = generate_presigned_get_url(object_key, expires_in=3600)
        except Exception as exc:
            logger.error("Upload to storage failed, falling back to local file: %s", exc)

    if not storage_key:
        storage_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploaded_files")
        os.makedirs(storage_dir, exist_ok=True)
        stored_name = f"{doc_id}.{file_ext}"
        stored_path = os.path.join(storage_dir, stored_name)
        with open(stored_path, "wb") as out:
            out.write(content)
        file_url = f"/files/{stored_name}"
    else:
        logger.info("[Upload] Stored document in Supabase Storage at key=%s", storage_key)

    resolved_project_id = project_id
    if meeting_id and not resolved_project_id:
        res = db.execute(text("SELECT project_id::text FROM meeting WHERE id = :mid"), {'mid': meeting_id})
        row = res.fetchone()
        if row:
            resolved_project_id = UUID(row[0]) if row[0] else None

    doc = Document(
        id=doc_id,
        meeting_id=meeting_id or UUID("00000000-0000-0000-0000-000000000000"),
        project_id=resolved_project_id,
        title=filename,
        file_type=file_ext,
        file_size=file_size,
        description=description,
        file_url=file_url,
        storage_key=storage_key,
        uploaded_by=uploaded_by,
        uploaded_at=datetime.now(),
    )
    _mock_documents[str(doc_id)] = doc

    logger.info(f"[Upload] Stored file {filename}, size={file_size} bytes")

    return DocumentUploadResponse(
        id=doc_id,
        title=filename,
        file_url=file_url,
        storage_key=storage_key,
        message="Tải lên thành công",
    )


async def update_document(
    db: Session,
    document_id: UUID,
    data: DocumentUpdate,
) -> Optional[Document]:
    """Update a document"""
    doc = _mock_documents.get(str(document_id))
    if not doc:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doc, key, value)
    
    _mock_documents[str(document_id)] = doc
    return doc


async def delete_document(db: Session, document_id: UUID) -> bool:
    """Delete a document"""
    if str(document_id) in _mock_documents:
        del _mock_documents[str(document_id)]
        return True
    return False
