import asyncio
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from groq import Groq
from app.core.config import get_settings

settings = get_settings()


def _output_language_code() -> str:
    raw = (settings.llm_output_language or "vi").strip().lower()
    if raw in {"vi", "vi-vn", "vietnamese", "tieng viet", "tiếng việt"}:
        return "vi"
    if raw in {"en", "en-us", "en-gb", "english"}:
        return "en"
    return raw or "vi"


def _output_language_name() -> str:
    code = _output_language_code()
    if code == "vi":
        return "Vietnamese"
    if code == "en":
        return "English"
    return settings.llm_output_language or "Vietnamese"


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


def is_gemini_available() -> bool:
    """Check if Gemini or Groq is configured and usable."""
    provider = _select_provider()
    if provider != "mock":
        return True
    print("[AI] No AI API key configured (Gemini or Groq)")
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
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                return (getattr(response, "text", None) or "").strip()
            except Exception:
                # Fallback: inline system prompt if SDK config signature differs
                merged_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = client.models.generate_content(
                    model=model_name,
                    contents=merged_prompt,
                )
                return (getattr(response, "text", None) or "").strip()
        if genai_legacy:
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel(
                model_name=model_name,
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
        print(f"[gemini] generate error: {exc}")
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
        return ""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[groq] generate error: {exc}")
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
        return ""
    resp = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


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
- Prefer responding in {_output_language_name()} (configured default).
- If the user explicitly asks for another language, follow the user request.
"""

    async def chat(self, message: str, context: Optional[str] = None) -> str:
        if self.provider == "mock":
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
                self.history.append({"user": full_prompt, "assistant": assistant_message})
                return self._clean_markdown(assistant_message)
                
        except Exception as e:
            import traceback
            print(f"[{self.provider}] Chat error: {e}")
            print(traceback.format_exc())
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
        prompt = f"""You are MINUTE AI, a meeting and study-session copilot.
Create a rich {language_name} summary using ONLY the JSON data below. Do not invent facts.

Rules:
- Output language: {language_name}.
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
        result: Dict[str, Any] = {}
        try:
            result = json.loads(response)
        except Exception:
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(0))
                except Exception:
                    result = {}

        summary = ""
        key_points: List[str] = []
        if isinstance(result, dict):
            summary = str(result.get("summary", "") or "")
            raw_points = result.get("key_points", [])
            if isinstance(raw_points, list):
                key_points = [str(item) for item in raw_points if str(item).strip()]
            elif raw_points:
                key_points = [str(raw_points)]
        if not summary and not key_points:
            summary = response.strip()

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
        prompt = f"""You are MINUTE AI, generating professional meeting minutes for business teams.
Analyze the transcript below and produce a detailed, factual minutes JSON.

TRANSCRIPT:
{transcript[:20000]}

OUTPUT REQUIREMENTS (Strict JSON Mode):
- Return exactly ONE JSON object only (no markdown code fence, no commentary).
- Output language: {language_name}.
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
        
        # Robust JSON extraction
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            import re
            # Try to find JSON block match
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
            
            # Extract markdown code block if present  
            code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
            if code_block:
                try:
                    return json.loads(code_block.group(1))
                except:
                    pass
            
            # Fallback structure with raw response as summary
            print(f"[AI] Failed to parse JSON minutes, using fallback")
            return {
                "executive_summary": response[:1000],
                "key_points": [],
                "action_items": [],
                "decisions": [],
                "risks": [],
                "next_steps": [],
                "attendees_mentioned": [],
                "study_pack": None
            }
    
    async def generate_summary(self, transcript: str) -> str:
        """Generate meeting summary"""
        language_name = _output_language_name()
        prompt = f"""Create a detailed {language_name} meeting summary from the transcript below.
Use only transcript evidence and do not hallucinate.
Never return an empty response.
If transcript is short, still provide a useful preliminary summary and clearly list missing context.

Transcript:
{transcript[:3000]}

Format:
## Meeting Summary

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
- ...
"""
        
        return await self.chat.chat(prompt)
