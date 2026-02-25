# MeetMate Backend (FastAPI/WS + LangGraph)

Backend của MeetMate tập trung vào realtime pipeline (audio -> STT -> transcript), điều phối LangGraph theo stage Pre/In/Post, RAG/Knowledge Hub, và tool-calling cho hệ sinh thái doanh nghiệp BFSI.

## Overview
- FastAPI API + WebSocket cho realtime transcript/recap/ADR.
- Stage-aware router (LangGraph) dùng shared `MeetingState`.
- SmartVoice streaming STT (gRPC) + fallback WS ingest cho dev/test.
- RAG/Knowledge Hub: ingest -> chunk -> embed -> pgvector -> grounded Q&A.
- Tool execution API: đề xuất tạo task/đặt lịch/tích hợp hệ thống ngoài.

## Directory Structure
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/          # REST APIs
│   │       └── websocket/          # WS handlers (audio, frontend, ingest)
│   ├── core/                       # config, logging, security
│   ├── db/                         # DB session/init
│   ├── llm/                        # LangGraph router, chains, prompts, tools
│   ├── models/                     # SQLAlchemy models
│   ├── schemas/                    # Pydantic schemas
│   ├── services/                   # business logic + realtime pipeline
│   ├── vectorstore/                # pgvector + retrieval
│   ├── websocket/                  # WS manager/events
│   ├── workers/                    # background tasks
│   └── main.py                     # FastAPI app entry
├── alembic/                        # migrations
├── tests/                          # unit + integration + WS tools
├── protos/                         # SmartVoice gRPC protos
├── protos_compiled/                # compiled protos (optional)
├── local_embeddings/               # local cache (optional)
├── Dockerfile
├── requirements.txt
├── render.yaml
├── env.example.txt
└── alembic.ini
```

## Architecture Notes
### 1) Stage-aware AI Router
- Entry graph trong `app/llm/graphs/router.py` chọn subgraph pre/in/post.
- Shared `MeetingState` định nghĩa tại `app/llm/graphs/state.py` để giữ transcript, ADR, RAG hits và tool suggestions.

### 2) Realtime Pipeline
- Create session: `POST /api/v1/sessions`.
- Audio ingest (prod): `WS /api/v1/ws/audio/{session_id}?token=...` -> SmartVoice STT -> `session_bus`.
- Transcript ingest (dev/test): `WS /api/v1/ws/in-meeting/{session_id}`.
- Frontend egress: `WS /api/v1/ws/frontend/{session_id}` nhận `transcript_event` + `state`.

### 3) RAG & Knowledge Hub
- Upload -> extract text -> chunk -> embed (Jina) -> pgvector.
- Query: `POST /api/v1/knowledge/query` (grounded, citations).
- Vector search: `POST /api/v1/knowledge/search`.

### 4) Tool Execution
- `POST /api/v1/tools/execute` để dispatch tool (task/jira/schedule) qua `app/services/tool_executor.py` (stub).

## Quickstart
### Docker (recommended)
From repo root:
```powershell
cd infra
docker compose up -d --build
```
- API: `http://localhost:8000`
- DB: `localhost:5433` (meetmate/meetmate)

### Local venv
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Configuration
- Local env: `backend/.env.local` hoặc `infra/env/.env.local`.
- Template: `backend/env.example.txt`.

Key variables:
- `DATABASE_URL`
- `SECRET_KEY`, `GOOGLE_OAUTH_CLIENT_ID`
- `GEMINI_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`
- `JINA_API_KEY`, `JINA_EMBED_MODEL`, `JINA_EMBED_DIMENSIONS`
- `SMARTVOICE_GRPC_ENDPOINT`, `SMARTVOICE_ACCESS_TOKEN`, `SMARTVOICE_TOKEN_ID`, `SMARTVOICE_TOKEN_KEY`
- `GOMEET_API_BASE_URL`, `GOMEET_PARTNER_TOKEN`
- `SUPABASE_S3_*`, `SMTP_*`, `EMAIL_ENABLED`

## Testing
```powershell
cd backend
pytest
```
WS demo scripts: `backend/tests/README.md`.

## Deployment
- Docker image: `backend/Dockerfile` (context: repo root).
- Render: `backend/render.yaml`.
- DB bootstrap: `infra/postgres/init/*.sql`.

## References
- Realtime spec: `docs/in_meeting_flow.md`, `docs/real_time_transcript.md`
- API contracts: `docs/api_contracts.md`
- RAG: `docs/rag_architecture.md`, `docs/knowledge_vector_search.md`
