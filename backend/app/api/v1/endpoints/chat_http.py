"""
AI Chat HTTP Endpoints
Handles synchronous chat requests with Groq LLM (replaces Gemini)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4
from typing import Optional
import json

from app.db.session import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSession,
    ChatSessionList,
    HomeAskRequest,
    GenerateAgendaRequest,
    ExtractItemsRequest,
    GenerateSummaryRequest,
    AIGenerationResponse,
)
from app.llm.gemini_client import GeminiChat, MeetingAIAssistant, is_gemini_available

router = APIRouter()

HOME_ASK_CONTEXT = """MeetMate | Tro ly hop thong minh cho "AI-First Workplace" tai LPBank
(Desktop app + Teams add-in, RAG + LLM + Tool-Calling)

1. Problem Summary - Van de trong hop tai doanh nghiep lon
- Bien ban hop ghi thu cong, phat hanh cham; sai/thieu y chinh, kho tong hop action items.
- Nguoi hop phai vua lang nghe vua ghi chep -> mat tap trung, bo sot quyet dinh.
- Tai lieu rai rac (LOffice, SharePoint/OneDrive, email, wiki) -> kho tra nhanh khi dang hop.
- Sau hop kho theo doi cong viec: ai lam gi, deadline khi nao; cap nhat tien do roi rac.
- Nhieu cuoc hop noi bo LPBank (da phong ban) can tuan thu bao mat, luu tru, kiem toan.

2. Solution Overview - Giai phap tong quan
MeetMate la tro ly AI da giai doan (Pre-Meeting -> In-Meeting -> Post-Meeting), tich hop sau Google Meet/VNPT GoMeet & LOffice.
Muc tieu: Chuan hoa quy trinh hop, giam ghi chep thu cong, tang kha nang theo doi cong viec sau hop.

2.1 Pre-Meeting (chuan bi truoc hop)
- Tu dong bo lich tu Outlook/Teams; nhan dien chu de/doi tuong/don vi tham gia.
- RAG tim tai lieu lien quan (de an, policy, KPI, quyet dinh truoc) tu LOffice/SharePoint.
- Goi y agenda + "pre-read pack", gui mail/Teams cho nguoi tham du.
- Thu thap input truoc hop (note, cau hoi, rui ro, yeu cau demo) de toi uu thoi luong.

2.2 In-Meeting (tro ly realtime)
- Join tu dong bang bot/desktop app; ASR + diarization -> transcript theo tung nguoi noi (vi/en).
- Live recap theo moc thoi gian; "ask-AI" ngay trong cuoc hop (tra cuu policy/so lieu qua RAG)
- Nhan dien quyet dinh, action items, risks theo ngu canh; hien thi bang viec ngay panel.
- Tool-calling: tao task (Planner/Jira), dat lich follow-up, mo tai lieu lien quan, ghi poll/vote.
- Co-host etiquette: khong lam gian doan; chi "noi khi duoc goi", uu tien hien thi sidebar.

2.3 Post-Meeting (ket thuc & theo doi)
- Executive summary (muc tieu, quyet dinh, action/owner/deadline, rui ro, next steps).
- Dong bo task ve cong cu LPBank dung (LOffice Work, Microsoft Planner/Jira/TFS).
- Video highlights (trich doan keypoints), timeline + transcript co tim kiem nhu Fathom.
- Luu tru transcript/summary co ma hoa, phan quyen, audit trail; cho phep Q&A sau hop.

Gia tri mang lai:
- Truoc hop: co mot agent tong hop, tim hieu va len san agenda chi tiet, chuyen nghiep nhat de cac stage sau su dung, va gui cho cac phong ban lien quan tham khao.
- Trong hop: co thu ky ao realtime, recap mach lac; hoi-dap tai lieu noi bo ngay tai cho.
- Sau hop: bien ban chuan hoa, action/owner/deadline ro rang; tu sync Planner/Jira/LOffice Work.
- Ve dai han: hinh thanh "organizational memory" - tim lai moi quyet dinh/rui ro theo du an/phong ban.

