from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: str
    display_name: str
    role: str = 'user'  # admin / PMO / chair / user
    department_id: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: str
    organization_id: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True


class UserList(BaseModel):
    users: List[User]
    total: int


class Department(BaseModel):
    id: str
    name: str
    organization_id: Optional[str] = None


class DepartmentList(BaseModel):
    departments: List[Department]
    total: int
