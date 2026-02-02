from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectList,
    ProjectMemberList,
    ProjectMember,
)
from app.schemas.document import DocumentList
from app.schemas.meeting import MeetingList
from app.schemas.action_item import ActionItemList
from app.services import project_service
from app.services import document_service, meeting_service, action_item_service

# Allow all authenticated users to view/create projects (no admin gate)
router = APIRouter(tags=["projects"])


@router.get("/", response_model=ProjectList)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: str | None = None,
    department_id: str | None = None,
    organization_id: str | None = None,
    db: Session = Depends(get_db)
):
    projects, total = project_service.list_projects(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        department_id=department_id,
        organization_id=organization_id,
    )
    return ProjectList(projects=projects, total=total)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    return project_service.create_project(db, data)


@router.patch("/{project_id}", response_model=Project)
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = project_service.update_project(db, project_id, data)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    ok = project_service.delete_project(db, project_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return None


# Members
@router.get("/{project_id}/members", response_model=ProjectMemberList)
def list_members(project_id: str, db: Session = Depends(get_db)):
    return project_service.list_members(db, project_id)


@router.post("/{project_id}/members", response_model=ProjectMember, status_code=status.HTTP_201_CREATED)
def add_member(project_id: str, user_id: str, role: str = "member", db: Session = Depends(get_db)):
    return project_service.add_member(db, project_id, user_id, role)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(project_id: str, user_id: str, db: Session = Depends(get_db)):
    ok = project_service.remove_member(db, project_id, user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return None


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMember)
def update_member_role(project_id: str, user_id: str, role: str, db: Session = Depends(get_db)):
    updated = project_service.add_member(db, project_id, user_id, role)  # upsert role
    return updated


# Related resources
@router.get("/{project_id}/documents", response_model=DocumentList)
async def list_project_documents(project_id: str, db: Session = Depends(get_db)):
    """List documents by project (mock storage)"""
    from uuid import UUID
    project_uuid = UUID(project_id)
    return await document_service.list_all_documents(db, meeting_id=None, project_id=project_uuid, skip=0, limit=500)


@router.get("/{project_id}/meetings", response_model=MeetingList)
def list_project_meetings(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    meetings, total = meeting_service.list_meetings(db, skip=skip, limit=limit, project_id=project_id)
    return MeetingList(meetings=meetings, total=total)


@router.get("/{project_id}/action-items", response_model=ActionItemList)
def list_project_action_items(
    project_id: str,
    status: str | None = None,
    priority: str | None = None,
    owner_user_id: str | None = None,
    db: Session = Depends(get_db),
):
    return action_item_service.list_all_action_items(
        db=db,
        status=status,
        priority=priority,
        owner_user_id=owner_user_id,
        overdue_only=False,
        project_id=project_id,
    )