3. Tong quan cach MeetMate hoat dong (non-tech)
3.1 Pre-Meeting - Chuan bi thong minh
- Dong bo lich (Outlook/Teams), hieu chu de & don vi tham du
- RAG tim dung de an/policy/KPI/bien ban cu theo quyen truy cap
- De xuat agenda + pre-read pack co trich dan nguon; gui Teams/email

3.2 In-Meeting - Tro ly realtime
- Bot/desktop app join tu dong -> transcript theo speaker (vi/en).
- Live recap tung moc; phat hien Decision/Action/Risk (bang viec hien ngay panel).
- Ask-AI: tra policy/so lieu qua RAG co phan quyen.
- Tool-calling: tao task, dat lich follow-up, mo tai lieu, poll/vote -> 1-click confirm.

3.3 Post-Meeting - Tong hop & theo doi
- Executive summary (muc tieu, quyet dinh, action/owner/deadline, rui ro, next steps).
- Highlights video (diem nhan + timecode), transcript co tim kiem nhu Fathom.
- Dong bo task ve Planner/Jira/LOffice Work; nhac deadline; Q&A sau hop.

4. Cong nghe chinh (tom gon)
- LLM Orchestrator (LangGraph/LangChain): 1 pipeline, 3 mode theo giai doan.
- ASR streaming enterprise + diarization; tu vung nganh ngan hang.
- RAG (pgvector/Milvus): ingestion tu LOffice/SharePoint/OneDrive/wiki/email, OCR PDF, chunk 400-800 tokens, permission-aware.
- Tool-calling: Microsoft Graph (Teams/Outlook/Planner), Jira/TFS, LOffice API.
- Guardrails: "no-source -> no-answer", chan prompt-injection, PII masking, audit trail.

5. Phu hop tieu chi VNPT AI
5.1 Tinh phu hop de bai (25d)
- Giam ghi chep thu cong, tang theo doi sau hop dung muc tieu BTC.
- Phan tich pain point & neu "vi sao AI": ASR + LLM + RAG + tool-calling la loi.
- Tich hop Teams & LOffice cua LPBank (thuc tien trien khai).

5.2 Tinh doi moi & khac biet (20d)
- Co-host realtime tieng Viet, RAG theo quyen tai lieu, trich dan bat buoc.
- Khac biet >= 30% so voi tool chi "ghi am -> transcript": MeetMate dieu phoi cong viec end-to-end (tao task, dat lich, highlights, Q&A).
- Router provider-first (Azure/AWS/GCP) + Private Link -> an toan + linh hoat.

5.3 Tinh kha thi (25d)
- Nguon du lieu hop phap: audio cuoc hop, tai lieu noi bo da phan quyen.
- Trien khai kha thi: Enterprise API + RAG noi bo; khong can doi MLOps nang.
- Bao mat: ma hoa, RBAC/ABAC, zero-retention, audit; tuan thu quy dinh VN.
- Roadmap & GTM: pilot -> MVP -> enterprise (chi tiet o muc 8).

5.4 Tac dong du kien (20d)
- Tiet kiem thoi gian: vi du 100 cuoc/ngay x tiet kiem 15 phut/cuoc = 25 gio/ngay.
- Giam ty le hoan thanh action (co owner/deadline, nhac han).
- Giam rui ro tuan thu (bien ban chuan, truy vet day du).
- Tao "organizational memory" -> giam hop lap lai, nhanh ra quyet dinh.

5.5 Chat luong ho so (10d)
- Tai lieu <=5 trang, ngon ngu ro, suc tich; co wireframe y tuong va bang bam tieu chi.

