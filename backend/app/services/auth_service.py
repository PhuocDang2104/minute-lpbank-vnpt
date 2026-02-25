"""
Authentication service layer.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from threading import Lock
from typing import Any, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.schemas.auth import (
    CurrentUser,
    Token,
    UserLogin,
    UserRegister,
    UserRegisterResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

_ACCESS_TOKEN_EXPIRES_IN = ACCESS_TOKEN_EXPIRE_MINUTES * 60

_LOGIN_WINDOW_SECONDS = 10 * 60
_LOGIN_BLOCK_SECONDS = 5 * 60
_MAX_FAILED_ATTEMPTS = 5
_failed_attempts: dict[str, list[float]] = {}
_blocked_until: dict[str, float] = {}
_attempts_lock = Lock()


def _now_ts() -> float:
    return datetime.now(tz=timezone.utc).timestamp()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _throttle_key(email: str, client_ip: Optional[str]) -> str:
    ip = (client_ip or "unknown").strip()
    return f"{email}|{ip}"


def _prune_attempts(now_ts: float) -> None:
    min_allowed = now_ts - _LOGIN_WINDOW_SECONDS
    for key, values in list(_failed_attempts.items()):
        filtered = [ts for ts in values if ts >= min_allowed]
        if filtered:
            _failed_attempts[key] = filtered
        else:
            _failed_attempts.pop(key, None)

    for key, blocked_at in list(_blocked_until.items()):
        if blocked_at <= now_ts:
            _blocked_until.pop(key, None)


def _check_rate_limit(key: str) -> None:
    now_ts = _now_ts()
    with _attempts_lock:
        _prune_attempts(now_ts)
        blocked_at = _blocked_until.get(key)
        if blocked_at and blocked_at > now_ts:
            retry_after = int(blocked_at - now_ts)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau {retry_after} giây.",
            )


def _record_failed_attempt(key: str) -> None:
    now_ts = _now_ts()
    with _attempts_lock:
        _prune_attempts(now_ts)
        attempts = _failed_attempts.setdefault(key, [])
        attempts.append(now_ts)
        if len(attempts) >= _MAX_FAILED_ATTEMPTS:
            _blocked_until[key] = now_ts + _LOGIN_BLOCK_SECONDS


def _clear_failed_attempts(key: str) -> None:
    with _attempts_lock:
        _failed_attempts.pop(key, None)
        _blocked_until.pop(key, None)


def _fetch_user_by_email(db: Session, email: str) -> Optional[dict[str, Any]]:
    query = text(
        """
        SELECT
            id::text AS id,
            email,
            display_name,
            password_hash,
            role,
            department_id::text AS department_id,
            organization_id::text AS organization_id,
            avatar_url,
            is_active,
            created_at,
            last_login_at
        FROM user_account
        WHERE lower(email) = :email
        LIMIT 1
        """
    )
    row = db.execute(query, {"email": email}).mappings().first()
    return dict(row) if row else None


def _fetch_user_by_id(db: Session, user_id: str) -> Optional[dict[str, Any]]:
    query = text(
        """
        SELECT
            id::text AS id,
            email,
            display_name,
            password_hash,
            role,
            department_id::text AS department_id,
            organization_id::text AS organization_id,
            avatar_url,
            is_active,
            created_at,
            last_login_at
        FROM user_account
        WHERE id = :user_id
        LIMIT 1
        """
    )
    row = db.execute(query, {"user_id": user_id}).mappings().first()
    return dict(row) if row else None


def _touch_last_login(db: Session, user_id: str) -> None:
    db.execute(
        text(
            """
            UPDATE user_account
            SET last_login_at = now(), updated_at = now()
            WHERE id = :user_id
            """
        ),
        {"user_id": user_id},
    )
    db.commit()


def _display_name_from_user(user: dict[str, Any]) -> str:
    display_name = (user.get("display_name") or "").strip()
    if display_name:
        return display_name
    email = str(user.get("email") or "")
    return email.split("@")[0] if "@" in email else "Minute User"


def _to_current_user(user: dict[str, Any]) -> CurrentUser:
    return CurrentUser(
        id=user["id"],
        email=user["email"],
        display_name=_display_name_from_user(user),
        role=user.get("role") or "user",
        department_id=user.get("department_id"),
        organization_id=user.get("organization_id"),
        avatar_url=user.get("avatar_url"),
        created_at=user.get("created_at"),
        last_login_at=user.get("last_login_at"),
        is_active=bool(user.get("is_active", True)),
    )


def issue_token_pair(user: dict[str, Any]) -> Token:
    claims = {
        "sub": user["id"],
        "email": user["email"],
        "role": user.get("role") or "user",
    }
    return Token(
        access_token=create_access_token(claims),
        refresh_token=create_refresh_token(claims),
        token_type="bearer",
        expires_in=_ACCESS_TOKEN_EXPIRES_IN,
    )


def register_user(db: Session, payload: UserRegister) -> UserRegisterResponse:
    email = _normalize_email(payload.email)
    existing = _fetch_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã tồn tại trong hệ thống.",
        )

    display_name = payload.display_name.strip()
    if not display_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tên hiển thị không hợp lệ.",
        )

    hashed_password = hash_password(payload.password)
    insert_query = text(
        """
        INSERT INTO user_account (
            email,
            display_name,
            password_hash,
            role,
            department_id,
            organization_id,
            is_active,
            created_at,
            updated_at
        )
        VALUES (
            :email,
            :display_name,
            :password_hash,
            'user',
            :department_id,
            :organization_id,
            true,
            now(),
            now()
        )
        RETURNING id::text AS id, email, display_name, role
        """
    )

    try:
        row = db.execute(
            insert_query,
            {
                "email": email,
                "display_name": display_name,
                "password_hash": hashed_password,
                "department_id": payload.department_id,
                "organization_id": payload.organization_id,
            },
        ).mappings().first()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã tồn tại trong hệ thống.",
        ) from None
    except Exception as exc:
        db.rollback()
        logger.exception("register_user failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể đăng ký tài khoản.",
        ) from exc

    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo người dùng mới.",
        )

    return UserRegisterResponse(
        id=row["id"],
        email=row["email"],
        display_name=row["display_name"] or display_name,
        role=row["role"] or "user",
    )


def authenticate_user(db: Session, payload: UserLogin, client_ip: Optional[str]) -> Token:
    email = _normalize_email(payload.email)
    key = _throttle_key(email, client_ip)
    _check_rate_limit(key)

    user = _fetch_user_by_email(db, email)
    if not user or not user.get("password_hash"):
        _record_failed_attempt(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng.",
        )

    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )

    is_valid_password = False
    try:
        is_valid_password = verify_password(payload.password, user["password_hash"])
    except Exception:
        is_valid_password = False

    if not is_valid_password:
        _record_failed_attempt(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng.",
        )

    _clear_failed_attempts(key)
    _touch_last_login(db, user["id"])
    refreshed_user = _fetch_user_by_id(db, user["id"]) or user
    return issue_token_pair(refreshed_user)


def refresh_tokens(db: Session, refresh_token: str) -> Token:
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ.",
        )

    user = _fetch_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại.",
        )

    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )

    return issue_token_pair(user)


def get_current_user_profile(db: Session, user_id: str) -> CurrentUser:
    user = _fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ.",
        )
    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )
    return _to_current_user(user)


def change_password(db: Session, user_id: str, current_password: str, new_password: str) -> None:
    user = _fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng.")
    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )

    password_hash = user.get("password_hash")
    if not password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này chưa có mật khẩu nội bộ.",
        )

    try:
        is_valid_current_password = verify_password(current_password, password_hash)
    except Exception:
        is_valid_current_password = False

    if not is_valid_current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không đúng.",
        )

    db.execute(
        text(
            """
            UPDATE user_account
            SET password_hash = :password_hash, updated_at = now()
            WHERE id = :user_id
            """
        ),
        {"password_hash": hash_password(new_password), "user_id": user_id},
    )
    db.commit()


def verify_active_token_user(db: Session, user_id: str) -> dict[str, Any]:
    user = _fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ.",
        )
    if not bool(user.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )
    return user


async def authenticate_google_user(db: Session, id_token: str) -> Token:
    claims = await verify_google_id_token(id_token)
    email = _normalize_email(str(claims.get("email", "")))
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token không chứa email hợp lệ.",
        )

    name = str(claims.get("name") or "").strip()
    picture = str(claims.get("picture") or "").strip() or None

    user = _fetch_user_by_email(db, email)
    if user:
        if not bool(user.get("is_active", True)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa.",
            )
        db.execute(
            text(
                """
                UPDATE user_account
                SET
                    display_name = COALESCE(NULLIF(:display_name, ''), display_name),
                    avatar_url = COALESCE(:avatar_url, avatar_url),
                    last_login_at = now(),
                    updated_at = now()
                WHERE id = :user_id
                """
            ),
            {
                "display_name": name,
                "avatar_url": picture,
                "user_id": user["id"],
            },
        )
        db.commit()
        latest_user = _fetch_user_by_id(db, user["id"]) or user
        return issue_token_pair(latest_user)

    display_name = name or email.split("@")[0]
    insert_query = text(
        """
        INSERT INTO user_account (
            email,
            display_name,
            role,
            avatar_url,
            is_active,
            last_login_at,
            created_at,
            updated_at
        )
        VALUES (
            :email,
            :display_name,
            'user',
            :avatar_url,
            true,
            now(),
            now(),
            now()
        )
        RETURNING id::text AS id
        """
    )
    try:
        created = db.execute(
            insert_query,
            {
                "email": email,
                "display_name": display_name,
                "avatar_url": picture,
            },
        ).mappings().first()
        db.commit()
    except IntegrityError:
        db.rollback()
        # Race condition: user created by another request; fetch and continue.
        existing = _fetch_user_by_email(db, email)
        if existing:
            return issue_token_pair(existing)
        raise

    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo tài khoản từ Google.",
        )

    latest_user = _fetch_user_by_id(db, created["id"])
    if not latest_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tải tài khoản Google vừa tạo.",
        )
    return issue_token_pair(latest_user)


async def verify_google_id_token(id_token: str) -> dict[str, Any]:
    token = (id_token or "").strip()
    if len(token) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token không hợp lệ.",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": token},
            )
    except httpx.HTTPError as exc:
        logger.warning("verify_google_id_token network error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể xác thực Google token lúc này.",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token không hợp lệ hoặc đã hết hạn.",
        )

    claims = response.json()
    if not isinstance(claims, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token không hợp lệ.",
        )

    expected_aud = settings.google_oauth_client_id.strip()
    token_aud = str(claims.get("aud", "")).strip()
    if expected_aud and token_aud != expected_aud:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token không đúng client.",
        )

    issuer = str(claims.get("iss", "")).strip()
    if issuer and issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token issuer không hợp lệ.",
        )

    email_verified = claims.get("email_verified")
    if not (email_verified is True or str(email_verified).lower() == "true"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email Google chưa được xác minh.",
        )

    exp_raw = claims.get("exp")
    if exp_raw is not None:
        try:
            exp_ts = int(str(exp_raw))
            if exp_ts <= int(_now_ts()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google token đã hết hạn.",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token không hợp lệ.",
            ) from None

    return claims
