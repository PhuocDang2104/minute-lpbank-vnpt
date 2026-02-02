"""
AI Service - Mock implementations for demo
In production, this would integrate with LangChain/LangGraph agents
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.ai import (
    AgendaItem, AgendaProposal, GenerateAgendaResponse,
    PrereadDocument, PrereadDocumentList,
    RAGResponse, Citation, RAGHistory,
    MeetingSuggestion, SuggestionList
)


# ============================================
# MOCK AI AGENDA GENERATION
# ============================================

MOCK_AGENDAS = {
    'steering': [
        AgendaItem(order=1, title='Khai mạc & Điểm danh', duration_minutes=5, presenter='Chủ tịch'),
        AgendaItem(order=2, title='Báo cáo tiến độ dự án', duration_minutes=15, presenter='PM'),
        AgendaItem(order=3, title='Review Budget & Resources', duration_minutes=10, presenter='PMO'),
        AgendaItem(order=4, title='Thảo luận Risks & Issues', duration_minutes=15, presenter='Risk Manager'),
        AgendaItem(order=5, title='Quyết định & Action Items', duration_minutes=10, presenter='Chủ tịch'),
        AgendaItem(order=6, title='Kết luận & Bước tiếp theo', duration_minutes=5, presenter='Chủ tịch'),
    ],
    'weekly_status': [
        AgendaItem(order=1, title='Sprint Review - Demo Features', duration_minutes=20, presenter='Dev Lead'),
        AgendaItem(order=2, title='Blockers & Dependencies', duration_minutes=10, presenter='Scrum Master'),
        AgendaItem(order=3, title='Kế hoạch Sprint tiếp theo', duration_minutes=15, presenter='PO'),
        AgendaItem(order=4, title='Q&A', duration_minutes=10),
    ],
    'risk_review': [
        AgendaItem(order=1, title='Review Risk Register', duration_minutes=15, presenter='Risk Manager'),
        AgendaItem(order=2, title='Đánh giá rủi ro mới', duration_minutes=20),
        AgendaItem(order=3, title='Mitigation Plans', duration_minutes=15),
        AgendaItem(order=4, title='Escalation Items', duration_minutes=10, presenter='PM'),
    ],
    'workshop': [
        AgendaItem(order=1, title='Giới thiệu & Mục tiêu', duration_minutes=10, presenter='Facilitator'),
        AgendaItem(order=2, title='Brainstorming Session', duration_minutes=30),
        AgendaItem(order=3, title='Group Discussion', duration_minutes=20),
        AgendaItem(order=4, title='Tổng hợp & Action Items', duration_minutes=15),
    ],
    'daily': [
        AgendaItem(order=1, title='Yesterday - Đã làm gì?', duration_minutes=5),
        AgendaItem(order=2, title='Today - Sẽ làm gì?', duration_minutes=5),
        AgendaItem(order=3, title='Blockers', duration_minutes=5),
    ],
}


def generate_agenda(db: Session, meeting_id: str, context: Optional[str] = None) -> GenerateAgendaResponse:
    """Generate agenda using AI (mocked)"""
    
    # Get meeting info
    query = text("SELECT meeting_type, title FROM meeting WHERE id = :meeting_id")
    result = db.execute(query, {'meeting_id': meeting_id})
    row = result.fetchone()
    
    meeting_type = row[0] if row else 'weekly_status'
    
    # Get mock agenda based on meeting type
    items = MOCK_AGENDAS.get(meeting_type, MOCK_AGENDAS['weekly_status'])
    
    agenda = AgendaProposal(
        id=str(uuid4()),
        meeting_id=meeting_id,
        items=items,
        status='draft',
        generated_at=datetime.utcnow()
    )
    
    return GenerateAgendaResponse(
        agenda=agenda,
        confidence=0.85
    )


def save_agenda(db: Session, meeting_id: str, items: List[AgendaItem]) -> AgendaProposal:
    """Save agenda to database"""
    import json
    
    agenda_id = str(uuid4())
    now = datetime.utcnow()
    
    # Convert items to JSON
    items_json = [item.model_dump() for item in items]
    
    query = text("""
        INSERT INTO agenda_proposed (id, meeting_id, generated_agenda, status, created_at)
        VALUES (:id, :meeting_id, :agenda, 'draft', :created_at)
        ON CONFLICT (meeting_id) DO UPDATE SET
            generated_agenda = :agenda,
            updated_at = :created_at
        RETURNING id::text, meeting_id::text, generated_agenda, status, created_at
    """)
    
    result = db.execute(query, {
        'id': agenda_id,
        'meeting_id': meeting_id,
        'agenda': json.dumps(items_json),
        'created_at': now
    })
    db.commit()
    
    return AgendaProposal(
        id=agenda_id,
        meeting_id=meeting_id,
        items=items,
        status='draft',
        generated_at=now
    )


# ============================================
# MOCK PRE-READ DOCUMENT SUGGESTIONS
# ============================================

MOCK_DOCUMENTS = [
    {
        'title': 'Project Charter - Core Banking Modernization',
        'source': 'SharePoint',
        'url': 'https://lpbank.sharepoint.com/sites/tech/docs/core-banking-charter.pdf',
        'snippet': 'Tài liệu Project Charter định nghĩa scope, objectives, và key stakeholders cho dự án Core Banking Modernization.',
        'relevance_score': 0.95
    },
    {
        'title': 'Technical Architecture Document v2.1',
        'source': 'SharePoint',
        'url': 'https://lpbank.sharepoint.com/sites/tech/docs/technical-arch-v21.pdf',
        'snippet': 'Kiến trúc kỹ thuật bao gồm system design, API specifications, và integration patterns.',
        'relevance_score': 0.92
    },
    {
        'title': 'NHNN Circular 09/2020 - IT Risk Management',
        'source': 'Wiki',
        'url': 'https://wiki.lpbank.vn/compliance/nhnn-circular-09-2020',
        'snippet': 'Thông tư quy định về quản lý rủi ro CNTT trong hoạt động ngân hàng, bao gồm data retention và security requirements.',
        'relevance_score': 0.88
    },
    {
        'title': 'Sprint 23 Release Notes',
        'source': 'Confluence',
        'url': 'https://confluence.lpbank.vn/display/MB/Sprint+23+Release',
        'snippet': 'Chi tiết các features đã release trong Sprint 23, bao gồm bug fixes và improvements.',
        'relevance_score': 0.85
    },
    {
        'title': 'Risk Assessment Template',
        'source': 'LOffice',
        'url': 'https://loffice.lpbank.vn/docs/risk-assessment-template.docx',
        'snippet': 'Template đánh giá rủi ro cho các dự án tích hợp hệ thống.',
        'relevance_score': 0.82
    },
]


def suggest_documents(db: Session, meeting_id: str, keywords: Optional[List[str]] = None) -> PrereadDocumentList:
    """Suggest pre-read documents using AI (mocked)"""
    
    documents = []
    for i, doc in enumerate(MOCK_DOCUMENTS[:4]):  # Return top 4
        documents.append(PrereadDocument(
            id=str(uuid4()),
            meeting_id=meeting_id,
            title=doc['title'],
            source=doc['source'],
            url=doc['url'],
            snippet=doc['snippet'],
            relevance_score=doc['relevance_score'],
            status='suggested',
            created_at=datetime.utcnow()
        ))
    
    return PrereadDocumentList(documents=documents, total=len(documents))


# ============================================
# MOCK RAG Q&A
# ============================================

MOCK_RAG_RESPONSES = {
    'data retention': {
        'answer': 'Theo Thông tư 09/2020/TT-NHNN về quản lý rủi ro CNTT, thời gian lưu trữ dữ liệu giao dịch (transaction logs) tối thiểu là **10 năm** kể từ ngày phát sinh giao dịch. Đối với dữ liệu khách hàng, thời gian lưu trữ là 5 năm sau khi kết thúc quan hệ khách hàng.',
        'citations': [
            Citation(
                title='Thông tư 09/2020/TT-NHNN',
                source='NHNN',
                page=12,
                snippet='Điều 15: Thời gian lưu trữ dữ liệu giao dịch tối thiểu 10 năm...',
                url='https://wiki.lpbank.vn/compliance/nhnn-circular-09-2020'
            )
        ],
        'confidence': 0.95
    },
    'security': {
        'answer': 'Theo policy của LPBank, tất cả dữ liệu nhạy cảm phải được mã hóa sử dụng **AES-256** cho data at rest và **TLS 1.3** cho data in transit. Penetration testing phải được thực hiện quarterly bởi bên thứ ba độc lập.',
        'citations': [
            Citation(
                title='LPBank Security Policy v3.0',
                source='SharePoint',
                page=8,
                snippet='Section 4.2: Data encryption requirements...',
                url='https://lpbank.sharepoint.com/policies/security-v3.pdf'
            )
        ],
        'confidence': 0.92
    },
    'default': {
        'answer': 'Dựa trên các tài liệu trong knowledge base, tôi tìm thấy một số thông tin liên quan. Tuy nhiên, để có câu trả lời chính xác hơn, bạn có thể cung cấp thêm context hoặc tham khảo trực tiếp các tài liệu được đề xuất bên dưới.',
        'citations': [
            Citation(
                title='Project Documentation Index',
                source='Confluence',
                snippet='Danh mục các tài liệu dự án...',
                url='https://confluence.lpbank.vn/display/DOC/Index'
            )
        ],
        'confidence': 0.65
    }
}


def query_rag(db: Session, query: str, meeting_id: Optional[str] = None) -> RAGResponse:
    """Query the RAG system (mocked)"""
    
    # Simple keyword matching for demo
    query_lower = query.lower()
    
    if 'retention' in query_lower or 'lưu trữ' in query_lower:
        mock = MOCK_RAG_RESPONSES['data retention']
    elif 'security' in query_lower or 'bảo mật' in query_lower or 'mã hóa' in query_lower:
        mock = MOCK_RAG_RESPONSES['security']
    else:
        mock = MOCK_RAG_RESPONSES['default']
    
    # Save query to database
    query_id = str(uuid4())
    if meeting_id:
        try:
            save_query = text("""
                INSERT INTO ask_ai_query (id, meeting_id, query_text, answer_text, citation, created_at)
                VALUES (:id, :meeting_id, :query, :answer, :citation, :created_at)
            """)
            import json
            db.execute(save_query, {
                'id': query_id,
                'meeting_id': meeting_id,
                'query': query,
                'answer': mock['answer'],
                'citation': json.dumps([c.model_dump() for c in mock['citations']]),
                'created_at': datetime.utcnow()
            })
            db.commit()
        except Exception:
            pass  # Ignore save errors for demo
    
    return RAGResponse(
        id=query_id,
        query=query,
        answer=mock['answer'],
        citations=mock['citations'],
        confidence=mock['confidence'],
        created_at=datetime.utcnow()
    )


def get_rag_history(db: Session, meeting_id: str) -> RAGHistory:
    """Get RAG query history for a meeting"""
    
    query = text("""
        SELECT id::text, query_text, answer_text, citation, created_at
        FROM ask_ai_query
        WHERE meeting_id = :meeting_id
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    result = db.execute(query, {'meeting_id': meeting_id})
    rows = result.fetchall()
    
    queries = []
    for row in rows:
        import json
        citations = []
        if row[3]:
            try:
                citation_data = json.loads(row[3]) if isinstance(row[3], str) else row[3]
                citations = [Citation(**c) for c in citation_data]
            except:
                pass
        
        queries.append(RAGResponse(
            id=row[0],
            query=row[1],
            answer=row[2],
            citations=citations,
            confidence=0.85,
            created_at=row[4]
        ))
    
    return RAGHistory(queries=queries, total=len(queries))


