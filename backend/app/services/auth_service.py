"""
Authentication Service
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status

from app.schemas.auth import (
    UserRegister, UserRegisterResponse, UserLogin, Token,
    CurrentUser, PasswordChange
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.services.email_service import send_email, is_email_enabled


def get_user_by_email(db: Session, email: str) -> Optional[dict]:
    """Get user by email with password hash and status"""
    print(f"[AUTH] Looking up user: {email}")
    query = text("""
        SELECT 
            u.id::text,
            u.email,
            u.display_name,
            u.role,
            u.password_hash,
            u.department_id::text,
            u.avatar_url,
            u.organization_id::text,
            u.created_at,
            u.is_active,
            u.last_login_at,
            d.name as department_name
        FROM user_account u
        LEFT JOIN department d ON u.department_id = d.id
        WHERE u.email = :email
    """)
    try:
        result = db.execute(query, {'email': email})
        row = result.fetchone()
    except Exception as e:
        db.rollback()
        print(f"[AUTH] Failed to query user: {e}")
        raise

    if not row:
        print(f"[AUTH] User not found: {email}")
        return None

    print(f"[AUTH] User found: {row[1]}, has_password: {row[4] is not None}, active: {row[9]}")
    return {
        'id': row[0],
        'email': row[1],
        'display_name': row[2],
        'role': row[3] or 'user',
        'password_hash': row[4],
        'department_id': row[5],
        'avatar_url': row[6],
        'organization_id': row[7],
        'created_at': row[8],
        'is_active': row[9] if row[9] is not None else True,
        'last_login_at': row[10],
        'department_name': row[11]
    }


def get_user_by_id(db: Session, user_id: str) -> Optional[CurrentUser]:
    """Get user by ID (without password)"""
    query = text("""
        SELECT 
            u.id::text, u.email, u.display_name, u.role,
            u.department_id::text, u.avatar_url,
            u.organization_id::text, u.created_at,
            u.is_active, u.last_login_at,
            d.name as department_name
        FROM user_account u
        LEFT JOIN department d ON u.department_id = d.id
        WHERE u.id = :user_id
    """)
    
    result = db.execute(query, {'user_id': user_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    return CurrentUser(
        id=row[0],
        email=row[1],
        display_name=row[2],
        role=row[3] or 'user',
        department_id=row[4],
        avatar_url=row[5],
        organization_id=row[6],
        created_at=row[7],
        is_active=row[8] if row[8] is not None else True,
        last_login_at=row[9],
        department_name=row[10]
    )


def register_user(db: Session, data: UserRegister) -> UserRegisterResponse:
    """Register a new user"""
    # Check if email already exists
    existing = get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    user_id = str(uuid4())
    password_hash = hash_password(data.password)
    now = datetime.utcnow()
    
    query = text("""
        INSERT INTO user_account (
            id, email, display_name, password_hash, role,
            department_id, organization_id, created_at, updated_at,
            is_active, last_login_at
        )
        VALUES (
            :id, :email, :display_name, :password_hash, 'user',
            :department_id, :organization_id, :created_at, :updated_at,
            :is_active, :last_login_at
        )
        RETURNING id::text
    """)
    
    try:
        db.execute(query, {
            'id': user_id,
            'email': data.email,
            'display_name': data.display_name,
            'password_hash': password_hash,
            'department_id': data.department_id,
            'organization_id': data.organization_id,
            'created_at': now,
            'updated_at': now,
            'is_active': True,
            'last_login_at': None
        })
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

    # Send welcome email (best effort)
    if is_email_enabled():
        try:
            subject = "Chào mừng bạn đến MeetMate"
            body_text = (
                f"Xin chào {data.display_name},\n\n"
                "Tài khoản của bạn đã được tạo thành công.\n"
                "Hãy đăng nhập để trải nghiệm MeetMate.\n\n"
                "Trân trọng,\nMeetMate"
            )
            body_html = f"""
            <p>Xin chào <b>{data.display_name}</b>,</p>
            <p>Tài khoản của bạn đã được tạo thành công.</p>
            <p>Hãy đăng nhập để trải nghiệm MeetMate.</p>
            <p>Trân trọng,<br/>MeetMate</p>
            """
            send_email(
                to_emails=[data.email],
                subject=subject,
                body_text=body_text,
                body_html=body_html,
            )
        except Exception as exc:
            # Không chặn đăng ký vì lỗi email
            print(f"[AUTH] Welcome email failed for {data.email}: {exc}")
    
    return UserRegisterResponse(
        id=user_id,
        email=data.email,
        display_name=data.display_name,
        role='user',
        message="User registered successfully. Please login to continue."
    )


def authenticate_user(db: Session, email: str, password: str) -> Optional[dict]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    
    if not user:
        print(f"[AUTH] Login rejected: user not found ({email})")
        return None

    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    password_hash = user.get('password_hash')
    if not password_hash:
        print(f"[AUTH] Login rejected: no password set for {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has no password set. Please reset your password."
        )
    
    if not verify_password(password, password_hash):
        print(f"[AUTH] Login rejected: wrong password for {email}")
        return None
    
    return user


def login(db: Session, data: UserLogin) -> Token:
    """Login user and return tokens"""
    print(f"[AUTH] Login attempt for: {data.email}")
    
    user = authenticate_user(db, data.email, data.password)
    
    if not user:
        print(f"[AUTH] Login failed for: {data.email} (invalid credentials)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"[AUTH] Login successful for: {data.email}")
    
    # Create tokens
    token_data = {
        "sub": user['id'],
        "email": user['email'],
        "role": user['role']
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Update last login
    try:
        db.execute(
            text("""
                UPDATE user_account
                SET last_login_at = :last_login_at, updated_at = :updated_at
                WHERE id = :user_id
            """),
            {
                'user_id': user['id'],
                'last_login_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[AUTH] Failed to update last_login_at for {data.email}: {e}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type='bearer',
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def refresh_tokens(db: Session, refresh_token: str) -> Token:
    """Refresh access token using refresh token"""
    payload = verify_token(refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user = get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Create new tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role
    }
    
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type='bearer',
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def change_password(
    db: Session, 
    user_id: str, 
    data: PasswordChange
) -> dict:
    """Change user password"""
    # Get user with password hash
    query = text("""
        SELECT password_hash FROM user_account WHERE id = :user_id
    """)
    result = db.execute(query, {'user_id': user_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password (if set)
    if row[0] and not verify_password(data.current_password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    new_hash = hash_password(data.new_password)
    update_query = text("""
        UPDATE user_account 
        SET password_hash = :password_hash, updated_at = :updated_at
        WHERE id = :user_id
    """)
    
    db.execute(update_query, {
        'user_id': user_id,
        'password_hash': new_hash,
        'updated_at': datetime.utcnow()
    })
    db.commit()
    
    return {"message": "Password changed successfully"}


# ============================================
# Legacy stub for backward compatibility
# ============================================

def login_stub(username: str, password: str) -> Token:
    """Stub login for testing (deprecated)"""
    from app.services import user_service
    user = user_service.get_user_stub()
    return Token(
        access_token=f"fake-token-for-{user.id}",
        token_type='bearer',
        expires_in=3600
    )
