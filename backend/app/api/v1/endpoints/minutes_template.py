"""
Minutes Template API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import template_service
from app.schemas.minutes_template import (
    MinutesTemplateCreate,
    MinutesTemplateUpdate,
    MinutesTemplateResponse,
    MinutesTemplateList,
)

router = APIRouter()


@router.get('', response_model=MinutesTemplateList)
def list_templates(
    meeting_type: Optional[str] = Query(None, description="Filter by meeting type"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all minutes templates"""
    return template_service.list_templates(
        db=db,
        meeting_type=meeting_type,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get('/default', response_model=MinutesTemplateResponse)
def get_default_template(db: Session = Depends(get_db)):
    """Get the default template"""
    template = template_service.get_default_template(db)
    if not template:
        raise HTTPException(status_code=404, detail="No default template found")
    return template


@router.get('/{template_id}', response_model=MinutesTemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a single template by ID"""
    template = template_service.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post('/', response_model=MinutesTemplateResponse, status_code=201)
def create_template(
    data: MinutesTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new template"""
    try:
        return template_service.create_template(db=db, data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put('/{template_id}', response_model=MinutesTemplateResponse)
def update_template(
    template_id: str,
    data: MinutesTemplateUpdate,
    db: Session = Depends(get_db),
):
    """Update a template"""
    template = template_service.update_template(db=db, template_id=template_id, data=data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete('/{template_id}', status_code=204)
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete a template"""
    success = template_service.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return None


@router.post('/{template_id}/set-default', response_model=MinutesTemplateResponse)
def set_default_template(template_id: str, db: Session = Depends(get_db)):
    """Set a template as default"""
    template = template_service.set_default_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

