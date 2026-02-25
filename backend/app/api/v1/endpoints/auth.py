from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.auth import (
    CurrentUser,
    GoogleLogin,
    MessageResponse,
    PasswordChange,
    RefreshTokenRequest,
    Token,
    UserLogin,
    UserRegister,
    UserRegisterResponse,
    VerifyResponse,
)
from app.services import auth_service

router = APIRouter()


def _client_ip(request: Request) -> Optional[str]:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return None


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    return auth_service.register_user(db, payload)


@router.post("/login", response_model=Token)
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    return auth_service.authenticate_user(db, payload, client_ip=_client_ip(request))


@router.post("/google", response_model=Token)
async def login_with_google(
    payload: GoogleLogin,
    db: Session = Depends(get_db),
):
    return await auth_service.authenticate_google_user(db, payload.id_token)


@router.post("/refresh", response_model=Token)
def refresh(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return auth_service.refresh_tokens(db, payload.refresh_token)


@router.get("/me", response_model=CurrentUser)
def me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ.",
        )
    return auth_service.get_current_user_profile(db, str(user_id))


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ.",
        )
    auth_service.change_password(
        db=db,
        user_id=str(user_id),
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return MessageResponse(message="Đổi mật khẩu thành công.")


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: dict = Depends(get_current_user)):
    if not current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ.",
        )
    return MessageResponse(message="Đăng xuất thành công.")


@router.get("/verify", response_model=VerifyResponse)
def verify(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ.",
        )
    user = auth_service.verify_active_token_user(db, str(user_id))
    return VerifyResponse(
        valid=True,
        user_id=user["id"],
        email=user.get("email"),
        role=user.get("role") or "user",
    )
