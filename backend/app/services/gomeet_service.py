from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from app.core.config import get_settings


settings = get_settings()

SESSION_QUERY_KEY = "sessionId"
INGEST_QUERY_KEYS = ("ingestToken", "audio_ingest_token")


class GoMeetConfigError(RuntimeError):
    pass


class GoMeetRequestError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class GoMeetResponseError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoMeetStartResult:
    host_join_url: str
    meeting_secret_key: str
    access_code: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class GoMeetJoinResult:
    join_url: str
    raw: dict[str, Any]


def _require_base_url() -> str:
    if not settings.gomeet_api_base_url:
        raise GoMeetConfigError("GOMEET_API_BASE_URL is not set")
    return settings.gomeet_api_base_url.rstrip("/")


def _build_headers(idempotency_key: str | None, require_auth: bool) -> dict[str, str]:
    headers: dict[str, str] = {}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    token = settings.gomeet_partner_token.strip() if settings.gomeet_partner_token else ""
    if require_auth:
        if not token:
            raise GoMeetConfigError("GOMEET_PARTNER_TOKEN is not set")
        headers["Authorization"] = f"Bearer {token}"
    elif token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _extract_str(payload: Any, keys: Iterable[str]) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for container_key in ("data", "result", "payload"):
        nested = payload.get(container_key)
        if isinstance(nested, dict):
            for key in keys:
                value = nested.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return None


def _extract_query_value(query: str, keys: Iterable[str]) -> Optional[str]:
    if not query:
        return None
    keyset = {k.lower() for k in keys}
    for raw_key, value in parse_qsl(query, keep_blank_values=True):
        if raw_key.lower() in keyset and value:
            return value
    return None


def _parse_host_join_url(host_join_url: str) -> tuple[Optional[str], Optional[str]]:
    parts = urlsplit(host_join_url)
    access_code = _extract_query_value(parts.query, ("accessCode", "access_code", "accesscode"))
    meeting_secret_key = _extract_query_value(parts.query, ("meetingSecretKey", "meeting_secret_key", "meetingSecret"))

    fragment = parts.fragment or ""
    frag_path = fragment
    frag_query = ""
    if "?" in fragment:
        frag_path, frag_query = fragment.split("?", 1)

    if not access_code:
        access_code = _extract_query_value(frag_query, ("accessCode", "access_code", "accesscode"))
    if not meeting_secret_key:
        meeting_secret_key = _extract_query_value(frag_query, ("meetingSecretKey", "meeting_secret_key", "meetingSecret"))

    lower_path = frag_path.lower()
    marker = "host/"
    idx = lower_path.find(marker)
    if idx >= 0:
        tail = frag_path[idx + len(marker):]
        tail = tail.lstrip("/")
        candidate = tail.split("/", 1)[0].strip()
        if candidate:
            meeting_secret_key = meeting_secret_key or candidate

    return meeting_secret_key, access_code


def _merge_query(existing: list[tuple[str, str]], updates: dict[str, str]) -> list[tuple[str, str]]:
    filtered = [(k, v) for (k, v) in existing if k not in updates]
    filtered.extend(list(updates.items()))
    return filtered


def build_full_join_url(join_url: str, session_id: str, audio_ingest_token: str) -> str:
    params = {SESSION_QUERY_KEY: session_id}
    for key in INGEST_QUERY_KEYS:
        params[key] = audio_ingest_token

    parts = urlsplit(join_url)
    if parts.fragment:
        frag_base, frag_query = (parts.fragment.split("?", 1) + [""])[:2]
        frag_params = parse_qsl(frag_query, keep_blank_values=True)
        merged = _merge_query(frag_params, params)
        new_fragment = f"{frag_base}?{urlencode(merged)}" if merged else frag_base
        return urlunsplit(parts._replace(fragment=new_fragment))

    query_params = parse_qsl(parts.query, keep_blank_values=True)
    merged = _merge_query(query_params, params)
    return urlunsplit(parts._replace(query=urlencode(merged)))


async def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timeout = settings.gomeet_timeout_seconds or 15
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, url, headers=headers, json=json, params=params)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        payload: Any | None = None
        try:
            payload = resp.json()
        except ValueError:
            payload = resp.text
        raise GoMeetRequestError(
            f"GoMeet request failed: {resp.status_code}",
            status_code=resp.status_code,
            payload=payload,
        ) from exc
    try:
        data = resp.json()
    except ValueError as exc:
        raise GoMeetResponseError("GoMeet returned non-JSON response") from exc
    if not isinstance(data, dict):
        raise GoMeetResponseError("GoMeet response is not a JSON object")
    return data


async def start_new_meeting(
    *,
    idempotency_key: str | None = None,
    payload: dict[str, Any] | None = None,
) -> GoMeetStartResult:
    base_url = _require_base_url()
    url = f"{base_url}/Meeting/StartNewMeeting"
    headers = _build_headers(idempotency_key, require_auth=True)
    data = await _request_json("POST", url, headers=headers, json=payload or {})

    host_join_url = _extract_str(data, ("hostJoinUrl", "host_join_url", "hostJoinURL"))
    meeting_secret_key = _extract_str(data, ("meetingSecretKey", "meeting_secret_key", "meetingSecret"))
    access_code = _extract_str(data, ("accessCode", "access_code", "accesscode"))
    if host_join_url and (not meeting_secret_key or not access_code):
        parsed_secret, parsed_code = _parse_host_join_url(host_join_url)
        meeting_secret_key = meeting_secret_key or parsed_secret
        access_code = access_code or parsed_code
    if not host_join_url or not meeting_secret_key or not access_code:
        raise GoMeetResponseError("GoMeet StartNewMeeting missing required fields")

    return GoMeetStartResult(
        host_join_url=host_join_url,
        meeting_secret_key=meeting_secret_key,
        access_code=access_code,
        raw=data,
    )


async def join_meeting(
    *,
    meeting_secret_key: str,
    access_code: str,
    idempotency_key: str | None = None,
) -> GoMeetJoinResult:
    base_url = _require_base_url()
    url = f"{base_url}/JoinMeetings/Join"
    headers = _build_headers(idempotency_key, require_auth=False)
    params = {"meetingSecretKey": meeting_secret_key, "accessCode": access_code}
    data = await _request_json("POST", url, headers=headers, params=params)

    join_url = _extract_str(data, ("joinUrl", "join_url", "joinURL"))
    if not join_url:
        raise GoMeetResponseError("GoMeet Join missing joinUrl")
    return GoMeetJoinResult(join_url=join_url, raw=data)
