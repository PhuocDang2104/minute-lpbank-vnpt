"""
Meeting Minutes Service
"""
from datetime import datetime
import json
import logging
import math
import re
from typing import Iterable
from typing import List, Optional, Tuple, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import get_settings
from app.schemas.minutes import (
    MeetingMinutesCreate, MeetingMinutesUpdate,
    MeetingMinutesResponse, MeetingMinutesList,
    DistributionLogCreate, DistributionLogResponse, DistributionLogList,
    GenerateMinutesRequest
)
from app.services import transcript_service, action_item_service
from app.utils.markdown_utils import render_markdown_to_html
from app.services import meeting_service, participant_service
from pathlib import Path
from datetime import timezone

logger = logging.getLogger(__name__)
settings = get_settings()


# Transcript windowing settings (character-based)
MAX_DIRECT_TRANSCRIPT_CHARS = 15000
WINDOW_CHAR_SIZE = 8000
WINDOW_CHAR_OVERLAP = 200
MAX_WINDOWS = 12


def _prefer_vietnamese_output() -> bool:
    raw = (settings.llm_output_language or "vi").strip().lower()
    return raw in {"vi", "vi-vn", "vn", "vietnamese", "vietnam", "tieng viet", "tiếng việt", ""}


def _output_language_name() -> str:
    return "Vietnamese" if _prefer_vietnamese_output() else "English"


SUMMARY_FIELD_KEYS: Tuple[str, ...] = (
    "summary",
    "executive_summary",
    "overview",
    "meeting_summary",
)

KEY_POINTS_FIELD_KEYS: Tuple[str, ...] = (
    "key_points",
    "keypoints",
    "highlights",
    "main_points",
    "takeaways",
    "bullet_points",
)


def _decode_jsonish_text(value: str) -> str:
    return (
        (value or "")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\\n", "\n")
        .replace("\\t", " ")
        .replace("\\\\", "\\")
        .strip()
    )


def _extract_embedded_summary_payload(raw_text: str) -> Tuple[str, List[str]]:
    text_value = (raw_text or "").strip()
    if not text_value:
        return "", []

    cleaned = (
        text_value.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json|text|md|markdown)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    candidates = [cleaned]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if 0 <= start < end:
        candidates.append(cleaned[start : end + 1])

    for candidate in candidates:
        quoted_keys = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_-]*)\s*:', r'\1"\2":', candidate)
        single_to_double = re.sub(
            r"'([^'\\]*(?:\\.[^'\\]*)*)'",
            lambda m: '"' + m.group(1).replace('"', '\\"') + '"',
            quoted_keys,
        )
        variants = [
            candidate,
            re.sub(r",\s*([}\]])", r"\1", candidate),
            quoted_keys,
            single_to_double,
        ]
        for variant in variants:
            try:
                parsed = json.loads(variant)
            except Exception:
                continue
            if not isinstance(parsed, dict):
                continue

            summary = ""
            for key in SUMMARY_FIELD_KEYS:
                value = parsed.get(key)
                if isinstance(value, str) and value.strip():
                    summary = value.strip()
                    break

            if not summary and isinstance(parsed.get("data"), dict):
                nested_payload = parsed.get("data") or {}
                for key in SUMMARY_FIELD_KEYS:
                    value = nested_payload.get(key)
                    if isinstance(value, str) and value.strip():
                        summary = value.strip()
                        break

            key_points: List[str] = []
            for key in KEY_POINTS_FIELD_KEYS:
                value = parsed.get(key)
                if isinstance(value, list):
                    key_points = [str(item).strip() for item in value if str(item).strip()]
                    break

            if not key_points and isinstance(parsed.get("data"), dict):
                nested_payload = parsed.get("data") or {}
                for key in KEY_POINTS_FIELD_KEYS:
                    value = nested_payload.get(key)
                    if isinstance(value, list):
                        key_points = [str(item).strip() for item in value if str(item).strip()]
                        break

            if summary or key_points:
                return _decode_jsonish_text(summary), [_decode_jsonish_text(item) for item in key_points]

    summary = ""
    key_pattern = "|".join(re.escape(k) for k in SUMMARY_FIELD_KEYS)
    summary_patterns = [
        rf'["\']?(?:{key_pattern})["\']?\s*:\s*"([\s\S]*?)"(?=\s*,\s*["\']?[A-Za-z_][A-Za-z0-9_-]*["\']?\s*:|\s*[}}])',
        rf'["\']?(?:{key_pattern})["\']?\s*:\s*\'([\s\S]*?)\'(?=\s*,\s*["\']?[A-Za-z_][A-Za-z0-9_-]*["\']?\s*:|\s*[}}])',
    ]
    for pattern in summary_patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match and match.group(1).strip():
            summary = _decode_jsonish_text(match.group(1))
            break

    points: List[str] = []
    points_key_pattern = "|".join(re.escape(k) for k in KEY_POINTS_FIELD_KEYS)
    points_match = re.search(
        rf'["\']?(?:{points_key_pattern})["\']?\s*:\s*\[([\s\S]*?)\]',
        cleaned,
        flags=re.IGNORECASE,
    )
    if points_match and points_match.group(1):
        body = points_match.group(1)
        for item_match in re.finditer(r'"((?:\\.|[^"\\])*)"|\'((?:\\.|[^\'\\])*)\'', body):
            candidate = item_match.group(1) if item_match.group(1) is not None else (item_match.group(2) or "")
            decoded = _decode_jsonish_text(candidate)
            if decoded:
                points.append(decoded)

    return summary, points


def _table_exists(db: Session, table_name: str) -> bool:
    try:
        result = db.execute(
            text("SELECT to_regclass(:table_name)"),
            {"table_name": f"public.{table_name}"},
        ).scalar()
        return bool(result)
    except Exception:
        return False


def _ensure_minutes_tables(db: Session) -> None:
    """
    Safety net for cloud environments stamped/migrated inconsistently.
    Keeps minutes generation usable even if migration was skipped.
    """
    if not _table_exists(db, "meeting_minutes"):
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS meeting_minutes (
                    id UUID PRIMARY KEY,
                    meeting_id UUID NOT NULL REFERENCES meeting(id) ON DELETE CASCADE,
                    version INTEGER NOT NULL DEFAULT 1,
                    minutes_text TEXT,
                    minutes_html TEXT,
                    minutes_markdown TEXT,
                    minutes_doc_url TEXT,
                    executive_summary TEXT,
                    generated_at TIMESTAMPTZ DEFAULT now(),
                    edited_by UUID REFERENCES user_account(id) ON DELETE SET NULL,
                    edited_at TIMESTAMPTZ,
                    status VARCHAR NOT NULL DEFAULT 'draft',
                    approved_by UUID REFERENCES user_account(id) ON DELETE SET NULL,
                    approved_at TIMESTAMPTZ
                );
                """
            )
        )
        db.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_meeting_minutes_meeting_id ON meeting_minutes(meeting_id);"
            )
        )

    if not _table_exists(db, "minutes_distribution_log"):
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS minutes_distribution_log (
                    id UUID PRIMARY KEY,
                    minutes_id UUID NOT NULL REFERENCES meeting_minutes(id) ON DELETE CASCADE,
                    meeting_id UUID NOT NULL REFERENCES meeting(id) ON DELETE CASCADE,
                    channel VARCHAR NOT NULL,
                    recipient_email VARCHAR,
                    user_id UUID REFERENCES user_account(id) ON DELETE SET NULL,
                    sent_at TIMESTAMPTZ DEFAULT now(),
                    status VARCHAR NOT NULL DEFAULT 'sent',
                    error_message TEXT,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
        )
        db.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_minutes_distribution_log_meeting_id ON minutes_distribution_log(meeting_id);"
            )
        )

    db.commit()


def _chunk_text(text: str, max_chars: int, overlap: int) -> Iterable[str]:
    """Chunk text into overlapping windows by character count."""
    if not text:
        return []
    if max_chars <= 0:
        return [text]
    overlap = max(0, min(overlap, max_chars - 1))
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


async def _summarize_transcript_windows(
    assistant: "MeetingAIAssistant",
    transcript: str,
) -> List[str]:
    """Summarize transcript by windows, then return list of summaries."""
    if not transcript:
        return []

    window_size = WINDOW_CHAR_SIZE
    if len(transcript) > WINDOW_CHAR_SIZE * MAX_WINDOWS:
        window_size = math.ceil(len(transcript) / MAX_WINDOWS)

    chunks = list(_chunk_text(transcript, window_size, WINDOW_CHAR_OVERLAP))
    summaries: List[str] = []
    output_language = _output_language_name()
    for idx, chunk in enumerate(chunks, start=1):
        prompt = (
            f"Summarize the following transcript window in {output_language} into 6-10 concise bullets. "
            "Use only provided evidence, do not hallucinate. "
            "If data is sparse, still provide a preliminary summary instead of leaving it empty. "
            "Call out notable timestamps, participants, and any action/decision/risk signals.\n\n"
            f"WINDOW {idx}/{len(chunks)}:\n{chunk}"
        )
        try:
            summary = await assistant.chat.chat(prompt)
        except Exception as exc:
            logger.warning("Failed to summarize transcript window %s: %s", idx, exc)
            summary = ""
        summary = (summary or "").strip()
        if summary:
            summaries.append(summary)
    return summaries


def _hydrate_minutes_html(minutes: MeetingMinutesResponse) -> MeetingMinutesResponse:
    """
    Ensure minutes_html is populated when minutes_markdown exists.
    Useful for older records created before markdown->HTML auto render.
    """
    if minutes.minutes_markdown and (not minutes.minutes_html or _looks_like_markdown(minutes.minutes_html)):
        try:
            minutes.minutes_html = render_markdown_to_html(minutes.minutes_markdown)
        except Exception:
            # Keep silent to avoid breaking response
            pass
    return minutes


def _looks_like_markdown(text: Optional[str]) -> bool:
    if not text:
        return True
    # heuristic: common markdown markers
    return ("| ---" in text) or ("**" in text) or ("##" in text) or ("- " in text and "<" not in text)


def _infer_session_type(meeting_type: Optional[str], request_session_type: Optional[str]) -> str:
    if request_session_type in {"meeting", "course"}:
        return request_session_type
    mt = (meeting_type or "").strip().lower()
    if not mt:
        return "meeting"

    course_markers = (
        "study",
        "training",
        "education",
        "learning",
        "workshop",
        "course",
        "class",
        "training/study",
        "dao tao",
        "đào tạo",
        "hoc",
        "học",
    )
    if any(marker in mt for marker in course_markers):
        return "course"
    return "meeting"


def _fmt_seconds(value: Optional[float]) -> str:
    if value is None:
        return ""
    total = max(0, int(value))
    mm = total // 60
    ss = total % 60
    return f"{mm:02d}:{ss:02d}"


def _load_topic_tracker(db: Session, meeting_id: str) -> List[Dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT topic_id, title, start_t, end_t
            FROM topic_segment
            WHERE meeting_id = :meeting_id
            ORDER BY start_t ASC NULLS LAST, created_at ASC
            """
        ),
        {"meeting_id": meeting_id},
    ).fetchall()
    topics: List[Dict[str, Any]] = []
    for row in rows:
        start_t = float(row[2]) if row[2] is not None else None
        end_t = float(row[3]) if row[3] is not None else None
        duration = None
        if start_t is not None and end_t is not None and end_t >= start_t:
            duration = round(end_t - start_t, 2)
        topics.append(
            {
                "topic_id": row[0],
                "title": row[1],
                "start_time": start_t,
                "end_time": end_t,
                "duration_seconds": duration,
            }
        )
    return topics