# ============================================
# MEETING SUGGESTIONS
# ============================================

MOCK_PERSON_SUGGESTIONS = [
    {
        'title': 'Nguyễn Thị Risk Manager',
        'description': 'Expert về Risk & Compliance, tham gia nhiều dự án Core Banking',
        'reason': 'Có kinh nghiệm với các dự án tương tự',
        'score': 0.88
    },
    {
        'title': 'Trần Văn Security',
        'description': 'Security Architect, chuyên gia penetration testing',
        'reason': 'Meeting có liên quan đến security requirements',
        'score': 0.82
    },
]


def get_meeting_suggestions(db: Session, meeting_id: str) -> SuggestionList:
    """Get AI suggestions for a meeting (people, documents)"""
    
    suggestions = []
    
    # Document suggestions
    for doc in MOCK_DOCUMENTS[:2]:
        suggestions.append(MeetingSuggestion(
            id=str(uuid4()),
            meeting_id=meeting_id,
            suggestion_type='document',
            title=doc['title'],
            description=doc['snippet'][:100],
            reference_url=doc['url'],
            score=doc['relevance_score'],
            status='pending',
            reason='Tài liệu liên quan đến chủ đề cuộc họp'
        ))
    
    # Person suggestions
    for person in MOCK_PERSON_SUGGESTIONS:
        suggestions.append(MeetingSuggestion(
            id=str(uuid4()),
            meeting_id=meeting_id,
            suggestion_type='person',
            title=person['title'],
            description=person['description'],
            score=person['score'],
            status='pending',
            reason=person['reason']
        ))
    
    return SuggestionList(suggestions=suggestions, total=len(suggestions))

