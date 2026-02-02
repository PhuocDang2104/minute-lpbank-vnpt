"""
LLM Client via Groq (replaces legacy Gemini usage)
"""
import json
from typing import Optional, List, Dict, Any
from groq import Groq
from app.core.config import get_settings

settings = get_settings()


def get_gemini_client():
    """Return Groq client (legacy name kept for compatibility)."""
    if not settings.groq_api_key:
        return None
    return Groq(api_key=settings.groq_api_key)


def is_gemini_available() -> bool:
    """Check if Groq API key is configured."""
    if not settings.groq_api_key:
        print("[Groq] No API key configured")
        return False
    try:
        client = Groq(api_key=settings.groq_api_key)
        client.chat.completions.create(
            messages=[{"role": "user", "content": "ping"}],
            model=settings.groq_model,
            max_tokens=8,
        )
        return True
    except Exception as e:
        print(f"[Groq] API error: {e}")
        return False


class GeminiChat:
    """Chat wrapper using Groq chat completions."""
    
    def __init__(self, system_prompt: Optional[str] = None, mock_response: Optional[str] = None):
        self.client = get_gemini_client()
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.mock_response = mock_response or "AI dang o che do mock, chua cau hinh GROQ_API_KEY."
        self.history: List[Dict[str, str]] = []
    
    def _default_system_prompt(self) -> str:
        return """Bạn là MeetMate AI Assistant - trợ lý thông minh cho PMO (Project Management Office) của ngân hàng LPBank.

Nhiệm vụ của bạn:
1. Hỗ trợ chuẩn bị cuộc họp (Pre-meeting): Gợi ý agenda, tài liệu, người tham gia
2. Hỗ trợ trong cuộc họp (In-meeting): Ghi chép, phát hiện action items, decisions, risks
3. Hỗ trợ sau cuộc họp (Post-meeting): Tạo biên bản, theo dõi tasks, Q&A

Nguyên tắc:
- Trả lời tiếng Việt, ngắn gọn, không markdown.
- Nếu không chắc chắn, nói rõ "Tôi không có thông tin về điều này".
"""

    async def chat(self, message: str, context: Optional[str] = None) -> str:
        if not self.client:
            return self._mock_response(message)
        try:
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            if context:
                messages.append({"role": "system", "content": f"Context:\n{context}"})
            for h in self.history[-5:]:
                messages.append({"role": "user", "content": h["user"]})
                messages.append({"role": "assistant", "content": h["assistant"]})
            messages.append({"role": "user", "content": message})

            resp = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
            )
            assistant_message = resp.choices[0].message.content
            assistant_message = self._clean_markdown(assistant_message)
            self.history.append({"user": message, "assistant": assistant_message})
            return assistant_message
        except Exception as e:
            import traceback
            print(f"[Groq] Chat error: {e}")
            print(traceback.format_exc())
            return self._mock_response(message)
    
    def _clean_markdown(self, text: str) -> str:
        import re
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def _mock_response(self, message: str) -> str:
        return self.mock_response


class MeetingAIAssistant:
    """AI Assistant for meeting context (uses Groq)"""
    
    def __init__(self, meeting_id: str, meeting_context: Optional[Dict[str, Any]] = None):
        self.meeting_id = meeting_id
        self.meeting_context = meeting_context or {}
        self.chat = GeminiChat()
    
    def _build_context(self) -> str:
        ctx_parts = []
        if self.meeting_context.get('title'):
            ctx_parts.append(f"Cuộc họp: {self.meeting_context['title']}")
        if self.meeting_context.get('type'):
            ctx_parts.append(f"Loại: {self.meeting_context['type']}")
        if self.meeting_context.get('project'):
            ctx_parts.append(f"Dự án: {self.meeting_context['project']}")
        if self.meeting_context.get('agenda'):
            ctx_parts.append(f"Agenda: {self.meeting_context['agenda']}")
        if self.meeting_context.get('transcript'):
            ctx_parts.append(f"Transcript (trích): {self.meeting_context['transcript'][:500]}...")
        return "\n".join(ctx_parts)
    
    async def ask(self, question: str) -> str:
        context = self._build_context()
        return await self.chat.chat(question, context)
    
    async def generate_agenda(self, meeting_type: str) -> str:
        prompt = f"""Tạo chương trình cuộc họp chi tiết cho loại: {meeting_type}

Yêu cầu JSON:
[{{"order":1,"title":"...","duration_minutes":10,"presenter":"..."}}]"""
        return await self.chat.chat(prompt)
    
    async def extract_action_items(self, transcript: str) -> str:
        prompt = f"""Trích Action Items từ transcript:
{transcript[:2000]}
Format JSON: [{{"description":"","owner":"","deadline":"","priority":""}}]"""
        return await self.chat.chat(prompt)
    
    async def extract_decisions(self, transcript: str) -> str:
        prompt = f"""Trích Decisions từ transcript:
{transcript[:2000]}
Format JSON: [{{"description":"","rationale":"","confirmed_by":""}}]"""
        return await self.chat.chat(prompt)
    
    async def extract_risks(self, transcript: str) -> str:
        prompt = f"""Trích Risks từ transcript:
{transcript[:2000]}
Format JSON: [{{"description":"","severity":"","mitigation":""}}]"""
        return await self.chat.chat(prompt)
    
    async def generate_summary(self, transcript: str) -> str:
        prompt = f"""Tóm tắt cuộc họp từ transcript:
{transcript[:3000]}
"""
        return await self.chat.chat(prompt)


