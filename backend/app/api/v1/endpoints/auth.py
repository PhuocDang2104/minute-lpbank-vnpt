"""
Authentication API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.auth import (
    UserRegister, UserRegisterResponse, UserLogin, Token,
    CurrentUser, PasswordChange, PasswordReset
)
from app.services import auth_service
from app.core.security import get_current_user, get_current_user_id
from app.services.email_service import send_email, is_email_enabled

router = APIRouter()


# ============================================
# Register / Signup
# ============================================

@router.post('/register', response_model=UserRegisterResponse)
def register(
    data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: At least 6 characters
    - **display_name**: User's display name (2-100 characters)
    - **department_id**: Optional department UUID
    - **organization_id**: Optional organization UUID
    """
    return auth_service.register_user(db, data)


# ============================================
# Login
# ============================================

@router.post('/login', response_model=Token)
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password to get access token.
    
    Returns JWT access token and refresh token.
    """
    return auth_service.login(db, data)


@router.post('/token', response_model=Token)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint (for Swagger UI).
    
    Use email as username.
    """
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    return auth_service.login(db, login_data)


# ============================================
# Token Refresh
# ============================================

@router.post('/refresh', response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    return auth_service.refresh_tokens(db, refresh_token)


# ============================================
# Current User
# ============================================

@router.get('/me', response_model=CurrentUser)
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    
    Requires valid access token in Authorization header.
    """
    user_id = current_user.get("sub")
    user = auth_service.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# ============================================
# Password Management
# ============================================

@router.post('/change-password')
def change_password(
    data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for current user.
    
    Requires current password for verification.
    """
    user_id = current_user.get("sub")
    return auth_service.change_password(db, user_id, data)


@router.post('/forgot-password')
def forgot_password(data: PasswordReset):
    """
    Request password reset email.
    
    Note: Email sending not implemented in demo version.
    """
    # In production, this would:
    # 1. Generate reset token
    # 2. Save token with expiry
    # 3. Send email with reset link
    return {
        "message": f"If an account exists for {data.email}, a password reset link has been sent.",
        "note": "Email sending not implemented in demo version"
    }


# ============================================
# Logout
# ============================================

@router.post('/logout')
def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: With JWT, logout is handled client-side by deleting the token.
    For enhanced security, implement token blacklisting.
    """
    return {
        "message": "Logged out successfully",
        "note": "Please delete the token from client storage"
    }


# ============================================
# Verify Token
# ============================================

@router.get('/verify')
def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify if the current token is valid.
    
    Returns user info if token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role")
    }


class WelcomeRequest(BaseModel):
    email: str
    display_name: str = "Bạn"


@router.post('/welcome')
def send_welcome_email(payload: WelcomeRequest):
    """
    Send welcome email manually (for Supabase signup flows).
    """
    if not is_email_enabled():
        raise HTTPException(status_code=500, detail="Email not configured")
    subject = "Chào mừng bạn đến MeetMate"
    body_text = (
        f"Xin chào {payload.display_name},\n\n"
        "Tài khoản của bạn đã được tạo thành công.\n"
        "Hãy đăng nhập để trải nghiệm MeetMate.\n\n"
        "Trân trọng,\nMeetMate"
    )
    body_html = f"""
    <p>Xin chào <b>{payload.display_name}</b>,</p>
    <p>Tài khoản của bạn đã được tạo thành công.</p>
    <p>Hãy đăng nhập để trải nghiệm MeetMate.</p>
    <p>Trân trọng,<br/>MeetMate</p>
    """
    res = send_email(
        to_emails=[payload.email],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
    )
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Send failed"))
    return {"message": "Welcome email sent"}