def _load_visual_highlights(db: Session, meeting_id: str, limit: int = 12) -> List[str]:
    highlights: List[str] = []
    try:
        rows = db.execute(
            text(
                """
                SELECT timestamp, event_type, description, ocr_text
                FROM visual_event
                WHERE meeting_id = :meeting_id
                ORDER BY timestamp ASC
                LIMIT :limit
                """
            ),
            {"meeting_id": meeting_id, "limit": limit},
        ).fetchall()
        for r in rows:
            t = float(r[0] or 0.0)
            evt = (r[1] or "visual").strip()
            desc = (r[2] or "").strip()
            ocr = (r[3] or "").strip()
            text_part = desc or ocr
            if text_part:
                highlights.append(f"[{_fmt_seconds(t)} | {evt}] {text_part[:220]}")
    except Exception as exc:
        logger.warning("Failed loading visual_event highlights for %s: %s", meeting_id, exc)
        db.rollback()

    try:
        rows = db.execute(
            text(
                """
                SELECT timestamp, object_label, ocr_text, confidence
                FROM visual_object_event
                WHERE meeting_id = :meeting_id
                ORDER BY timestamp ASC
                LIMIT :limit
                """
            ),
            {"meeting_id": meeting_id, "limit": max(4, limit // 2)},
        ).fetchall()
        for r in rows:
            t = float(r[0] or 0.0)
            label = (r[1] or "").strip()
            ocr = (r[2] or "").strip()
            conf = r[3]
            if not (label or ocr):
                continue
            conf_text = ""
            if conf is not None:
                conf_text = f" (conf={float(conf):.2f})"
            highlights.append(f"[{_fmt_seconds(t)} | object]{conf_text} {(label + ' ' + ocr).strip()[:220]}")
    except Exception:
        # visual_object_event may not exist on old DBs; ignore silently
        db.rollback()

    return highlights


def _safe_json_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _build_ai_filters(
    action_rows: List[Dict[str, Any]],
    decision_rows: List[Dict[str, Any]],
    risk_rows: List[Dict[str, Any]],
    topic_rows: List[Dict[str, Any]],
) -> List[str]:
    filters: List[str] = []

    if action_rows:
        filters.append(f"action:all ({len(action_rows)})")
        high_count = sum(
            1
            for row in action_rows
            if str(row.get("priority", "")).lower() in {"high", "critical"}
        )
        if high_count:
            filters.append(f"action:high_priority ({high_count})")
        unassigned_count = sum(
            1 for row in action_rows if not str(row.get("owner") or "").strip()
        )
        if unassigned_count:
            filters.append(f"action:unassigned ({unassigned_count})")

    if decision_rows:
        filters.append(f"decision:all ({len(decision_rows)})")
        pending_decisions = sum(
            1
            for row in decision_rows
            if str(row.get("status", "")).lower() in {"", "proposed", "draft"}
        )
        if pending_decisions:
            filters.append(f"decision:pending_confirmation ({pending_decisions})")

    if risk_rows:
        filters.append(f"risk:all ({len(risk_rows)})")
        high_risks = sum(
            1
            for row in risk_rows
            if str(row.get("severity", "")).lower() in {"high", "critical"}
        )
        if high_risks:
            filters.append(f"risk:high_or_critical ({high_risks})")

    if topic_rows:
        filters.append(f"topic:tracked ({len(topic_rows)})")

    return filters


def _is_placeholder_value(text_value: str) -> bool:
    value = str(text_value or "").strip().lower()
    if not value:
        return True
    markers = (
        "khong ro",
        "không rõ",
        "khong co",
        "không có",
        "unknown",
        "not specified",
        "n/a",
        "none",
        "null",
        "timestamp: khong ro",
        "timestamp: không rõ",
    )
    return any(marker in value for marker in markers)


def _normalize_key_points(raw_points: Any) -> List[str]:
    normalized: List[str] = []

    def _add_candidate(value: Any) -> None:
        if isinstance(value, str):
            candidate = value.strip()
            if candidate and not _is_placeholder_value(candidate):
                normalized.append(candidate)
            return
        if isinstance(value, dict):
            for key in ("point", "text", "summary", "content", "description", "title"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip() and not _is_placeholder_value(candidate):
                    normalized.append(candidate.strip())
                    return
            return

    if isinstance(raw_points, str):
        for part in re.split(r"[\n;]+", raw_points):
            _add_candidate(part)
    elif isinstance(raw_points, list):
        for item in raw_points:
            _add_candidate(item)
    elif isinstance(raw_points, dict):
        _add_candidate(raw_points)

    deduped: List[str] = []
    seen = set()
    for item in normalized:
        cleaned = re.sub(r"^[-*•\d.\)\s]+", "", item).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped


def _normalize_label_list(raw_values: Any, max_items: int = 10) -> List[str]:
    values: List[str] = []
    if isinstance(raw_values, str):
        values = [v.strip() for v in re.split(r"[,\n;]+", raw_values) if v.strip()]
    elif isinstance(raw_values, list):
        for item in raw_values:
            if isinstance(item, str) and item.strip():
                values.append(item.strip())
            elif isinstance(item, dict):
                for key in ("keyword", "topic", "label", "name", "title", "text", "point"):
                    candidate = item.get(key)
                    if isinstance(candidate, str) and candidate.strip():
                        values.append(candidate.strip())
                        break

    deduped: List[str] = []
    seen = set()
    for value in values:
        cleaned = re.sub(r"^[-*•\d.\)\s]+", "", value).strip()
        if len(cleaned) < 2 or _is_placeholder_value(cleaned):
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
        if len(deduped) >= max_items:
            break
    return deduped


def _derive_keywords(summary: str, key_points: List[str], max_items: int = 8) -> List[str]:
    corpus = " ".join([str(summary or ""), *(key_points or [])]).lower()
    if not corpus.strip():
        return []

    stopwords = {
        "the", "and", "with", "from", "this", "that", "have", "been", "were", "into", "about",
        "summary", "key", "point", "points", "meeting", "session", "evidence", "timestamp",
        "của", "và", "là", "cho", "với", "những", "được", "trong", "một", "nhiều", "nội", "dung",
        "không", "theo", "các", "đã", "đang", "về", "để", "cần", "từ", "sẽ", "việc", "quyết", "định",
    }
    freq: Dict[str, int] = {}
    for token in re.findall(r"[0-9A-Za-zÀ-ỹà-ỹ]{3,}", corpus, flags=re.UNICODE):
        cleaned = token.strip().lower()
        if cleaned in stopwords:
            continue
        freq[cleaned] = freq.get(cleaned, 0) + 1

    ranked = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return [word for word, _count in ranked[:max_items]]


def _derive_topics(
    key_points: List[str],
    topic_tracker: List[Dict[str, Any]],
    keywords: List[str],
    max_items: int = 8,
) -> List[str]:
    topics: List[str] = []

    for row in topic_tracker or []:
        title = str(row.get("title") or "").strip()
        if title and not _is_placeholder_value(title):
            topics.append(title)

    for point in key_points or []:
        cleaned = re.sub(r"^[-*•\d.\)\s]+", "", str(point)).strip()
        if not cleaned:
            continue
        sentence = re.split(r"[.;!?]", cleaned)[0].strip()
        if not sentence:
            continue
        words = sentence.split()
        if len(words) <= 1:
            continue
        topics.append(" ".join(words[: min(len(words), 6)]))

    topics.extend(keywords or [])

    deduped: List[str] = []
    seen = set()
    for topic in topics:
        cleaned = re.sub(r"\s+", " ", str(topic or "").strip())
        if len(cleaned) < 2 or _is_placeholder_value(cleaned):
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
        if len(deduped) >= max_items:
            break
    return deduped


def _word_count(text_value: str) -> int:
    if not text_value:
        return 0
    return len(re.findall(r"[0-9A-Za-zÀ-ỹà-ỹ]+", text_value, flags=re.UNICODE))


def _join_preview(values: List[str], limit: int = 4) -> str:
    cleaned = [str(item).strip() for item in values if str(item).strip()]
    return "; ".join(cleaned[:limit])


def _expand_summary_if_needed(
    summary: str,
    meeting_title: str,
    meeting_desc: str,
    key_points: List[str],
    action_rows: List[Dict[str, Any]],
    decision_rows: List[Dict[str, Any]],
    risk_rows: List[Dict[str, Any]],
    next_steps: List[str],
    topic_tracker: List[Dict[str, Any]],
    transcript_excerpt: str = "",
) -> str:
    base_summary = str(summary or "").strip()
    if _word_count(base_summary) >= 140:
        return base_summary

    prefer_vi = _prefer_vietnamese_output()
    paragraphs: List[str] = []
    if base_summary:
        paragraphs.append(base_summary)
    elif meeting_desc:
        if prefer_vi:
            paragraphs.append(
                f"Cuộc họp '{meeting_title}' tập trung vào nội dung: {meeting_desc[:420].strip()}."
            )
        else:
            paragraphs.append(
                f"The meeting '{meeting_title}' focused on: {meeting_desc[:420].strip()}."
            )
    else:
        if prefer_vi:
            paragraphs.append(
                f"Cuộc họp '{meeting_title}' đã được ghi nhận và cần biên bản chi tiết để theo dõi tiến độ."
            )
        else:
            paragraphs.append(
                f"The meeting '{meeting_title}' was captured and requires detailed minutes for follow-up."
            )

    key_points_preview = _join_preview(key_points, 5)
    if key_points_preview:
        if prefer_vi:
            paragraphs.append(
                "Các điểm thảo luận trọng tâm gồm: "
                + key_points_preview
                + ". Nội dung cho thấy các bên đã làm rõ vấn đề, phạm vi ảnh hưởng và hướng xử lý ưu tiên."
            )
        else:
            paragraphs.append(
                "Core discussion points included: "
                + key_points_preview
                + ". The flow clarified scope, impact, and priority handling direction."
            )

    if decision_rows:
        decision_preview = _join_preview(
            [str(row.get("description") or "").strip() for row in decision_rows],
            3,
        )
        if prefer_vi:
            paragraphs.append(
                f"Đã ghi nhận {len(decision_rows)} quyết định. "
                + (f"Các quyết định đáng chú ý: {decision_preview}. " if decision_preview else "")
                + "Các quyết định này là căn cứ để triển khai kế hoạch và phân quyền thực thi."
            )
        else:
            paragraphs.append(
                f"{len(decision_rows)} decision(s) were captured. "
                + (f"Notable decisions: {decision_preview}. " if decision_preview else "")
                + "These decisions establish the execution baseline and ownership boundaries."
            )

    if action_rows:
        action_preview = _join_preview(
            [
                f"{str(row.get('description') or '').strip()} (owner: {str(row.get('owner') or 'N/A').strip()})"
                for row in action_rows
                if str(row.get("description") or "").strip()
            ],
            3,
        )
        if prefer_vi:
            paragraphs.append(
                f"Đã tổng hợp {len(action_rows)} đầu việc cần theo dõi. "
                + (f"Một số đầu việc tiêu biểu: {action_preview}. " if action_preview else "")
                + "Cần rà soát deadline và trạng thái định kỳ để đảm bảo tiến độ cam kết."
            )
        else:
            paragraphs.append(
                f"{len(action_rows)} action item(s) were consolidated. "
                + (f"Representative items: {action_preview}. " if action_preview else "")
                + "Deadlines and status should be reviewed on a recurring cadence."
            )

    if risk_rows:
        risk_preview = _join_preview(
            [str(row.get("description") or "").strip() for row in risk_rows],
            3,
        )
        if prefer_vi:
            paragraphs.append(
                f"Đã phát hiện {len(risk_rows)} rủi ro/vướng mắc. "
                + (f"Các rủi ro chính: {risk_preview}. " if risk_preview else "")
                + "Đề xuất theo dõi mức độ ảnh hưởng và kế hoạch giảm thiểu theo từng mốc."
            )
        else:
            paragraphs.append(
                f"{len(risk_rows)} risk(s)/blockers were identified. "
                + (f"Primary risks: {risk_preview}. " if risk_preview else "")
                + "Impact levels and mitigation plans should be tracked by milestone."
            )

    if next_steps:
        next_steps_preview = _join_preview(next_steps, 4)
        if prefer_vi:
            paragraphs.append(
                "Các bước tiếp theo đã được xác định: "
                + next_steps_preview
                + ". Cần chốt người phụ trách và thời hạn cụ thể cho từng hạng mục."
            )
        else:
            paragraphs.append(
                "Next steps were identified: "
                + next_steps_preview
                + ". Owners and concrete due dates should be finalized per item."
            )

    if topic_tracker:
        if prefer_vi:
            paragraphs.append(
                f"Phiên họp ghi nhận {len(topic_tracker)} cụm chủ đề theo timeline, hỗ trợ truy vết nhanh nội dung và quyết định."
            )
        else:
            paragraphs.append(
                f"The session tracked {len(topic_tracker)} topic clusters on the timeline for better traceability."
            )

    if transcript_excerpt and _word_count("\n\n".join(paragraphs)) < 120:
        snippet = transcript_excerpt[:520].replace("\n", " ").strip()
        if snippet:
            if prefer_vi:
                paragraphs.append(
                    "Bằng chứng transcript tiêu biểu: " + snippet + "."
                )
            else:
                paragraphs.append(
                    "Representative transcript evidence: " + snippet + "."
                )

    return "\n\n".join([item for item in paragraphs if item.strip()]).strip()


def list_minutes(db: Session, meeting_id: str) -> MeetingMinutesList:
    """List all minutes versions for a meeting"""
    _ensure_minutes_tables(db)
    query = text("""
        SELECT 
            id::text, meeting_id::text, version, minutes_text,
            minutes_html, minutes_markdown, minutes_doc_url,
            executive_summary, generated_at, edited_by::text,
            edited_at, status, approved_by::text, approved_at
        FROM meeting_minutes
        WHERE meeting_id = :meeting_id
        ORDER BY version DESC
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    minutes_list = []
    for row in rows:
        minutes_list.append(_hydrate_minutes_html(MeetingMinutesResponse(
            id=row[0],
            meeting_id=row[1],
            version=row[2],
            minutes_text=row[3],
            minutes_html=row[4],
            minutes_markdown=row[5],
            minutes_doc_url=row[6],
            executive_summary=row[7],
            generated_at=row[8],
            edited_by=row[9],
            edited_at=row[10],
            status=row[11],
            approved_by=row[12],
            approved_at=row[13]
        )))
    
    return MeetingMinutesList(minutes=minutes_list, total=len(minutes_list))


def get_latest_minutes(db: Session, meeting_id: str) -> Optional[MeetingMinutesResponse]:
    """Get the latest minutes for a meeting"""
    _ensure_minutes_tables(db)
    query = text("""
        SELECT 
            id::text, meeting_id::text, version, minutes_text,
            minutes_html, minutes_markdown, minutes_doc_url,
            executive_summary, generated_at, edited_by::text,
            edited_at, status, approved_by::text, approved_at
        FROM meeting_minutes
        WHERE meeting_id = :meeting_id
        ORDER BY version DESC
        LIMIT 1
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    return _hydrate_minutes_html(MeetingMinutesResponse(
        id=row[0],
        meeting_id=row[1],
        version=row[2],
        minutes_text=row[3],
        minutes_html=row[4],
        minutes_markdown=row[5],
        minutes_doc_url=row[6],
        executive_summary=row[7],
        generated_at=row[8],
        edited_by=row[9],
        edited_at=row[10],
        status=row[11],
        approved_by=row[12],
        approved_at=row[13]
    ))


def get_minutes_by_id(db: Session, minutes_id: str) -> Optional[MeetingMinutesResponse]:
    """Get minutes by ID (hydrated with rendered HTML if only markdown exists)."""
    _ensure_minutes_tables(db)
    query = text("""
        SELECT 
            id::text, meeting_id::text, version, minutes_text,
            minutes_html, minutes_markdown, minutes_doc_url,
            executive_summary, generated_at, edited_by::text,
            edited_at, status, approved_by::text, approved_at
        FROM meeting_minutes
        WHERE id = :minutes_id
        LIMIT 1
    """)
    row = db.execute(query, {'minutes_id': minutes_id}).fetchone()
    if not row:
        return None

    return _hydrate_minutes_html(MeetingMinutesResponse(
        id=row[0],
        meeting_id=row[1],
        version=row[2],
        minutes_text=row[3],
        minutes_html=row[4],
        minutes_markdown=row[5],
        minutes_doc_url=row[6],
        executive_summary=row[7],
        generated_at=row[8],
        edited_by=row[9],
        edited_at=row[10],
        status=row[11],
        approved_by=row[12],
        approved_at=row[13]
    ))


def render_minutes_html_content(minutes: MeetingMinutesResponse) -> str:
    """
    Render minutes into HTML for export/viewing, preferring stored HTML,
    otherwise converting markdown, otherwise wrapping plain text.
    """
    if minutes.minutes_html and not _looks_like_markdown(minutes.minutes_html):
        return minutes.minutes_html

    # Prefer markdown if available
    source_md = minutes.minutes_markdown or (minutes.minutes_html if _looks_like_markdown(minutes.minutes_html) else None)
    if source_md:
        return render_markdown_to_html(source_md)
    if minutes.minutes_text:
        from html import escape
        return f"<pre style=\"white-space: pre-wrap; font-family: sans-serif;\">{escape(minutes.minutes_text)}</pre>"
    return "<p>Chưa có nội dung biên bản.</p>"


def render_minutes_full_page(db: Session, minutes_id: str) -> str:
    """
    Build a styled HTML page for export/print, including meta info.
    """
    minutes = get_minutes_by_id(db, minutes_id)
    if not minutes:
        raise ValueError("Minutes not found")

    meeting = meeting_service.get_meeting(db, minutes.meeting_id)
    participants = participant_service.list_participants(db, minutes.meeting_id) if meeting else None

    title = meeting.title if meeting else "Biên bản cuộc họp"
    start = getattr(meeting, "start_time", None)
    end = getattr(meeting, "end_time", None)
    def _fmt_time(dt):
        if not dt:
            return ""
        if isinstance(dt, str):
            try:
                from datetime import datetime
                return datetime.fromisoformat(dt.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
            except Exception:
                return dt
        if getattr(dt, "tzinfo", None) is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M")

    date_str = _fmt_time(start).split(" ")[0] if start else ""
    time_str = ""
    if start and end:
        time_str = f"{_fmt_time(start).split(' ')[1]} - {_fmt_time(end).split(' ')[1]}"
    elif start:
        time_str = _fmt_time(start)

    participants_names = ""
    if participants and participants.participants:
        names = []
        for p in participants.participants:
            name = p.display_name or p.email or "Thành viên"
            names.append(name)
        participants_names = ", ".join(names)

    template_path = Path(__file__).parent.parent / "templates" / "minutes_export.html"
    template_html = template_path.read_text(encoding="utf-8")

    content_html = render_minutes_html_content(minutes)
    exec_summary_html = minutes.executive_summary or (
        "<p>Chưa có tóm tắt.</p>" if _prefer_vietnamese_output() else "<p>No summary available.</p>"
    )

    filled = (
        template_html
        .replace("{{title}}", title)
        .replace("{{date}}", date_str or "N/A")
        .replace("{{time}}", time_str or "N/A")
        .replace("{{type}}", getattr(meeting, "meeting_type", "") if meeting else "")
        .replace("{{participants}}", participants_names or "N/A")
        .replace("{{executive_summary}}", exec_summary_html if exec_summary_html.startswith("<") else f"<p>{exec_summary_html}</p>")
        .replace("{{minutes_content}}", content_html)
    )
    return filled


def create_minutes(db: Session, data: MeetingMinutesCreate) -> MeetingMinutesResponse:
    """Create new meeting minutes"""
    _ensure_minutes_tables(db)
    minutes_id = str(uuid4())
    now = datetime.utcnow()
    rendered_html = None
    if data.minutes_markdown and not data.minutes_html:
        rendered_html = render_markdown_to_html(data.minutes_markdown)
    
    # Get next version number
    version_query = text("""
        SELECT COALESCE(MAX(version), 0) + 1
        FROM meeting_minutes
        WHERE meeting_id = :meeting_id
    """)
    version_result = db.execute(version_query, {'meeting_id': data.meeting_id})
    version = version_result.fetchone()[0]
    
    query = text("""
        INSERT INTO meeting_minutes (
            id, meeting_id, version, minutes_text, minutes_html,
            minutes_markdown, executive_summary, status, generated_at
        )
        VALUES (
            :id, :meeting_id, :version, :minutes_text, :minutes_html,
            :minutes_markdown, :executive_summary, :status, :generated_at
        )
        RETURNING id::text
    """)
    
    db.execute(query, {
        'id': minutes_id,
        'meeting_id': data.meeting_id,
        'version': version,
        'minutes_text': data.minutes_text,
        'minutes_html': data.minutes_html or rendered_html,
        'minutes_markdown': data.minutes_markdown,
        'executive_summary': data.executive_summary,
        'status': data.status,
        'generated_at': now
    })
    db.commit()

    if data.executive_summary and str(data.executive_summary).strip():
        try:
            from app.services.summary_service import create_summary
            create_summary(
                db,
                meeting_id=str(data.meeting_id),
                content=str(data.executive_summary),
                summary_type="minutes_executive",
                artifacts={"minutes_id": minutes_id, "source": "meeting_minutes"},
            )
        except Exception as exc:
            logger.warning("Failed to persist executive summary for meeting %s: %s", data.meeting_id, exc)
            db.rollback()
    
    return MeetingMinutesResponse(
        id=minutes_id,
        meeting_id=data.meeting_id,
        version=version,
        minutes_text=data.minutes_text,
        minutes_html=data.minutes_html or rendered_html,
        minutes_markdown=data.minutes_markdown,
        executive_summary=data.executive_summary,
        status=data.status,
        generated_at=now
    )


def update_minutes(
    db: Session, 
    minutes_id: str, 
    data: MeetingMinutesUpdate,
    edited_by: Optional[str] = None
) -> Optional[MeetingMinutesResponse]:
    """Update meeting minutes"""
    updates = ["edited_at = :edited_at"]
    params = {'minutes_id': minutes_id, 'edited_at': datetime.utcnow()}
    rendered_html = None
    if data.minutes_markdown is not None:
        rendered_html = render_markdown_to_html(data.minutes_markdown)
    
    if edited_by:
        updates.append("edited_by = :edited_by")
        params['edited_by'] = edited_by
    
    if data.minutes_text is not None:
        updates.append("minutes_text = :minutes_text")
        params['minutes_text'] = data.minutes_text
    if data.minutes_html is not None:
        updates.append("minutes_html = :minutes_html")
        params['minutes_html'] = data.minutes_html
    elif rendered_html is not None:
        updates.append("minutes_html = :minutes_html")
        params['minutes_html'] = rendered_html
    if data.minutes_markdown is not None:
        updates.append("minutes_markdown = :minutes_markdown")
        params['minutes_markdown'] = data.minutes_markdown
    if data.executive_summary is not None:
        updates.append("executive_summary = :executive_summary")
        params['executive_summary'] = data.executive_summary
    if data.status is not None:
        updates.append("status = :status")
        params['status'] = data.status
    
    query = text(f"""
        UPDATE meeting_minutes
        SET {', '.join(updates)}
        WHERE id = :minutes_id
        RETURNING id::text, meeting_id::text
    """)
    
    result = db.execute(query, params)
    db.commit()
    row = result.fetchone()
    
    if not row:
        return None

    if data.executive_summary is not None and str(data.executive_summary).strip():
        try:
            from app.services.summary_service import create_summary
            create_summary(
                db,
                meeting_id=row[1],
                content=str(data.executive_summary),
                summary_type="minutes_executive",
                artifacts={"minutes_id": minutes_id, "source": "meeting_minutes_update"},
            )
        except Exception as exc:
            logger.warning("Failed to persist updated executive summary for meeting %s: %s", row[1], exc)
            db.rollback()
    
    return get_latest_minutes(db, row[1])


def approve_minutes(
    db: Session, 
    minutes_id: str, 
    approved_by: str
) -> Optional[MeetingMinutesResponse]:
    """Approve meeting minutes"""
    now = datetime.utcnow()
    
    query = text("""
        UPDATE meeting_minutes
        SET status = 'approved', approved_by = :approved_by, approved_at = :approved_at
        WHERE id = :minutes_id
        RETURNING id::text, meeting_id::text
    """)
    
    result = db.execute(query, {
        'minutes_id': minutes_id,
        'approved_by': approved_by,
        'approved_at': now
    })
    db.commit()
    row = result.fetchone()
    
    if not row:
        return None
    
    return get_latest_minutes(db, row[1])


# ============================================
# AI-Powered Minutes Generation
# ============================================

async def generate_minutes_with_ai(
    db: Session,
    request: GenerateMinutesRequest,
    user_id: Optional[str] = None,
) -> MeetingMinutesResponse:
    """Generate minutes with two prompt strategies and feature-specific sections."""
    from app.llm.gemini_client import MeetingAIAssistant
    from app.services import template_formatter

    meeting_id = request.meeting_id

    meeting_query = text(
        """
        SELECT title, meeting_type, description, start_time, end_time, organizer_id
        FROM meeting WHERE id = :meeting_id
        """
    )
    meeting_result = db.execute(meeting_query, {"meeting_id": meeting_id})
    meeting_row = meeting_result.fetchone()

    if not meeting_row:
        raise ValueError(f"Meeting {meeting_id} not found")

    meeting_title = meeting_row[0]
    meeting_type = meeting_row[1]
    meeting_desc = meeting_row[2]
    start_time = meeting_row[3]
    end_time = meeting_row[4]
    organizer_id = meeting_row[5]

    prompt_strategy = (request.prompt_strategy or "context_json").strip().lower()
    if prompt_strategy not in {"context_json", "structured_json"}:
        prompt_strategy = "context_json"
    session_type = _infer_session_type(meeting_type, request.session_type)

    transcript = ""
    if request.include_transcript:
        try:
            transcript = transcript_service.get_full_transcript(db, meeting_id)
        except Exception as exc:
            logger.warning("Failed to fetch transcript for meeting %s: %s", meeting_id, exc)
            db.rollback()
            transcript = ""

    action_rows: List[Dict[str, Any]] = []
    if request.include_actions:
        try:
            action_list = action_item_service.list_action_items(db, meeting_id)
            for item in action_list.items:
                deadline = item.deadline.isoformat() if item.deadline else ""
                action_rows.append(
                    {
                        "description": (item.description or "").strip(),
                        "owner": (item.owner_name or item.owner_user_id or "").strip(),
                        "deadline": deadline,
                        "priority": (item.priority or "").strip(),
                        "status": (item.status or "").strip(),
                    }
                )
        except Exception as exc:
            logger.warning("Failed to fetch action items for meeting %s: %s", meeting_id, exc)
            db.rollback()
            action_rows = []

    decision_rows: List[Dict[str, Any]] = []
    if request.include_decisions:
        try:
            decision_list = action_item_service.list_decision_items(db, meeting_id)
            for item in decision_list.items:
                confirmed_by = item.confirmed_by or ""
                decision_rows.append(
                    {
                        "description": (item.description or "").strip(),
                        "rationale": (item.rationale or "").strip(),
                        "status": (item.status or "").strip(),
                        "confirmed_by": str(confirmed_by).strip(),
                    }
                )
        except Exception as exc:
            logger.warning("Failed to fetch decisions for meeting %s: %s", meeting_id, exc)
            db.rollback()
            decision_rows = []

    risk_rows: List[Dict[str, Any]] = []
    if request.include_risks:
        try:
            risk_list = action_item_service.list_risk_items(db, meeting_id)
            for item in risk_list.items:
                risk_rows.append(
                    {
                        "description": (item.description or "").strip(),
                        "severity": (item.severity or "").strip(),
                        "mitigation": (item.mitigation or "").strip(),
                        "status": (item.status or "").strip(),
                        "owner": (item.owner_name or item.owner_user_id or "").strip(),
                    }
                )
        except Exception as exc:
            logger.warning("Failed to fetch risks for meeting %s: %s", meeting_id, exc)
            db.rollback()
            risk_rows = []

    actions = [row.get("description", "") for row in action_rows if row.get("description")]
    decisions = [row.get("description", "") for row in decision_rows if row.get("description")]
    risks = [
        f"{row.get('description', '')} (Severity: {row.get('severity') or 'unknown'})"
        for row in risk_rows
        if row.get("description")
    ]

    related_docs: List[str] = []
    try:
        doc_rows = db.execute(
            text(
                """
                SELECT title, description, file_type
                FROM knowledge_document
                WHERE meeting_id = :meeting_id
                ORDER BY created_at DESC
                LIMIT 10
                """
            ),
            {"meeting_id": meeting_id},
        ).fetchall()
        related_docs = [f"{r[0]} ({r[2]}) - {r[1] or ''}".strip() for r in doc_rows]
    except Exception as exc:
        logger.warning("Failed to fetch related documents for meeting %s: %s", meeting_id, exc)
        db.rollback()
        related_docs = []

    topic_tracker: List[Dict[str, Any]] = []
    if request.include_topic_tracker:
        try:
            topic_tracker = _load_topic_tracker(db, meeting_id)
        except Exception as exc:
            logger.warning("Failed to fetch topic tracker for meeting %s: %s", meeting_id, exc)
            db.rollback()
            topic_tracker = []

    visual_highlights = _load_visual_highlights(db, meeting_id)

    transcript_for_llm = transcript or ""
    if transcript_for_llm and len(transcript_for_llm) > MAX_DIRECT_TRANSCRIPT_CHARS:
        llm_fallback_transcript = transcript_for_llm[:MAX_DIRECT_TRANSCRIPT_CHARS]
    else:
        llm_fallback_transcript = transcript_for_llm

    context_payload = {
        "title": meeting_title,
        "type": meeting_type,
        "description": meeting_desc,
        "time": f"{start_time} - {end_time}",
        "transcript": llm_fallback_transcript,
        "actions": actions,
        "decisions": decisions,
        "risks": risks,
        "documents": related_docs,
        "visual_context": visual_highlights,
        "study_pack": None,
        "topic_tracker": topic_tracker,
        "session_type": session_type,
    }

    llm_config = None
    runtime_candidates: List[str] = []
    for candidate in (organizer_id, user_id, "00000000-0000-0000-0000-000000000001"):
        normalized = str(candidate or "").strip()
        if not normalized or normalized in runtime_candidates:
            continue
        runtime_candidates.append(normalized)

    try:
        from app.services import user_service
        from app.llm.gemini_client import LLMConfig
        for candidate in runtime_candidates:
            override = user_service.get_user_llm_override(
                db,
                candidate,
                allow_demo_fallback=(candidate == "00000000-0000-0000-0000-000000000001"),
            )
            if not override:
                continue
            llm_config = LLMConfig(**override)
            logger.info(
                "Using runtime LLM settings for minutes meeting_id=%s user_id=%s provider=%s model=%s",
                meeting_id,
                candidate,
                llm_config.provider,
                llm_config.model,
            )
            break
    except Exception as exc:
        logger.warning(
            "Failed to load runtime LLM settings for meeting_id=%s organizer_id=%s user_id=%s: %s",
            meeting_id,
            organizer_id,
            user_id,
            exc,
        )
        db.rollback()
    if not llm_config:
        logger.info(
            "No user-specific LLM override found for meeting_id=%s organizer_id=%s user_id=%s. Falling back to environment defaults.",
            meeting_id,
            organizer_id,
            user_id,
        )

    assistant = MeetingAIAssistant(
        meeting_id,
        {
            'title': meeting_title,
            'type': meeting_type,
            'description': meeting_desc
        },
        llm_config=llm_config,
    )

    summary_result: Dict[str, Any] = {"summary": "", "key_points": []}
    study_pack: Optional[Dict[str, Any]] = None
    next_steps: List[str] = []
    structured_payload: Dict[str, Any] = {}
    keywords: List[str] = []
    topics: List[str] = []

    def _parse_json_fragment(raw_text: str, expect_array: bool = False):
        try:
            parsed = json.loads(raw_text)
            if expect_array and isinstance(parsed, list):
                return parsed
            if not expect_array and isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        pattern = r"\[[\s\S]*\]" if expect_array else r"\{[\s\S]*\}"
        match = re.search(pattern, raw_text or "")
        if not match:
            return [] if expect_array else {}
        try:
            parsed = json.loads(match.group(0))
            if expect_array and isinstance(parsed, list):
                return parsed
            if not expect_array and isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return [] if expect_array else {}

    def _normalize_rows_from_llm(raw_rows: Any, row_type: str) -> List[Dict[str, Any]]:
        rows = _safe_json_list(raw_rows)
        normalized: List[Dict[str, Any]] = []
        for row in rows:
            if row_type == "action":
                normalized.append(
                    {
                        "description": str(row.get("description") or row.get("task") or "").strip(),
                        "owner": str(row.get("owner") or row.get("created_by") or "Unassigned").strip(),
                        "deadline": str(row.get("deadline") or "").strip(),
                        "priority": str(row.get("priority") or "medium").strip(),
                        "status": str(row.get("status") or "proposed").strip(),
                    }
                )
            elif row_type == "decision":
                normalized.append(
                    {
                        "description": str(row.get("description") or row.get("title") or "").strip(),
                        "rationale": str(row.get("rationale") or "").strip(),
                        "status": str(row.get("status") or "proposed").strip(),
                        "confirmed_by": str(row.get("approved_by") or row.get("decided_by") or "").strip(),
                    }
                )
            elif row_type == "risk":
                normalized.append(
                    {
                        "description": str(row.get("description") or row.get("risk") or "").strip(),
                        "severity": str(row.get("severity") or "medium").strip(),
                        "mitigation": str(row.get("mitigation") or "").strip(),
                        "status": str(row.get("status") or "proposed").strip(),
                        "owner": str(row.get("raised_by") or row.get("owner") or "").strip(),
                    }
                )
        def _is_valid_row(row: Dict[str, Any]) -> bool:
            desc = str(row.get("description") or "").strip()
            if not desc or _is_placeholder_value(desc):
                return False
            if row_type == "risk":
                lowered = desc.lower()
                if any(
                    marker in lowered
                    for marker in (
                        "no risk",
                        "không có rủi ro",
                        "khong co rui ro",
                        "no issue",
                        "không có vấn đề",
                        "khong co van de",
                    )
                ):
                    return False
            return True

        return [r for r in normalized if _is_valid_row(r)]

    def _normalize_study_pack(raw_study: Any) -> Optional[Dict[str, Any]]:
        if isinstance(raw_study, str):
            raw_study = _parse_json_fragment(raw_study, expect_array=False)
        if not isinstance(raw_study, dict):
            return None
        concepts_raw = raw_study.get("concepts")
        formulas_raw = (
            raw_study.get("formulas")
            or raw_study.get("important_formulas")
            or raw_study.get("key_formulas")
        )
        quiz_raw = raw_study.get("quiz") or raw_study.get("quizzes") or raw_study.get("questions")

        concepts = _safe_json_list(concepts_raw)
        if not concepts and isinstance(concepts_raw, list):
            concepts = [
                {"concept": str(item).strip(), "explanation": "", "example": ""}
                for item in concepts_raw
                if str(item).strip()
            ]

        formulas = _safe_json_list(formulas_raw)
        if not formulas and isinstance(formulas_raw, list):
            formulas = [
                {"name": str(item).strip(), "formula": str(item).strip(), "meaning": "", "usage": ""}
                for item in formulas_raw
                if str(item).strip()
            ]

        quiz = _safe_json_list(quiz_raw)
        if not quiz and isinstance(quiz_raw, list):
            quiz = [
                {"question": str(item).strip(), "options": [], "answer": "", "explanation": ""}
                for item in quiz_raw
                if str(item).strip()
            ]

        return {
            "concepts": concepts,
            "formulas": formulas,
            "quiz": quiz,
        }

    if transcript_for_llm and len(transcript_for_llm) > MAX_DIRECT_TRANSCRIPT_CHARS:
        window_summaries = await _summarize_transcript_windows(assistant, transcript_for_llm)
        if window_summaries:
            context_payload["transcript"] = "\n\n".join(
                [f"[Window {idx + 1}] {entry}" for idx, entry in enumerate(window_summaries)]
            )

    try:
        if prompt_strategy == "structured_json" and transcript:
            structured_payload = await assistant.generate_minutes_json(
                transcript,
                session_type=session_type,
            )
            summary_result = {
                "summary": str(structured_payload.get("executive_summary") or "").strip(),
                "key_points": _normalize_key_points(structured_payload.get("key_points")),
            }
            keywords = _normalize_label_list(structured_payload.get("keywords"), max_items=10)
            topics = _normalize_label_list(structured_payload.get("topics"), max_items=10)
            if request.include_actions and not action_rows:
                action_rows = _normalize_rows_from_llm(structured_payload.get("action_items"), "action")
            if request.include_decisions and not decision_rows:
                decision_rows = _normalize_rows_from_llm(structured_payload.get("decisions"), "decision")
            if request.include_risks and not risk_rows:
                risk_rows = _normalize_rows_from_llm(structured_payload.get("risks"), "risk")
            if isinstance(structured_payload.get("next_steps"), list):
                next_steps = [str(item).strip() for item in structured_payload.get("next_steps", []) if str(item).strip()]
            if session_type == "course":
                raw_study_payload = structured_payload.get("study_pack")
                if not isinstance(raw_study_payload, dict):
                    raw_study_payload = {
                        "concepts": structured_payload.get("concepts"),
                        "formulas": structured_payload.get("formulas"),
                        "quiz": (
                            structured_payload.get("quiz")
                            or structured_payload.get("quizzes")
                            or structured_payload.get("questions")
                        ),
                    }
                study_pack = _normalize_study_pack(raw_study_payload)
        else:
            summary_result = await assistant.generate_summary_with_context(context_payload)
    except Exception as exc:
        logger.warning("AI summary generation failed for meeting %s: %s", meeting_id, exc)
        prefer_vi = _prefer_vietnamese_output()
        fallback_summary = (
            meeting_desc
            or (
                "Chưa có mô tả cuộc họp. Vui lòng bổ sung ngữ cảnh để tạo tóm tắt đầy đủ hơn."
                if prefer_vi
                else "No meeting description is available yet. Please add context for a richer summary."
            )
        )
        summary_result = {
            "summary": fallback_summary,
            "key_points": actions[:3] if actions else decisions[:3],
        }

    if isinstance(summary_result, str):
        summary_result = {"summary": summary_result, "key_points": []}
    elif not isinstance(summary_result, dict):
        summary_result = {"summary": str(summary_result), "key_points": []}
    else:
        summary_result = {
            "summary": summary_result.get("summary", ""),
            "key_points": summary_result.get("key_points", []),
        }
    summary_result["key_points"] = _normalize_key_points(summary_result.get("key_points"))

    raw_summary_text = str(summary_result.get("summary", "") or "").strip()
    extracted_summary_text, extracted_key_points = _extract_embedded_summary_payload(raw_summary_text)
    summary_result["summary"] = extracted_summary_text or _decode_jsonish_text(raw_summary_text)
    if extracted_key_points and not summary_result.get("key_points"):
        summary_result["key_points"] = _normalize_key_points(extracted_key_points)
    if not summary_result["summary"]:
        prefer_vi = _prefer_vietnamese_output()
        if meeting_desc:
            if prefer_vi:
                summary_result["summary"] = (
                    f"Tóm tắt sơ bộ cho '{meeting_title}': {meeting_desc[:360]}. "
                    "Vui lòng bổ sung transcript để tạo biên bản sâu và đáng tin cậy hơn."
                )
            else:
                summary_result["summary"] = (
                    f"Preliminary summary for '{meeting_title}': {meeting_desc[:360]}. "
                    "Add transcript evidence for deeper and more reliable minutes."
                )
        elif llm_fallback_transcript:
            if prefer_vi:
                summary_result["summary"] = (
                    f"Tóm tắt sơ bộ cho '{meeting_title}': {llm_fallback_transcript[:420]}. "
                    "Bản nháp này nên được tinh chỉnh bằng transcript đầy đủ."
                )
            else:
                summary_result["summary"] = (
                    f"Preliminary summary for '{meeting_title}': {llm_fallback_transcript[:420]}. "
                    "This draft should be refined with full transcript context."
                )
        elif related_docs:
            if prefer_vi:
                summary_result["summary"] = (
                    f"Tóm tắt sơ bộ cho '{meeting_title}': đã có tài liệu liên quan. "
                    "Vui lòng bổ sung dữ liệu transcript để tạo biên bản chi tiết."
                )
            else:
                summary_result["summary"] = (
                    f"Preliminary summary for '{meeting_title}': related documents are available. "
                    "Please add transcript data to generate detailed minutes."
                )
        else:
            if prefer_vi:
                summary_result["summary"] = (
                    f"Tóm tắt sơ bộ cho '{meeting_title}': phiên họp đã được ghi nhận, "
                    "nhưng bằng chứng nội dung hiện còn hạn chế."
                )
            else:
                summary_result["summary"] = (
                    f"Preliminary summary for '{meeting_title}': this session is recorded, "
                    "but content evidence is currently limited."
                )
    if not summary_result["key_points"]:
        fallback_points: List[str] = []
        prefer_vi = _prefer_vietnamese_output()
        if action_rows:
            if prefer_vi:
                fallback_points.append(f"Đã ghi nhận {len(action_rows)} đầu việc.")
            else:
                fallback_points.append(f"{len(action_rows)} action item(s) were captured.")
        if decision_rows:
            if prefer_vi:
                fallback_points.append(f"Đã ghi nhận {len(decision_rows)} quyết định.")
            else:
                fallback_points.append(f"{len(decision_rows)} decision(s) were captured.")
        if risk_rows:
            if prefer_vi:
                fallback_points.append(f"Đã ghi nhận {len(risk_rows)} rủi ro.")
            else:
                fallback_points.append(f"{len(risk_rows)} risk(s) were captured.")
        if related_docs:
            if prefer_vi:
                fallback_points.append(f"Có {len(related_docs)} tài liệu tham chiếu liên quan.")
            else:
                fallback_points.append(f"{len(related_docs)} reference document(s) are linked.")
        if not fallback_points:
            if prefer_vi:
                fallback_points.append("Vui lòng bổ sung transcript để tăng độ sâu và độ chính xác của tóm tắt.")
            else:
                fallback_points.append("Add transcript evidence to improve summary depth and accuracy.")
        summary_result["key_points"] = _normalize_key_points(fallback_points[:5])

    summary_result["summary"] = _expand_summary_if_needed(
        summary=str(summary_result.get("summary") or ""),
        meeting_title=str(meeting_title or ""),
        meeting_desc=str(meeting_desc or ""),
        key_points=summary_result["key_points"],
        action_rows=action_rows,
        decision_rows=decision_rows,
        risk_rows=risk_rows,
        next_steps=next_steps,
        topic_tracker=topic_tracker,
        transcript_excerpt=llm_fallback_transcript[:1200] if llm_fallback_transcript else "",
    )

    if not keywords:
        keywords = _derive_keywords(
            summary=str(summary_result.get("summary") or ""),
            key_points=summary_result.get("key_points") or [],
            max_items=8,
        )
    if not topics:
        topics = _derive_topics(
            key_points=summary_result.get("key_points") or [],
            topic_tracker=topic_tracker,
            keywords=keywords,
            max_items=8,
        )

    actions = [row.get("description", "") for row in action_rows if row.get("description")]
    decisions = [row.get("description", "") for row in decision_rows if row.get("description")]
    risks = [
        f"{row.get('description', '')} (Severity: {row.get('severity') or 'unknown'})"
        for row in risk_rows
        if row.get("description")
    ]

    if not next_steps:
        next_steps = actions[:3]

    ai_filters: List[str] = []
    if request.include_ai_filters and session_type == "meeting":
        ai_filters = _build_ai_filters(action_rows, decision_rows, risk_rows, topic_tracker)

    if request.template_id:
        context_payload["summary"] = summary_result.get("summary", "")
        context_payload["key_points"] = summary_result.get("key_points", [])
        context_payload["keywords"] = keywords
        context_payload["topics"] = topics
        context_payload["session_type"] = session_type
        context_payload["action_items"] = action_rows
        context_payload["decision_items"] = decision_rows
        context_payload["risk_items"] = risk_rows
        context_payload["next_steps"] = next_steps
        context_payload["topic_tracker"] = topic_tracker
        context_payload["visual_context"] = visual_highlights
        context_payload["ai_filters"] = ai_filters
        context_payload["study_pack"] = study_pack
        context_payload["prompt_strategy"] = prompt_strategy
        minutes_content = template_formatter.format_minutes_with_template(
            db=db,
            template_id=request.template_id,
            meeting_id=meeting_id,
            context=context_payload,
            format_type=request.format,
        )
    else:
        minutes_content = format_minutes(
            meeting_title=meeting_title,
            meeting_type=meeting_type,
            start_time=start_time,
            end_time=end_time,
            summary=summary_result.get("summary", ""),
            key_points=summary_result.get("key_points", []),
            keywords=keywords,
            topics=topics,
            session_type=session_type,
            actions=actions,
            decisions=decisions,
            risks=risks,
            action_rows=action_rows,
            decision_rows=decision_rows,
            risk_rows=risk_rows,
            next_steps=next_steps,
            study_pack=study_pack,
            topic_tracker=topic_tracker if request.include_topic_tracker else [],
            ai_filters=ai_filters if request.include_ai_filters else [],
            include_topic_tracker=request.include_topic_tracker,
            include_ai_filters=request.include_ai_filters,
            include_quiz=request.include_quiz,
            include_knowledge_table=request.include_knowledge_table,
            format_type=request.format,
        )

    minutes_html_value = minutes_content if request.format == "html" else None
    if request.format == "markdown":
        minutes_html_value = render_markdown_to_html(minutes_content)

    minutes_data = MeetingMinutesCreate(
        meeting_id=meeting_id,
        minutes_text=minutes_content if request.format == "text" else None,
        minutes_markdown=minutes_content if request.format == "markdown" else None,
        minutes_html=minutes_html_value,
        executive_summary=summary_result.get("summary", ""),
        status="draft",
    )

    return create_minutes(db, minutes_data)


def format_minutes(
    meeting_title: str,
    meeting_type: str,
    start_time,
    end_time,
    summary: str,
    key_points: List[str],
    keywords: List[str],
    topics: List[str],
    session_type: str,
    actions: List[str],
    decisions: List[str],
    risks: List[str],
    action_rows: Optional[List[Dict[str, Any]]] = None,
    decision_rows: Optional[List[Dict[str, Any]]] = None,
    risk_rows: Optional[List[Dict[str, Any]]] = None,
    next_steps: Optional[List[str]] = None,
    study_pack: Optional[Dict[str, Any]] = None,
    topic_tracker: Optional[List[Dict[str, Any]]] = None,
    ai_filters: Optional[List[str]] = None,
    include_topic_tracker: bool = True,
    include_ai_filters: bool = True,
    include_quiz: bool = False,
    include_knowledge_table: bool = False,
    format_type: str = "markdown",
) -> str:
    """Format session minutes as markdown-friendly text."""

    def _fmt_dt(value) -> str:
        if not value:
            return "N/A"
        if isinstance(value, str):
            return value
        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y %H:%M")
        return str(value)

    def _md_cell(value: Any) -> str:
        text_val = str(value or "").replace("|", "\\|").replace("\n", " ").strip()
        return text_val or "-"

    lines: List[str] = []
    lines.append(f"# Biên bản: {meeting_title}")
    lines.append("")

    action_rows = action_rows or []
    decision_rows = decision_rows or []
    risk_rows = risk_rows or []
    topic_tracker = topic_tracker or []
    ai_filters = ai_filters or []
    next_steps = next_steps or []
    key_points = [str(point).strip() for point in (key_points or []) if str(point).strip()]
    keywords = [str(keyword).strip() for keyword in (keywords or []) if str(keyword).strip()]
    topics = [str(topic).strip() for topic in (topics or []) if str(topic).strip()]
    summary_text = str(summary or "").strip()
    prefer_vi = _prefer_vietnamese_output()

    lines.append("## Thông tin cuộc họp")
    lines.append(f"- **Loại cuộc họp:** {meeting_type or 'N/A'}")
    lines.append(f"- **Chế độ phiên:** {session_type.title()}")
    lines.append(f"- **Thời gian:** {_fmt_dt(start_time)} - {_fmt_dt(end_time)}")
    lines.append("")

    lines.append("## Tóm tắt điều hành")
    if summary_text:
        lines.append(summary_text)
    else:
        lines.append(
            "_Chưa có tóm tắt điều hành._"
            if prefer_vi
            else "_No executive summary available._"
        )
    lines.append("")

    lines.append("## Các điểm chính")
    if key_points:
        for point in key_points:
            lines.append(f"- {point}")
    else:
        lines.append(
            "- Chưa có điểm chính được trích xuất."
            if prefer_vi
            else "- No key points extracted yet."
        )
    lines.append("")

    lines.append("## Từ khóa trọng tâm" if prefer_vi else "## Core keywords")
    if keywords:
        for keyword in keywords:
            lines.append(f"- {keyword}")
    else:
        lines.append(
            "- Chưa có từ khóa nổi bật."
            if prefer_vi
            else "- No notable keywords yet."
        )
    lines.append("")

    lines.append("## Chủ đề chính" if prefer_vi else "## Primary topics")
    if topics:
        for topic in topics:
            lines.append(f"- {topic}")
    else:
        lines.append(
            "- Chưa có chủ đề nổi bật."
            if prefer_vi
            else "- No primary topics available."
        )
    lines.append("")

    if session_type == "meeting":
        lines.append("## Quyết định")
        if decision_rows:
            lines.append("| Quyết định | Lý do | Trạng thái | Người xác nhận |")
            lines.append("| --- | --- | --- | --- |")
            for row in decision_rows:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("description")),
                            _md_cell(row.get("rationale")),
                            _md_cell(row.get("status")),
                            _md_cell(row.get("confirmed_by")),
                        ]
                    )
                    + " |"
                )
        elif decisions:
            for idx, item in enumerate(decisions, start=1):
                lines.append(f"{idx}. {item}")
        else:
            lines.append(
                "- Chưa ghi nhận quyết định cụ thể."
                if prefer_vi
                else "- No concrete decisions recorded."
            )
        lines.append("")

        lines.append("## Hành động cần thực hiện")
        if action_rows:
            lines.append("| Người phụ trách | Hạn chót | Mức ưu tiên | Trạng thái | Hành động |")
            lines.append("| --- | --- | --- | --- | --- |")
            for row in action_rows:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("owner")),
                            _md_cell(row.get("deadline")),
                            _md_cell(row.get("priority")),
                            _md_cell(row.get("status")),
                            _md_cell(row.get("description")),
                        ]
                    )
                    + " |"
                )
        elif actions:
            for idx, item in enumerate(actions, start=1):
                lines.append(f"{idx}. {item}")
        else:
            lines.append(
                "- Chưa có đầu việc cần theo dõi."
                if prefer_vi
                else "- No tracked action items."
            )
        lines.append("")

        lines.append("## Rủi ro và trở ngại")
        if risk_rows:
            lines.append("| Rủi ro | Mức độ | Giảm thiểu | Người phụ trách | Trạng thái |")
            lines.append("| --- | --- | --- | --- | --- |")
            for row in risk_rows:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("description")),
                            _md_cell(row.get("severity")),
                            _md_cell(row.get("mitigation")),
                            _md_cell(row.get("owner")),
                            _md_cell(row.get("status")),
                        ]
                    )
                    + " |"
                )
        elif risks:
            for item in risks:
                lines.append(f"- {item}")
        else:
            lines.append(
                "- Chưa ghi nhận rủi ro nổi bật."
                if prefer_vi
                else "- No major risks recorded."
            )
        lines.append("")

        if include_ai_filters:
            lines.append("## Bộ lọc AI (tham chiếu)")
            if ai_filters:
                for flt in ai_filters:
                    lines.append(f"- {flt}")
            else:
                lines.append(
                    "- Chưa có bộ lọc AI."
                    if prefer_vi
                    else "- No AI filter metadata."
                )
            lines.append("")

    if include_topic_tracker:
        lines.append("## Theo dõi chủ đề")
        if topic_tracker:
            lines.append("| Chủ đề | Bắt đầu | Kết thúc | Thời lượng (giây) |")
            lines.append("| --- | --- | --- | --- |")
            for row in topic_tracker:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("title")),
                            _md_cell(_fmt_seconds(row.get("start_time"))),
                            _md_cell(_fmt_seconds(row.get("end_time"))),
                            _md_cell(row.get("duration_seconds")),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append(
                "- Chưa có dữ liệu theo dõi chủ đề."
                if prefer_vi
                else "- No topic-tracker data yet."
            )
        lines.append("")

    if session_type == "course" and study_pack:
        concepts = [item for item in _safe_json_list(study_pack.get("concepts")) if item]
        formulas = [item for item in _safe_json_list(study_pack.get("formulas")) if item]
        quiz = [item for item in _safe_json_list(study_pack.get("quiz")) if item]
        if include_knowledge_table:
            lines.append("## Bảng kiến thức trọng tâm")
            if concepts:
                lines.append("| Khái niệm | Giải thích |")
                lines.append("| --- | --- |")
                for item in concepts:
                    lines.append(
                        "| "
                        + " | ".join(
                            [
                                _md_cell(item.get("concept") or item.get("name")),
                                _md_cell(item.get("explanation") or item.get("description")),
                            ]
                        )
                        + " |"
                    )
            else:
                lines.append(
                    "- Chưa có dữ liệu khái niệm."
                    if prefer_vi
                    else "- No concept data available."
                )
            lines.append("")

            lines.append("## Công thức quan trọng" if prefer_vi else "## Important formulas")
            if formulas:
                lines.append("| Tên công thức | Biểu thức | Ý nghĩa |")
                lines.append("| --- | --- | --- |")
                for item in formulas:
                    lines.append(
                        "| "
                        + " | ".join(
                            [
                                _md_cell(item.get("name") or item.get("title")),
                                _md_cell(item.get("formula") or item.get("expression")),
                                _md_cell(item.get("meaning") or item.get("usage") or item.get("description")),
                            ]
                        )
                        + " |"
                    )
            else:
                lines.append(
                    "- Chưa có dữ liệu công thức."
                    if prefer_vi
                    else "- No formula data available."
                )
            lines.append("")
        if include_quiz:
            lines.append("## Câu hỏi ôn tập")
            if quiz:
                for idx, item in enumerate(quiz, start=1):
                    question = str(item.get("question") or "").strip()
                    lines.append(f"{idx}. {question or ('Chưa có nội dung câu hỏi' if prefer_vi else 'No question text')}")
                    options = item.get("options") if isinstance(item.get("options"), list) else []
                    for opt in options:
                        lines.append(f"   - {str(opt).strip()}")
                    answer = str(item.get("answer") or item.get("correct_answer") or "").strip()
                    if answer:
                        lines.append(
                            f"   - **Đáp án:** {answer}"
                            if prefer_vi
                            else f"   - **Answer:** {answer}"
                        )
            else:
                lines.append(
                    "- Chưa có câu hỏi ôn tập."
                    if prefer_vi
                    else "- No quiz data available."
                )
            lines.append("")

    lines.append("## Bước tiếp theo")
    if next_steps:
        for idx, step in enumerate(next_steps, start=1):
            lines.append(f"{idx}. {step}")
    else:
        lines.append(
            "- Chưa xác định bước tiếp theo."
            if prefer_vi
            else "- Next steps are not specified yet."
        )
    lines.append("")

    return "\n".join(lines)


