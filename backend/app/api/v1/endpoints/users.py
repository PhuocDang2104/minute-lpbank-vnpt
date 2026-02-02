from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.schemas.user import User, UserList, DepartmentList
from app.services import user_service
from app.db.session import get_db

router = APIRouter()


@router.get('/', response_model=UserList)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    department_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all users with optional search and filters"""
    users, total = user_service.list_users(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        department_id=department_id
    )
    return UserList(users=users, total=total)


@router.get('/me', response_model=User)
def get_me():
    """Get current user (stub)"""
    return user_service.get_user_stub()


@router.get('/departments', response_model=DepartmentList)
def list_departments(db: Session = Depends(get_db)):
    """List all departments"""
    departments, total = user_service.list_departments(db)
    return DepartmentList(departments=departments, total=total)


@router.get('/{user_id}', response_model=User)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a user by ID"""
    return user_service.get_user(db, user_id)
