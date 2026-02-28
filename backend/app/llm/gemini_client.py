import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

from groq import Groq
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _output_language_code() -> str:
    raw = (settings.llm_output_language or "vi").strip().lower()
    if raw in {"vi", "vi-vn", "vn", "vietnamese", "vietnam", "tieng viet", "tiếng việt"}:
        return "vi"
    if raw in {"en", "en-us", "en-gb", "english"}:
        return "en"
    return "vi" if not raw else raw


def _output_language_name() -> str:
    code = _output_language_code()
    if code == "vi":
        return "Vietnamese"
    if code == "en":
        return "English"
    return "Vietnamese"


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


def _strip_code_fences(raw: str) -> str:
    text = (raw or "").strip()
    if not text.startswith("```"):
        return text
    text = re.sub(r"^```(?:json|javascript|js|text|markdown)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _decode_json_like_string(value: str) -> str:
    return (
        (value or "")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\\n", "\n")
        .replace("\\t", " ")
        .replace("\\\\", "\\")
        .strip()
    )


def _dedupe_keep_order(values: List[str]) -> List[str]:
    seen = set()
    deduped: List[str] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _json_object_candidates(raw: str) -> List[str]:
    cleaned = _strip_code_fences(raw).replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    candidates = [cleaned]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if 0 <= start < end:
        candidates.append(cleaned[start : end + 1])
    return [c.strip() for c in candidates if c and c.strip()]


def _json_candidate_variants(candidate: str) -> List[str]:
    variants = [candidate]

    no_trailing_comma = re.sub(r",\s*([}\]])", r"\1", candidate)
    variants.append(no_trailing_comma)

    quoted_keys = re.sub(
        r'([{,]\s*)([A-Za-z_][A-Za-z0-9_-]*)\s*:',
        r'\1"\2":',
        no_trailing_comma,
    )
    variants.append(quoted_keys)

    single_quote_to_double = re.sub(
        r"'([^'\\]*(?:\\.[^'\\]*)*)'",
        lambda m: '"' + m.group(1).replace('"', '\\"') + '"',
        quoted_keys,
    )
    variants.append(single_quote_to_double)

    return _dedupe_keep_order([v.strip() for v in variants if v and v.strip()])


def _parse_json_object_relaxed(raw: str) -> Optional[Dict[str, Any]]:
    for candidate in _json_object_candidates(raw):
        for variant in _json_candidate_variants(candidate):
            try:
                parsed = json.loads(variant)
            except Exception:
                continue
            if isinstance(parsed, dict):
                return parsed
    return None


def _pick_first_string_value(obj: Dict[str, Any], keys: Tuple[str, ...]) -> str:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _pick_string_list_value(obj: Dict[str, Any], keys: Tuple[str, ...]) -> List[str]:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [
                line.strip()
                for line in value.splitlines()
                if line.strip()
            ]
    return []


def _extract_summary_and_points_from_payload(payload: Dict[str, Any]) -> Tuple[str, List[str]]:
    summary = _pick_first_string_value(payload, SUMMARY_FIELD_KEYS)
    key_points = _pick_string_list_value(payload, KEY_POINTS_FIELD_KEYS)

    nested = payload.get("data")
    if isinstance(nested, dict):
        if not summary:
            summary = _pick_first_string_value(nested, SUMMARY_FIELD_KEYS)
        if not key_points:
            key_points = _pick_string_list_value(nested, KEY_POINTS_FIELD_KEYS)

    return _decode_json_like_string(summary), [_decode_json_like_string(item) for item in key_points if item.strip()]


def _extract_summary_field_by_regex(raw: str) -> str:
    text = _strip_code_fences(raw)
    key_pattern = "|".join(re.escape(key) for key in SUMMARY_FIELD_KEYS)
    patterns = [
        rf'["\']?(?:{key_pattern})["\']?\s*:\s*"([\s\S]*?)"(?=\s*,\s*["\']?[A-Za-z_][A-Za-z0-9_-]*["\']?\s*:|\s*[}}])',
        rf'["\']?(?:{key_pattern})["\']?\s*:\s*\'([\s\S]*?)\'(?=\s*,\s*["\']?[A-Za-z_][A-Za-z0-9_-]*["\']?\s*:|\s*[}}])',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and match.group(1).strip():
            return _decode_json_like_string(match.group(1))
    return ""


def _extract_key_points_by_regex(raw: str) -> List[str]:
    text = _strip_code_fences(raw)
    key_pattern = "|".join(re.escape(key) for key in KEY_POINTS_FIELD_KEYS)
    pattern = rf'["\']?(?:{key_pattern})["\']?\s*:\s*\[([\s\S]*?)\]'
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match or not match.group(1):
        return []

    body = match.group(1)
    points: List[str] = []
    for item_match in re.finditer(r'"((?:\\.|[^"\\])*)"|\'((?:\\.|[^\'\\])*)\'', body):
        candidate = item_match.group(1) if item_match.group(1) is not None else (item_match.group(2) or "")
        decoded = _decode_json_like_string(candidate)
        if decoded:
            points.append(decoded)

    if points:
        return points

    fallback = [
        segment.strip(" \t\r\n-•\"'")
        for segment in re.split(r"[\n,;]+", body)
        if segment.strip(" \t\r\n-•\"'")
    ]
    return fallback


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    master_prompt: Optional[str] = None
    behavior_note_style: Optional[str] = None
    behavior_tone: Optional[str] = None
    behavior_cite_evidence: Optional[bool] = None
    behavior_profile: Optional[str] = None


def _compose_effective_system_prompt(
    base_prompt: Optional[str],
    llm_config: Optional[LLMConfig] = None,
) -> str:
    prompt_parts: List[str] = [(base_prompt or "").strip()]
    if not llm_config:
        return prompt_parts[0] if prompt_parts[0] else ""
    behavior_lines: List[str] = []
    if llm_config.behavior_note_style:
        behavior_lines.append(f"- Desired detail level: {llm_config.behavior_note_style}")
    if llm_config.behavior_tone:
        behavior_lines.append(f"- Desired tone/style: {llm_config.behavior_tone}")
    if llm_config.behavior_cite_evidence is True:
        behavior_lines.append("- Always include evidence (timestamps/documents) when available.")
    elif llm_config.behavior_cite_evidence is False:
        behavior_lines.append("- Evidence/citations are optional unless needed.")
    if llm_config.behavior_profile:
        behavior_lines.append(f"- User profile:\n{llm_config.behavior_profile}")
    if behavior_lines:
        prompt_parts.append(
            "User behavior settings (high priority within safety rules):\n"
            + "\n".join(behavior_lines)
        )
    if llm_config.master_prompt:
        prompt_parts.append(
            "User master prompt (highest priority within safety rules):\n"
            + llm_config.master_prompt.strip()
        )
    return "\n\n".join([p for p in prompt_parts if p])

try:
    # New Gemini SDK (google-genai)
    from google import genai as genai_client  # type: ignore
    from google.genai import types as genai_types  # type: ignore
    _GENAI_SDK = "google-genai"
except Exception:
    genai_client = None
    genai_types = None
    _GENAI_SDK = None

try:
    # Legacy Gemini SDK (google-generativeai)
    import google.generativeai as genai_legacy  # type: ignore
    _LEGACY_GENAI = True
except Exception:
    genai_legacy = None
    _LEGACY_GENAI = False


def _gemini_sdk_name() -> str:
    if _GENAI_SDK and genai_client:
        return "google-genai"
    if _LEGACY_GENAI and genai_legacy:
        return "google-generativeai"
    return "none"


def configure_genai() -> bool:
    """Configure legacy Google Generative AI if key is present."""
    if settings.gemini_api_key and genai_legacy:
        genai_legacy.configure(api_key=settings.gemini_api_key)
        return True
    return False


def get_groq_client(api_key_override: Optional[str] = None):
    """Return Groq client."""
    api_key = api_key_override or settings.groq_api_key
    if not api_key:
        return None
    return Groq(api_key=api_key)


def _select_provider(
    provider_override: Optional[str] = None,
    *,
    gemini_api_key: Optional[str] = None,
    groq_api_key: Optional[str] = None,
) -> str:
    if provider_override == "gemini":
        if (gemini_api_key or settings.gemini_api_key) and (genai_client or genai_legacy):
            return "gemini"
        return "mock"
    if provider_override == "groq":
        if groq_api_key or settings.groq_api_key:
            return "groq"
        return "mock"
    if (gemini_api_key or settings.gemini_api_key) and (genai_client or genai_legacy):
        return "gemini"
    if groq_api_key or settings.groq_api_key:
        return "groq"
    return "mock"


def _is_model_not_found_error(exc: Exception) -> bool:
    raw = str(exc).lower()
    return (
        ("model" in raw and "not found" in raw)
        or ("unknown model" in raw)
        or ("invalid model" in raw)
        or ("does not exist" in raw and "model" in raw)
    )


def _groq_model_candidates(model_name: str) -> List[str]:
    candidates: List[str] = []
    for name in (
        model_name,
        settings.llm_groq_chat_model,
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ):
        normalized = (name or "").strip()
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def is_gemini_available() -> bool:
    """Check if Gemini or Groq is configured and usable."""
    provider = _select_provider()
    if provider != "mock":
        return True
    logger.warning("[AI] No AI API key configured (Gemini or Groq)")
    return False


def get_llm_status() -> Dict[str, Any]:
    """Return provider + model metadata for UI/health checks."""
    provider = _select_provider()
    if provider == "gemini":
        model = settings.gemini_model
        api_key_set = bool(settings.gemini_api_key and len(settings.gemini_api_key) > 10)
        api_key_preview = (settings.gemini_api_key[:8] + "...") if settings.gemini_api_key else None
    elif provider == "groq":
        model = settings.llm_groq_chat_model
        api_key_set = bool(settings.groq_api_key and len(settings.groq_api_key) > 10)
        api_key_preview = (settings.groq_api_key[:8] + "...") if settings.groq_api_key else None
    else:
        model = None
        api_key_set = False
        api_key_preview = None
    return {
        "provider": provider,
        "status": "ready" if provider != "mock" else "mock_mode",
        "model": model,
        "api_key_set": api_key_set,
        "api_key_preview": api_key_preview,
        "sdk": _gemini_sdk_name(),
    }


def _gemini_generate(
    prompt: str,
    *,
    system_prompt: Optional[str],
    model_name: str,
    temperature: float,
    max_tokens: int,
    api_key: Optional[str] = None,
) -> str:
    api_key = api_key or settings.gemini_api_key
    if not api_key:
        return ""
    candidates = []
    for name in [
        model_name,
        settings.gemini_model,
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]:
        normalized = (name or "").strip()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    def _is_model_not_found(exc: Exception) -> bool:
        raw = str(exc).lower()
        return ("not found" in raw and "model" in raw) or ("models/" in raw and "not found" in raw)

    last_error: Optional[Exception] = None
    for candidate in candidates:
        try:
            if genai_client and genai_types:
                client = genai_client.Client(api_key=api_key)
                try:
                    config = genai_types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        system_instruction=system_prompt or None,
                    )
                    response = client.models.generate_content(
                        model=candidate,
                        contents=prompt,
                        config=config,
                    )
                    return (getattr(response, "text", None) or "").strip()
                except Exception:
                    # Fallback: inline system prompt if SDK config signature differs.
                    merged_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                    response = client.models.generate_content(
                        model=candidate,
                        contents=merged_prompt,
                    )
                    return (getattr(response, "text", None) or "").strip()

            if genai_legacy:
                genai_legacy.configure(api_key=api_key)
                model = genai_legacy.GenerativeModel(
                    model_name=candidate,
                    system_instruction=system_prompt or None,
                )
                response = model.generate_content(
                    prompt,
                    generation_config=genai_legacy.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )
                return (response.text or "").strip()
        except Exception as exc:
            last_error = exc
            if _is_model_not_found(exc):
                continue
            break

    if last_error:
        logger.error("[gemini] generate error model=%s: %s", model_name, last_error)
    return ""


def _groq_generate(
    prompt: str,
    *,
    system_prompt: Optional[str],
    model_name: str,
    temperature: float,
    max_tokens: int,
    api_key: Optional[str] = None,
) -> str:
    client = get_groq_client(api_key)
    if not client:
        logger.warning("[groq] generate requested but no API key is configured")
        return ""

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    last_error: Optional[Exception] = None
    for candidate_model in _groq_model_candidates(model_name):
        try:
            resp = client.chat.completions.create(
                model=candidate_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if candidate_model != model_name:
                logger.warning(
                    "[groq] fallback model used requested=%s resolved=%s",
                    model_name,
                    candidate_model,
                )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:
            last_error = exc
            if _is_model_not_found_error(exc):
                logger.warning("[groq] model unavailable: %s (%s)", candidate_model, exc)
                continue
            logger.error("[groq] generate failed model=%s: %s", candidate_model, exc)
            break

    if last_error:
        logger.error("[groq] generate error model=%s: %s", model_name, last_error)
    return ""


def _groq_chat(
    messages: List[Dict[str, str]],
    *,
    model_name: str,
    temperature: float,
    max_tokens: int,
    api_key: Optional[str] = None,
) -> str:
    client = get_groq_client(api_key)
    if not client:
        logger.warning("[groq] chat requested but no API key is configured")
        return ""

    last_error: Optional[Exception] = None
    for candidate_model in _groq_model_candidates(model_name):
        try:
            resp = client.chat.completions.create(
                model=candidate_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if candidate_model != model_name:
                logger.warning(
                    "[groq] fallback model used requested=%s resolved=%s",
                    model_name,
                    candidate_model,
                )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:
            last_error = exc
            if _is_model_not_found_error(exc):
                logger.warning("[groq] model unavailable: %s (%s)", candidate_model, exc)
                continue
            logger.error("[groq] chat failed model=%s: %s", candidate_model, exc)
            raise

    if last_error:
        logger.error("[groq] chat error model=%s: %s", model_name, last_error)
    return ""


def call_llm_sync(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    llm_config: Optional[LLMConfig] = None,
) -> str:
    """Sync LLM call used by low-latency / sync code paths."""
    effective_system_prompt = _compose_effective_system_prompt(system_prompt, llm_config) or None
    provider_override = llm_config.provider if llm_config else None
    gemini_key = llm_config.api_key if llm_config and llm_config.provider == "gemini" else None
    groq_key = llm_config.api_key if llm_config and llm_config.provider == "groq" else None
    provider = _select_provider(provider_override, gemini_api_key=gemini_key, groq_api_key=groq_key)
    temperature = settings.ai_temperature if temperature is None else temperature
    max_tokens = settings.ai_max_tokens if max_tokens is None else max_tokens
    if provider == "gemini":
        candidate_model = llm_config.model if llm_config else ""
        return _gemini_generate(
            prompt,
            system_prompt=effective_system_prompt,
            model_name=model_name or candidate_model or settings.gemini_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=gemini_key,
        )
    if provider == "groq":
        candidate_model = llm_config.model if llm_config else ""
        return _groq_generate(
            prompt,
            system_prompt=effective_system_prompt,
            model_name=model_name or candidate_model or settings.llm_groq_chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=groq_key,
        )
    logger.warning(
        "[AI] call_llm_sync in mock mode provider_override=%s",
        provider_override or "auto",
    )
    return ""

class GeminiChat:
    """Chat wrapper supporting Google Gemini and Groq."""
    
    def __init__(
        self,
        system_prompt: Optional[str] = None,
        mock_response: Optional[str] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        base_system_prompt = system_prompt or self._default_system_prompt()
        self.system_prompt = _compose_effective_system_prompt(base_system_prompt, llm_config)
        self.mock_response = mock_response or "AI is running in mock mode (no API key configured)."
        self.history: List[Dict[str, str]] = []
        self.mock_reason: Optional[str] = None
        
        provider_override = llm_config.provider if llm_config else None
        gemini_key = llm_config.api_key if llm_config and llm_config.provider == "gemini" else None
        groq_key = llm_config.api_key if llm_config and llm_config.provider == "groq" else None
        self.provider = _select_provider(provider_override, gemini_api_key=gemini_key, groq_api_key=groq_key)
        if self.provider == "gemini":
            candidate_model = llm_config.model if llm_config and llm_config.provider == "gemini" else ""
            self.model_name = candidate_model or settings.gemini_model
            self.api_key = gemini_key
        elif self.provider == "groq":
            candidate_model = llm_config.model if llm_config and llm_config.provider == "groq" else ""
            self.model_name = candidate_model or settings.llm_groq_chat_model
            self.api_key = groq_key
        else:
            self.model_name = None
            self.api_key = None
            if provider_override == "groq":
                self.mock_reason = "Groq is selected but no Groq API key is configured."
            elif provider_override == "gemini":
                self.mock_reason = "Gemini is selected but no Gemini API key is configured."
            else:
                self.mock_reason = "No AI API key is configured."

        if self.provider == "mock" and self.mock_reason:
            self.mock_response = f"{self.mock_response} ({self.mock_reason})"

        logger.info(
            "[AI] GeminiChat initialized provider=%s model=%s override=%s",
            self.provider,
            self.model_name or "n/a",
            provider_override or "auto",
        )
    
    def _default_system_prompt(self) -> str:
        return """You are MINUTE AI Assistant — an intelligent copilot for meetings and study sessions.

Mission:
1) Pre-meeting: suggest agendas, pre-read packs, and relevant documents.
2) In-meeting: produce time-aware recaps and detect actions/decisions/risks.
3) Post-meeting: generate minutes, summaries, notes, and next steps.
4) Study mode: extract key concepts, examples, and create practice quizzes.
5) Q&A: answer grounded in transcript/summary/documents.
6) Multimodal: if "visual_context" or frame notes exist, use them to ground answers.

Hard rules:
- Use ONLY the data provided (context/transcript/docs). If data is missing, answer what is supported and state what is unknown.
- Do not hallucinate or speculate beyond the provided context. Prefer concise, clear answers.
- If an action or tool call is needed, ask for confirmation first (human-in-the-loop).
- Respond in Vietnamese by default, naturally and professionally.
- If the user explicitly asks for another language, follow the user request.
"""

    async def chat(self, message: str, context: Optional[str] = None) -> str:
        if self.provider == "mock":
            logger.warning("[AI] Chat fallback to mock mode reason=%s", self.mock_reason or "unconfigured provider")
            return self._mock_response(message)
            
        try:
            full_prompt = message
            if context:
                full_prompt = f"Context:\n{context}\n\nUser Question: {message}"

            if self.provider == "gemini":
                response_text = await asyncio.to_thread(
                    _gemini_generate,
                    full_prompt,
                    system_prompt=self.system_prompt,
                    model_name=self.model_name or settings.gemini_model,
                    temperature=settings.ai_temperature,
                    max_tokens=settings.ai_max_tokens,
                    api_key=self.api_key,
                )
                if not (response_text or "").strip():
                    logger.warning(
                        "[AI] Empty Gemini response model=%s, falling back to mock response",
                        self.model_name or settings.gemini_model,
                    )
                    return self._mock_response(message)
                return self._clean_markdown(response_text)
            elif self.provider == "groq":
                # Groq
                messages = []
                if self.system_prompt:
                    messages.append({"role": "system", "content": self.system_prompt})
                # Check history (simplified)
                for h in self.history[-5:]:
                    messages.append({"role": "user", "content": h["user"]})
                    messages.append({"role": "assistant", "content": h["assistant"]})
                
                messages.append({"role": "user", "content": full_prompt})

                assistant_message = await asyncio.to_thread(
                    _groq_chat,
                    messages,
                    model_name=self.model_name or settings.llm_groq_chat_model,
                    temperature=settings.ai_temperature,
                    max_tokens=settings.ai_max_tokens,
                    api_key=self.api_key,
                )
                if not (assistant_message or "").strip():
                    logger.warning(
                        "[AI] Empty Groq response model=%s, falling back to mock response",
                        self.model_name or settings.llm_groq_chat_model,
                    )
                    return self._mock_response(message)
                self.history.append({"user": full_prompt, "assistant": assistant_message})
                return self._clean_markdown(assistant_message)
                
        except Exception as e:
            logger.exception(
                "[AI] Chat error provider=%s model=%s: %s",
                self.provider,
                self.model_name or "n/a",
                e,
            )
            return self._mock_response(message)
    
    def _clean_markdown(self, text: str) -> str:
        return (text or "").strip()
    
    def _mock_response(self, message: str) -> str:
        return self.mock_response


class MeetingAIAssistant:
    """AI Assistant specifically for meeting context"""
    
    def __init__(
        self,
        meeting_id: str,
        meeting_context: Optional[Dict[str, Any]] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.meeting_id = meeting_id
        self.meeting_context = meeting_context or {}
        self.chat = GeminiChat(llm_config=llm_config)
    
    def _build_context(self) -> str:
        """Build context string from meeting data"""
        ctx_parts = []
        
        if self.meeting_context.get('title'):
            ctx_parts.append(f"Meeting: {self.meeting_context['title']}")
        
        if self.meeting_context.get('type'):
            ctx_parts.append(f"Type: {self.meeting_context['type']}")
        
        if self.meeting_context.get('project'):
            ctx_parts.append(f"Project: {self.meeting_context['project']}")
        
        if self.meeting_context.get('agenda'):
            ctx_parts.append(f"Agenda: {self.meeting_context['agenda']}")

        if self.meeting_context.get('visual_context'):
            ctx_parts.append(f"Visual context: {self.meeting_context['visual_context']}")

        if self.meeting_context.get('timeline_highlights'):
            ctx_parts.append(f"Timeline highlights: {self.meeting_context['timeline_highlights']}")
        
        if self.meeting_context.get('transcript'):
            ctx_parts.append(f"Transcript excerpt: {self.meeting_context['transcript'][:15000]}...")
        
        return "\n".join(ctx_parts)
    
    async def ask(self, question: str) -> str:
        """Ask a question with meeting context"""
        context = self._build_context()
        return await self.chat.chat(question, context)
    
    async def generate_agenda(self, meeting_type: str) -> str:
        """Generate agenda based on meeting type"""
        prompt = f"""Tạo chương trình cuộc họp chi tiết cho loại: {meeting_type}

Yêu cầu:
- Mỗi mục có: số thứ tự, tiêu đề, thời lượng (phút), người trình bày
- Tổng thời gian khoảng 60 phút
- Format: JSON array với fields: order, title, duration_minutes, presenter"""
        
        return await self.chat.chat(prompt)
    
    async def extract_action_items(self, transcript: str) -> str:
        """Extract action items from transcript"""
        prompt = f"""Phân tích transcript sau và trích xuất các Action Items:

{transcript[:15000]}

Format output JSON:
[
  {{
    "description": "Mô tả task",
    "owner": "Tên người được giao (nếu có)",
    "deadline": "Deadline (nếu được đề cập)",
    "priority": "high/medium/low",
    "topic_id": "topic_related",
    "source_text": "Câu gốc trong transcript nếu có"
  }}
]"""
        
        return await self.chat.chat(prompt)
    
    async def extract_decisions(self, transcript: str) -> str:
        """Extract decisions from transcript"""
        prompt = f"""Phân tích transcript sau và trích xuất các Quyết định (Decisions):

{transcript[:15000]}

Format output JSON:
[
  {{
    "description": "Nội dung quyết định",
    "rationale": "Lý do (nếu có)",
    "confirmed_by": "Người xác nhận",
    "source_text": "Câu gốc trong transcript nếu có"
  }}
]"""
        
        return await self.chat.chat(prompt)
    
    async def extract_risks(self, transcript: str) -> str:
        """Extract risks from transcript"""
        prompt = f"""Phân tích transcript sau và trích xuất các Rủi ro (Risks):

{transcript[:15000]}

Format output JSON:
[
  {{
    "description": "Mô tả rủi ro",
    "severity": "critical/high/medium/low",
    "mitigation": "Biện pháp giảm thiểu (nếu có)",
    "source_text": "Câu gốc trong transcript nếu có"
  }}
]"""
        
        return await self.chat.chat(prompt)

    # ================= STUDY MODE METHODS =================

    async def extract_concepts(self, transcript: str) -> str:
        """Extract key concepts and terms from a study session transcript."""
        prompt = f"""Phân tích transcript buổi học/nghiên cứu sau để trích xuất các KHÁI NIỆM quan trọng (Concepts):

{transcript[:15000]}

Yêu cầu:
- Xác định các định nghĩa, thuật ngữ chuyên ngành, hoặc ý tưởng cốt lõi.
- Giải thích ngắn gọn dễ hiểu.

Format output JSON:
[
  {{
    "term": "Tên khái niệm/thuật ngữ",
    "definition": "Định nghĩa hoặc giải thích ngắn gọn",
    "example": "Ví dụ minh hoạ (nếu có trong bài)"
  }}
]"""
        return await self.chat.chat(prompt)

    async def generate_quiz(self, transcript: str) -> str:
        """Generate a quiz based on the transcript."""
        prompt = f"""Dựa trên nội dung buổi học sau, hãy tạo bộ câu hỏi trắc nghiệm (Quiz) để ôn tập:

{transcript[:15000]}

Yêu cầu:
- 5 câu hỏi trắc nghiệm.
- Mỗi câu có 4 lựa chọn (options).
- Chỉ định rõ đáp án đúng và giải thích tại sao.

Format output JSON:
[
  {{
    "question": "Nội dung câu hỏi",
    "options": ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"],
    "correct_answer_index": 0, // 0=A, 1=B, 2=C, 3=D
    "explanation": "Giải thích chi tiết tại sao đáp án này đúng"
  }}
]"""
        return await self.chat.chat(prompt)

    # ================= SUMMARY GENERATION =================

    async def generate_summary_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meeting summary with full context and practical guardrails."""
        language_name = _output_language_name()
        prefer_vi = _output_language_code() == "vi"
        language_guard = (
            "- Write fully in natural Vietnamese (Tiếng Việt). Do not switch to English unless user explicitly asks."
            if prefer_vi
            else "- Write fully in English unless user explicitly asks for another language."
        )
        prompt = f"""You are MINUTE AI, a meeting and study-session copilot.
Create a rich {language_name} summary using ONLY the JSON data below. Do not invent facts.

Rules:
- Output language: {language_name}.
- {language_guard}
- Never return an empty summary.
- Summary target length: 220-420 words, written in 3-6 coherent paragraphs.
- Cover: objective/context, major discussion threads, concrete outcomes, unresolved questions, risks, and next-step direction.
- Ground claims in provided evidence (transcript, visual_context, topic_tracker, documents, actions, decisions, risks).
- If data is sparse, still provide a useful preliminary summary and explicitly state what evidence is missing.
- Avoid refusal-style responses like "not enough data to generate" unless all fields are truly empty.
- key_points must contain 8-12 concise, specific, actionable bullets (plain strings).
- No markdown in summary or key_points.

        Data:
{json.dumps(context, ensure_ascii=False)}

Return STRICT JSON only (no extra prose):
{{"summary": "...", "key_points": ["...", "..."]}}"""
        response = await self.chat.chat(prompt)
        result = _parse_json_object_relaxed(response) or {}
        summary = ""
        key_points: List[str] = []
        if result:
            summary, key_points = _extract_summary_and_points_from_payload(result)

        if not summary:
            summary = _extract_summary_field_by_regex(response)
        if not key_points:
            key_points = _extract_key_points_by_regex(response)
        if not summary and not key_points:
            summary = _strip_code_fences(response).strip()

        if not summary.strip():
            title = str(context.get("title") or "Meeting").strip()
            desc = str(context.get("description") or "").strip()
            transcript = str(context.get("transcript") or "").strip()
            actions = context.get("actions") or []
            decisions = context.get("decisions") or []
            risks = context.get("risks") or []
            docs = context.get("documents") or []

            if desc:
                if prefer_vi:
                    summary = (
                        f"Tóm tắt sơ bộ cho '{title}': {desc[:360]}. "
                        "Cần thêm bằng chứng transcript để tăng độ chi tiết và độ tin cậy."
                    )
                else:
                    summary = (
                        f"Preliminary summary for '{title}': {desc[:360]}. "
                        "Additional transcript evidence will improve detail and confidence."
                    )
            elif transcript:
                if prefer_vi:
                    summary = (
                        f"Tóm tắt sơ bộ cho '{title}': {transcript[:420]}. "
                        "Bản nháp này nên được tinh chỉnh bằng transcript đầy đủ."
                    )
                else:
                    summary = (
                        f"Preliminary summary for '{title}': {transcript[:420]}. "
                        "This draft should be refined with full transcript context."
                    )
            elif actions or decisions or risks:
                if prefer_vi:
                    summary = (
                        f"Tóm tắt sơ bộ cho '{title}': đã ghi nhận "
                        f"{len(actions)} đầu việc, {len(decisions)} quyết định và {len(risks)} rủi ro. "
                        "Cần transcript hoặc ghi chú đầy đủ để tạo phần tường thuật chi tiết."
                    )
                else:
                    summary = (
                        f"Preliminary summary for '{title}': captured "
                        f"{len(actions)} action item(s), {len(decisions)} decision(s), and {len(risks)} risk(s). "
                        "Detailed narrative requires transcript or richer notes."
                    )
            elif docs:
                if prefer_vi:
                    summary = (
                        f"Tóm tắt sơ bộ cho '{title}': đã có tài liệu liên quan. "
                        "Vui lòng bổ sung transcript để tạo bản tóm tắt sâu và đáng tin cậy hơn."
                    )
                else:
                    summary = (
                        f"Preliminary summary for '{title}': related documents are available. "
                        "Please add transcript evidence for a deeper and more reliable summary."
                    )
            else:
                if prefer_vi:
                    summary = (
                        f"Tóm tắt sơ bộ cho '{title}': phiên họp đã được ghi nhận nhưng dữ liệu nội dung còn hạn chế. "
                        "Vui lòng cung cấp transcript hoặc ghi chú để tạo bản tóm tắt đầy đủ theo bằng chứng."
                    )
                else:
                    summary = (
                        f"Preliminary summary for '{title}': the session is recorded but content data is still limited. "
                        "Please provide transcript or notes to generate a full, evidence-based summary."
                    )

        if not key_points:
            fallback_points: List[str] = []
            actions = context.get("actions") or []
            decisions = context.get("decisions") or []
            risks = context.get("risks") or []
            docs = context.get("documents") or []
            if actions:
                if prefer_vi:
                    fallback_points.append(f"Đã ghi nhận {len(actions)} đầu việc cần theo dõi.")
                else:
                    fallback_points.append(f"{len(actions)} action item(s) were captured and should be tracked.")
            if decisions:
                if prefer_vi:
                    fallback_points.append(f"Đã xác định {len(decisions)} quyết định trong phiên họp.")
                else:
                    fallback_points.append(f"{len(decisions)} decision(s) were identified in this session.")
            if risks:
                if prefer_vi:
                    fallback_points.append(f"Đã ghi nhận {len(risks)} rủi ro hoặc blocker.")
                else:
                    fallback_points.append(f"{len(risks)} risk(s) or blockers were flagged.")
            if docs:
                if prefer_vi:
                    fallback_points.append(f"Có {len(docs)} tài liệu liên quan được gắn với phiên họp.")
                else:
                    fallback_points.append(f"{len(docs)} related document(s) are linked to this session.")
            if not fallback_points:
                if prefer_vi:
                    fallback_points.append("Bổ sung transcript hoặc ghi chú để tăng độ sâu và độ tin cậy cho tóm tắt.")
                else:
                    fallback_points.append("Add transcript or notes to increase summary depth and reliability.")
            key_points = fallback_points[:8]
        return {"summary": summary, "key_points": key_points}
    
    async def generate_minutes_json(self, transcript: str) -> Dict[str, Any]:
        """Generate comprehensive minutes in strict JSON format with rich content"""
        language_name = _output_language_name()
        prefer_vi = _output_language_code() == "vi"
        unknown_placeholder = "Không rõ" if prefer_vi else "Unknown"
        language_guard = (
            "Write all text values in natural Vietnamese. Do not output English sentences unless user explicitly asks."
            if prefer_vi
            else "Write all text values in natural English unless user explicitly asks another language."
        )
        prompt = f"""You are MINUTE AI, generating professional meeting minutes for business teams.
Analyze the transcript below and produce a detailed, factual minutes JSON.

TRANSCRIPT:
{transcript[:20000]}

OUTPUT REQUIREMENTS (Strict JSON Mode):
- Return exactly ONE JSON object only (no markdown code fence, no commentary).
- Output language: {language_name}.
- {language_guard}
- Be specific, evidence-based, and avoid hallucinations.
- If a field is unknown, use "{unknown_placeholder}" or null instead of omitting required structure.

Required JSON schema:
{{
  "executive_summary": "3-6 well-structured paragraphs, target 220-420 words (minimum 120 words if transcript is sparse). Include purpose, key discussion flow, outcomes, unresolved points, risks, and implications.",
  "key_points": [
    "8-15 concrete points, each concise and evidence-grounded"
  ],
  "action_items": [
    {{
      "description": "Detailed action",
      "owner": "Responsible person from transcript, else '{unknown_placeholder}'",
      "deadline": "YYYY-MM-DD if explicit, otherwise null",
      "priority": "high/medium/low",
      "created_by": "Who requested or initiated it, else '{unknown_placeholder}'"
    }}
  ],
  "decisions": [
    {{
      "description": "Clear decision statement",
      "rationale": "Why this decision was made",
      "decided_by": "Final decision maker if known, else '{unknown_placeholder}'",
      "approved_by": "Approver(s) if mentioned, else '{unknown_placeholder}'"
    }}
  ],
  "risks": [
    {{
      "description": "Risk or issue",
      "severity": "critical/high/medium/low",
      "mitigation": "Mitigation discussed, else empty string",
      "raised_by": "Who raised it, else '{unknown_placeholder}'"
    }}
  ],
  "next_steps": [
    "Specific follow-up steps after the meeting"
  ],
  "attendees_mentioned": [
    "Names explicitly mentioned in transcript"
  ]
}}

        Guidance:
- Extract as much useful detail as possible from transcript content.
- Do not repeat near-duplicate bullets; merge similar points.
- If visual signals appear (e.g., [VISUAL], [SCREEN], slide references), reflect them in executive_summary and key_points.
"""
        
        response = await self.chat.chat(prompt)

        payload = _parse_json_object_relaxed(response)
        if payload:
            # Backfill summary/key points in case model used alternative key names.
            summary, key_points = _extract_summary_and_points_from_payload(payload)
            if summary and not str(payload.get("executive_summary") or "").strip():
                payload["executive_summary"] = summary
            if key_points and not isinstance(payload.get("key_points"), list):
                payload["key_points"] = key_points
            if key_points and isinstance(payload.get("key_points"), list) and not payload.get("key_points"):
                payload["key_points"] = key_points

            for key in ("action_items", "decisions", "risks", "next_steps", "attendees_mentioned"):
                value = payload.get(key)
                if not isinstance(value, list):
                    payload[key] = []
            payload.setdefault("study_pack", None)
            return payload

        summary = _extract_summary_field_by_regex(response)
        key_points = _extract_key_points_by_regex(response)
        if not summary:
            summary = _strip_code_fences(response).strip()[:1200]

        logger.warning("[AI] Failed to parse strict minutes JSON; returning sanitized fallback payload.")
        return {
            "executive_summary": summary,
            "key_points": key_points,
            "action_items": [],
            "decisions": [],
            "risks": [],
            "next_steps": [],
            "attendees_mentioned": [],
            "study_pack": None,
        }
    
    async def generate_summary(self, transcript: str) -> str:
        """Generate meeting summary"""
        language_name = _output_language_name()
        prefer_vi = _output_language_code() == "vi"
        format_block = """## Tóm tắt cuộc họp

### Tường thuật điều hành
- 2-4 đoạn ngắn, rõ ràng, bám bằng chứng

### Điểm chính
- 8-12 ý cụ thể

### Quyết định
- ...

### Việc cần làm
- nêu người phụ trách, deadline (nếu có), người giao việc (nếu có)

### Rủi ro và trở ngại
- ...

### Bước tiếp theo
- ...

### Câu hỏi cần follow-up
- ...""" if prefer_vi else """## Meeting Summary

### Executive Narrative
- 2-4 compact paragraphs, concrete and evidence-based

### Key Points
- 8-12 specific points

### Decisions
- ...

### Action Items
- owner, deadline (if available), and requested-by when possible

### Risks and Blockers
- ...

### Next Steps
- ...

### Follow-up Questions
- ..."""
        language_guard = (
            "Write in natural Vietnamese (Tiếng Việt). Do not switch to English unless user explicitly asks."
            if prefer_vi
            else "Write in natural English unless user explicitly asks another language."
        )
        prompt = f"""Create a detailed {language_name} meeting summary from the transcript below.
Use only transcript evidence and do not hallucinate.
Never return an empty response.
If transcript is short, still provide a useful preliminary summary and clearly list missing context.
{language_guard}

Transcript:
{transcript[:3000]}

Format:
{format_block}
"""
        
        return await self.chat.chat(prompt)