# ============================================
# Distribution
# ============================================

def list_distribution_logs(db: Session, meeting_id: str) -> DistributionLogList:
    """List distribution logs for a meeting"""
    _ensure_minutes_tables(db)
    query = text("""
        SELECT 
            id::text, minutes_id::text, meeting_id::text,
            user_id::text, channel, recipient_email,
            sent_at, status, error_message
        FROM minutes_distribution_log
        WHERE meeting_id = :meeting_id
        ORDER BY sent_at DESC
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    logs = []
    for row in rows:
        logs.append(DistributionLogResponse(
            id=row[0],
            minutes_id=row[1],
            meeting_id=row[2],
            user_id=row[3],
            channel=row[4],
            recipient_email=row[5],
            sent_at=row[6],
            status=row[7],
            error_message=row[8]
        ))
    
    return DistributionLogList(logs=logs, total=len(logs))


def create_distribution_log(db: Session, data: DistributionLogCreate) -> DistributionLogResponse:
    """Create a distribution log entry"""
    _ensure_minutes_tables(db)
    log_id = str(uuid4())
    now = datetime.utcnow()
    
    query = text("""
        INSERT INTO minutes_distribution_log (
            id, minutes_id, meeting_id, user_id, channel,
            recipient_email, sent_at, status
        )
        VALUES (
            :id, :minutes_id, :meeting_id, :user_id, :channel,
            :recipient_email, :sent_at, :status
        )
        RETURNING id::text
    """)
    
    db.execute(query, {
        'id': log_id,
        'minutes_id': data.minutes_id,
        'meeting_id': data.meeting_id,
        'user_id': data.user_id,
        'channel': data.channel,
        'recipient_email': data.recipient_email,
        'sent_at': now,
        'status': data.status
    })
    db.commit()
    
    return DistributionLogResponse(
        id=log_id,
        minutes_id=data.minutes_id,
        meeting_id=data.meeting_id,
        user_id=data.user_id,
        channel=data.channel,
        recipient_email=data.recipient_email,
        sent_at=now,
        status=data.status
    )
