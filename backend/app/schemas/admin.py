from pydantic import BaseModel, Field
from typing import Optional


class AdminUserRoleUpdate(BaseModel):
    role: str = Field(..., description="New role (e.g., admin/PMO/chair/user)")


class AdminUserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Activate/deactivate user")


class AdminCreateUser(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    display_name: str
    role: Optional[str] = "user"
    department_id: Optional[str] = None
    organization_id: Optional[str] = None