6. Kien truc
- Client: Desktop app + Teams add-in (panel Live Notes/Actions/Ask-AI).
- Gateway: "content firewall" (mask PII truoc khi goi LLM API).
- ASR: Streaming enterprise; tra transcript + speaker.
- Agent: Orchestrator chon profile (pre/in/post), goi RAG va tools khi can.
- RAG: vector DB noi bo; chi tra trich doan lien quan + citations.
- Store: Minutes/Action/Decision/Risk, highlights, audit trail; retention policy.

7. Chi so do luong (KPIs)
- Thoi gian phat hanh minutes (muc tieu: <10 phut sau hop).
- Do tre recap live (muc tieu: <2-3s).
- WER ASR vi/en theo domain; precision/recall action items (QA noi bo).
- % action hoan thanh dung han, % cuoc hop co minutes tu dong.
- Muc do su dung: so luot Ask-AI, luot mo highlights/Q&A sau hop.

8. Lo trinh & GTM
- GD0 - POC (1 don vi nghiep vu):
  Join Teams, ASR realtime, recap live, minutes co ban; RAG 1-2 kho tai lieu.
- GD1 - MVP (mo rong 3-5 don vi):
  Action/Decision/Risk extractor; sync Planner/Jira/LOffice Work; Ask-AI co citations.
- GD2 - Enterprise:
  Guardrails day du, archive tuan thu, dashboard chat luong, highlights video.
- GD3 - Mo rong:
  Phan tich xu huong hop theo du an/don vi; da kenh (phong hop vat ly).

9. Uoc tinh tac dong & chi phi (khung tinh)
Case vi du: 100 cuoc/ngay x 15 phut tiet kiem/cuoc = 1.500 phut/ngay ~= 25 gio/ngay.
Neu chi phi lao dong quy doi 300k VND/gio -> ~7,5 trieu VND/ngay; ~165 trieu VND/thang (22 ngay).

Khung chi phi (pilot):
- ASR theo phut audio + LLM theo token + ha tang tich hop.
- Cong thuc: Tong phut hop x don gia ASR + Tong token x don gia LLM + chi phi dev/ops.
- Toi uu: router fast/strong, nen ngu canh, cache, batch post-meeting.

10. Khac biet & vi sao kho bat chuoc
- RAG theo quyen tai lieu LOffice/SharePoint (permission-aware) + citations bat buoc.
- Realtime co-host tieng Viet (agenda adherence, action/risk mining).
- Tool-calling chuan hoa he sinh thai LPBank (Planner/Jira/LOffice Work).
- Governance: content firewall, zero-retention, audit trail, version pinning.

11. Rui ro chinh & phuong an giam thieu
- Bao mat du lieu hop -> Private Link, PII masking, RBAC/ABAC, audit.
- ASR tieng Viet chuyen nganh -> tu dien domain, tinh chinh lexicon, QA dinh ky.
- Hallucination -> "no-source, no-answer", bat buoc citations tu RAG.
- Vendor lock-in -> Model Gateway ho tro nhieu provider & fallback.
- Thay doi thoi quen nguoi dung -> UI toi gian, 1-click confirm, dao tao nhanh.
"""

HOME_ASK_SYSTEM_PROMPT = f"""Ban la MeetMate Assistant cho LPBank.

Quy tac bat buoc:
- Chi su dung thong tin nam trong <context>.
- Neu cau hoi khong nam trong context hoac qua chuyen sau/ngoai pham vi, tra loi: "Minh chua co thong tin ve noi dung do trong tai lieu MeetMate hien tai. Ban co the hoi ve MeetMate, LPBank va cac muc trong mo ta."
- Neu nguoi dung chao hoi, cam on, chia se cam xuc hoac hoi dap giao tiep co ban, hay phan hoi than thien va goi y co the hoi ve MeetMate.
- Khong bịa, khong suy doan ngoai context, khong dua thong tin moi.
- Tra loi bang tieng Viet, van noi tu nhien, 1-5 cau, khong markdown.

