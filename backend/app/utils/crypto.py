import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    secret = settings.secret_key or ""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    token = _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"v1:{token}"


def decrypt_secret(token: Optional[str]) -> str:
    if not token:
        return ""
    value = token
    if value.startswith("v1:"):
        value = value[3:]
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""