class MeetingAIAssistant:
    """AI Assistant specifically for meeting context"""
    
    def __init__(self, meeting_id: str, meeting_context: Optional[Dict[str, Any]] = None):
        self.meeting_id = meeting_id
        self.meeting_context = meeting_context or {}
        self.chat = GeminiChat()
    
    def _build_context(self) -> str:
        """Build context string from meeting data"""
        ctx_parts = []
        
        if self.meeting_context.get('title'):
            ctx_parts.append(f"Cuộc họp: {self.meeting_context['title']}")
        
        if self.meeting_context.get('type'):
            ctx_parts.append(f"Loại: {self.meeting_context['type']}")
        
        if self.meeting_context.get('project'):
            ctx_parts.append(f"Dự án: {self.meeting_context['project']}")
        
        if self.meeting_context.get('agenda'):
            ctx_parts.append(f"Agenda: {self.meeting_context['agenda']}")
        
        if self.meeting_context.get('transcript'):
            ctx_parts.append(f"Transcript (trích): {self.meeting_context['transcript'][:500]}...")
        
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

{transcript[:2000]}

Format output JSON:
[
  {{
    "description": "Mô tả task",
    "owner": "Tên người được giao (nếu có)",
    "deadline": "Deadline (nếu được đề cập)",
    "priority": "high/medium/low"
  }}
]"""
        
        return await self.chat.chat(prompt)
    
    async def extract_decisions(self, transcript: str) -> str:
        """Extract decisions from transcript"""
        prompt = f"""Phân tích transcript sau và trích xuất các Quyết định (Decisions):

{transcript[:2000]}

Format output JSON:
[
  {{
    "description": "Nội dung quyết định",
    "rationale": "Lý do (nếu có)",
    "confirmed_by": "Người xác nhận"
  }}
]"""
        
        return await self.chat.chat(prompt)
    
    async def extract_risks(self, transcript: str) -> str:
        """Extract risks from transcript"""
        prompt = f"""Phân tích transcript sau và trích xuất các Rủi ro (Risks):

{transcript[:2000]}

Format output JSON:
[
  {{
    "description": "Mô tả rủi ro",
    "severity": "critical/high/medium/low",
    "mitigation": "Biện pháp giảm thiểu (nếu có)"
  }}
]"""
        
        return await self.chat.chat(prompt)

    async def generate_summary_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meeting summary with full context and strict guardrails."""
        prompt = f"""Bạn là trợ lý tạo biên bản cuộc họp.
Hãy tóm tắt dựa trên dữ liệu JSON bên dưới và KHÔNG bịa thông tin.

Quy tắc:
- Chỉ dùng dữ liệu đã cung cấp.
- Nếu transcript, description, actions, decisions, risks, documents đều rỗng:
  - Nếu title đủ cụ thể thì cho phép suy đoán 1-2 câu, bắt đầu bằng "Ước đoán: ".
  - Nếu title quá chung chung (vd: "Meeting", "Cuộc họp", "Sync", "Họp nhanh") thì trả về summary rỗng.
- Nếu có dữ liệu, tóm tắt 2-5 câu, ngắn gọn.
- key_points: 3-5 gạch đầu dòng rút từ transcript hoặc actions/decisions/risks; nếu không có thì [].

Dữ liệu:
{json.dumps(context, ensure_ascii=False)}

Trả về đúng JSON, không kèm text khác:
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
        return {"summary": summary, "key_points": key_points}
    
    async def generate_minutes_json(self, transcript: str) -> Dict[str, Any]:
        """Generate comprehensive minutes in strict JSON format with rich content"""
        prompt = f"""Bạn là trợ lý chuyên nghiệp tạo biên bản cuộc họp cho doanh nghiệp.