<context>
{HOME_ASK_CONTEXT}
</context>
"""

HOME_ASK_MOCK_RESPONSE = (
    "MeetMate la tro ly hop thong minh cho AI-First Workplace tai LPBank. "
    "Ung dung ho tro truoc, trong va sau cuoc hop: tu dong agenda, recap, "
    "bien ban, action items va theo doi cong viec. "
    "Nen tang gom desktop app + Teams add-in, ket hop RAG, LLM va tool-calling."
)


# Store chat sessions in memory (for demo - use Redis in production)
chat_sessions: dict = {}


def get_or_create_session(session_id: Optional[str], meeting_id: Optional[str]) -> tuple:
    """Get existing session or create new one"""
    if session_id and session_id in chat_sessions:
        return session_id, chat_sessions[session_id]
    
    new_id = session_id or str(uuid4())
    chat_sessions[new_id] = {
        'id': new_id,
        'meeting_id': meeting_id,
        'chat': GeminiChat(),
        'messages': [],
        'created_at': datetime.utcnow(),
    }
    return new_id, chat_sessions[new_id]


@router.get('/status')
def get_ai_status():
    """Check if AI is available"""
    from app.core.config import get_settings
    settings = get_settings()
    
    return {
        'groq_available': is_gemini_available(),
        'status': 'ready' if is_gemini_available() else 'mock_mode',
        'model': getattr(settings, 'groq_model', None),
        'api_key_set': bool(getattr(settings, 'groq_api_key', '') and len(getattr(settings, 'groq_api_key', '')) > 10),
        'api_key_preview': (getattr(settings, 'groq_api_key', '')[:8] + '...') if getattr(settings, 'groq_api_key', '') else None
    }


@router.get('/test')
async def test_groq():
    """Test Groq API directly"""
    from app.core.config import get_settings
    from groq import Groq
    
    settings = get_settings()
    
    if not settings.groq_api_key:
        return {'error': 'No API key configured', 'key': None}
    
    try:
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say hello in Vietnamese"}],
            model=settings.groq_model,
            max_tokens=30
        )
        return {
            'success': True,
            'response': resp.choices[0].message.content,
            'model': settings.groq_model
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'model': settings.groq_model,
            'api_key_preview': settings.groq_api_key[:8] + '...' if settings.groq_api_key else None
        }


@router.post('/message', response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message to AI and get response"""
    
    session_id, session = get_or_create_session(request.session_id, request.meeting_id)
    
    # Get meeting context if requested
    context = None
    if request.include_context and request.meeting_id:
        try:
            query = text("""
                SELECT m.title, m.meeting_type, m.description, p.name as project_name
                FROM meeting m
                LEFT JOIN project p ON m.project_id = p.id
                WHERE m.id = :meeting_id
            """)
            result = db.execute(query, {'meeting_id': request.meeting_id})
            row = result.fetchone()
            if row:
                context = f"Cuộc họp: {row[0]}\nLoại: {row[1]}\nMô tả: {row[2]}\nDự án: {row[3]}"
        except Exception:
            pass
    
    # Get AI response
    chat: GeminiChat = session['chat']
    response_text = await chat.chat(request.message, context)
    
    # Save message to session
    session['messages'].append({
        'role': 'user',
        'content': request.message,
        'timestamp': datetime.utcnow()
    })
    session['messages'].append({
        'role': 'assistant',
        'content': response_text,
        'timestamp': datetime.utcnow()
    })
    
    # Save to database if meeting_id provided
    if request.meeting_id:
        try:
            save_query = text("""
                INSERT INTO chat_message (id, session_id, meeting_id, role, content, created_at)
                VALUES (:id, :session_id, :meeting_id, 'user', :user_content, :created_at)
            """)
            db.execute(save_query, {
                'id': str(uuid4()),
                'session_id': session_id,
                'meeting_id': request.meeting_id,
                'user_content': request.message,
                'created_at': datetime.utcnow()
            })
            
            db.execute(save_query.text.replace("'user'", "'assistant'"), {
                'id': str(uuid4()),
                'session_id': session_id,
                'meeting_id': request.meeting_id,
                'user_content': response_text,
                'created_at': datetime.utcnow()
            })
            db.commit()
        except Exception as e:
            print(f"Failed to save chat message: {e}")
    
    return ChatResponse(
        id=str(uuid4()),
        message=response_text,
        role='assistant',
        confidence=0.85 if is_gemini_available() else 0.7,
        created_at=datetime.utcnow()
    )


