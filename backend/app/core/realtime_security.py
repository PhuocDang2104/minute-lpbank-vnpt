from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from app.core.config import get_settings


settings = get_settings()

ALGORITHM = "HS256"


def create_audio_ingest_token(session_id: str, ttl_seconds: int = 1800) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "scope": "audio_ingest",
        "session_id": session_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_audio_ingest_token(token: str, expected_session_id: Optional[str] = None) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if payload.get("scope") != "audio_ingest":
        return None
    if expected_session_id and payload.get("session_id") != expected_session_id:
        return None
    return payload