Phân tích nội dung cuộc họp (transcript) bên dưới và tạo biên bản chi tiết.

TRANSCRIPT CUỘC HỌP:
{transcript[:15000]}

YÊU CẦU OUTPUT (JSON Strict Mode):
Trả về MỘT JSON Object duy nhất (KHÔNG kèm markdown block ```json```) với cấu trúc:

{{
    "executive_summary": "Tóm tắt điều hành 2-4 đoạn văn. Bắt đầu bằng mục đích cuộc họp, các nội dung chính đã thảo luận, kết quả đạt được và những điều cần theo dõi.",
    
    "key_points": [
        "Điểm thảo luận quan trọng 1 - mô tả ngắn gọn nội dung và ai đề cập",
        "Điểm thảo luận quan trọng 2 - kết quả hoặc kết luận",
        "Điểm thảo luận quan trọng 3"
    ],
    
    "action_items": [
        {{
            "description": "Mô tả chi tiết công việc cần thực hiện",
            "owner": "Tên người được giao (trích từ transcript, nếu không rõ ghi 'Chưa phân công')",
            "deadline": "YYYY-MM-DD nếu đề cập, hoặc 'Sớm nhất có thể' nếu urgent, hoặc null",
            "priority": "high/medium/low - dựa vào mức độ nhấn mạnh trong cuộc họp",
            "created_by": "Tên người tạo ra yêu cầu này trong cuộc họp"
        }}
    ],
    
    "decisions": [
        {{
            "description": "Nội dung quyết định rõ ràng, cụ thể",
            "rationale": "Lý do dẫn đến quyết định này (tóm tắt thảo luận)",
            "decided_by": "Tên người chốt quyết định cuối cùng",
            "approved_by": "Những người đồng ý/phê duyệt (nếu có)"
        }}
    ],
    
    "risks": [
        {{
            "description": "Mô tả rủi ro hoặc vấn đề tiềm ẩn được nêu ra",
            "severity": "critical/high/medium/low",
            "mitigation": "Biện pháp giảm thiểu đã thảo luận",
            "raised_by": "Người nêu ra rủi ro này"
        }}
    ],
    
    "next_steps": [
        "Bước tiếp theo 1 cần thực hiện sau cuộc họp",
        "Bước tiếp theo 2"
    ],
    
    "attendees_mentioned": [
        "Tên người tham gia được nhắc đến trong transcript"
    ]
}}

LƯU Ý QUAN TRỌNG:
- Trích xuất TẤT CẢ thông tin có trong transcript, không bỏ sót
- Với mỗi action/decision/risk, PHẢI ghi rõ ai là người tạo/đề xuất/quyết định
- Nếu không xác định được người, ghi "Không rõ" thay vì bỏ trống
- Priority: high = được nhấn mạnh nhiều lần, medium = đề cập bình thường, low = đề cập qua
- executive_summary phải viết như văn bản chuyên nghiệp, có đầu có đuôi
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
                "attendees_mentioned": []
            }
    
    async def generate_summary(self, transcript: str) -> str:
        """Generate meeting summary"""
        prompt = f"""Tạo tóm tắt cuộc họp dựa trên transcript sau, không bịa thông tin.
Nếu transcript trống hoặc không đủ dữ liệu thì trả về chuỗi rỗng.

{transcript[:3000]}

Format:
## Tóm tắt cuộc họp

### Các điểm chính
- ...

### Quyết định
- ...

### Action Items
- ...

### Rủi ro được đề cập
- ...

### Bước tiếp theo
- ..."""
        
        return await self.chat.chat(prompt)
