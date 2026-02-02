"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ============================================
# Register / Signup
# ============================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    display_name: str = Field(..., min_length=2, max_length=100)
    department_id: Optional[str] = None
    organization_id: Optional[str] = None


class UserRegisterResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    message: str = "User registered successfully"


# ============================================
# Login
# ============================================

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = 'bearer'
    expires_in: int = 3600  # seconds


class TokenPayload(BaseModel):
    sub: str  # user_id
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


# ============================================
# Password
# ============================================

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


# ============================================
# Current User
# ============================================

class CurrentUser(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    organization_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True