@router.post('/home', response_model=ChatResponse)
async def home_ask(request: HomeAskRequest):
    """Lightweight home ask endpoint with strict MeetMate context."""
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    chat = GeminiChat(system_prompt=HOME_ASK_SYSTEM_PROMPT, mock_response=HOME_ASK_MOCK_RESPONSE)
    response_text = await chat.chat(message)

    return ChatResponse(
        id=str(uuid4()),
        message=response_text,
        role='assistant',
        confidence=0.85 if is_gemini_available() else 0.7,
        created_at=datetime.utcnow()
    )


@router.get('/sessions', response_model=ChatSessionList)
def list_sessions(
    meeting_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List chat sessions"""
    sessions = []
    
    for sid, session in chat_sessions.items():
        if meeting_id and session.get('meeting_id') != meeting_id:
            continue
        
        sessions.append(ChatSession(
            id=sid,
            meeting_id=session.get('meeting_id'),
            messages=session.get('messages', []),
            created_at=session.get('created_at', datetime.utcnow()),
            updated_at=datetime.utcnow()
        ))
    
    return ChatSessionList(sessions=sessions, total=len(sessions))


@router.get('/sessions/{session_id}', response_model=ChatSession)
def get_session(session_id: str):
    """Get a specific chat session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    return ChatSession(
        id=session_id,
        meeting_id=session.get('meeting_id'),
        messages=session.get('messages', []),
        created_at=session.get('created_at', datetime.utcnow()),
        updated_at=datetime.utcnow()
    )


@router.delete('/sessions/{session_id}')
def delete_session(session_id: str):
    """Delete a chat session"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return {'status': 'deleted'}


# ============================================
# AI GENERATION ENDPOINTS
# ============================================

@router.post('/generate/agenda', response_model=AIGenerationResponse)
async def generate_agenda_ai(
    request: GenerateAgendaRequest,
    db: Session = Depends(get_db)
):
    """Generate meeting agenda using AI"""
    assistant = MeetingAIAssistant(request.meeting_id, {
        'type': request.meeting_type,
    })
    
    result = await assistant.generate_agenda(request.meeting_type)
    
    return AIGenerationResponse(
        id=str(uuid4()),
        result=result,
        confidence=0.85,
        created_at=datetime.utcnow()
    )


@router.post('/extract/items', response_model=AIGenerationResponse)
async def extract_items_ai(
    request: ExtractItemsRequest,
    db: Session = Depends(get_db)
):
    """Extract action items, decisions, or risks from transcript"""
    assistant = MeetingAIAssistant(request.meeting_id)
    
    if request.item_type == 'actions':
        result = await assistant.extract_action_items(request.transcript)
    elif request.item_type == 'decisions':
        result = await assistant.extract_decisions(request.transcript)
    elif request.item_type == 'risks':
        result = await assistant.extract_risks(request.transcript)
    else:
        raise HTTPException(status_code=400, detail="Invalid item_type")
    
    return AIGenerationResponse(
        id=str(uuid4()),
        result=result,
        confidence=0.80,
        created_at=datetime.utcnow()
    )


@router.post('/generate/summary', response_model=AIGenerationResponse)
async def generate_summary_ai(
    request: GenerateSummaryRequest,
    db: Session = Depends(get_db)
):
    """Generate meeting summary from transcript"""
    assistant = MeetingAIAssistant(request.meeting_id)
    
    result = await assistant.generate_summary(request.transcript)
    
    return AIGenerationResponse(
        id=str(uuid4()),
        result=result,
        confidence=0.85,
        created_at=datetime.utcnow()
    )
