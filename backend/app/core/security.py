"""
Security Utilities - Password Hashing & JWT
"""
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# JWT settings
ALGORITHM = "HS256"
# Shorter TTL for access token; refresh covers longer lived sessions
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 60 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7
SUPABASE_AUD = settings.supabase_jwt_aud or "authenticated"


# ============================================
# Password Hashing
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# JWT Token
# ============================================

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_supabase_token(token: str) -> Optional[dict]:
    """Decode Supabase JWT using supabase_jwt_secret if configured."""
    if not settings.supabase_jwt_secret:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[ALGORITHM],
            audience=SUPABASE_AUD,
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify token is valid and of correct type"""
    # Prefer Supabase token if configured, else fall back to local secret
    payload = decode_supabase_token(token) or decode_token(token)
    
    if not payload:
        return None
    
    # Local token has "type", Supabase token may not
    if payload.get("type") and payload.get("type") != token_type:
        return None
    
    # Check expiration (both tokens)
    exp = payload.get("exp")
    if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
        return None
    
    # Normalize role
    if "role" not in payload and payload.get("app_metadata", {}).get("role"):
        payload["role"] = payload["app_metadata"]["role"]
    if "role" not in payload and payload.get("role") is None:
        payload["role"] = payload.get("aud") or "user"

    return payload


# ============================================
# Auth Dependencies
# ============================================

def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)):
    """Get current user if token provided (optional auth)"""
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    return payload


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user (required auth)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
    
    return payload


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """Get current user ID from token"""
    return current_user.get("sub")


def get_current_profile(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Verify Supabase/local JWT and return profile info from profiles or user_account.
    Returns dict with id, email, display_name, role.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = verify_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Try profiles first
    row = None
    try:
        row = db.execute(
            text(
                "SELECT id::text, email, display_name, role "
                "FROM profiles WHERE id = :id"
            ),
            {"id": user_id},
        ).mappings().first()
    except Exception:
        row = None

    # Fallback to legacy user_account
    if not row:
        try:
            row = db.execute(
                text(
                    "SELECT id::text, email, display_name, role "
                    "FROM user_account WHERE id = :id"
                ),
                {"id": user_id},
            ).mappings().first()
        except Exception:
            row = None

    profile = {
        "id": user_id,
        "email": payload.get("email"),
        "display_name": payload.get("name") or payload.get("user_metadata", {}).get("full_name"),
        "role": payload.get("role") or payload.get("app_metadata", {}).get("role") or "user",
    }

    if row:
        profile.update({
            "email": row.get("email") or profile["email"],
            "display_name": row.get("display_name") or profile["display_name"],
            "role": row.get("role") or profile["role"],
        })

    return profile


def require_role(allowed_roles: list[str]):
    """Dependency to require specific roles"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not authorized. Required: {allowed_roles}"
            )
        return current_user
    return role_checker


# Role-based dependencies
require_admin = require_role(["admin"])
require_pmo = require_role(["admin", "PMO"])
require_chair = require_role(["admin", "PMO", "chair"])
