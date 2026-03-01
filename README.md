# MINUTE - Multimodal Meeting & Study Companion (Gemini Hackathon 3)

**Web app + Realtime/Record processing | Gemini 3 API | Tiered LightRAG | Tool-calling (human-in-the-loop)**

MINUTE standardizes the lifecycle of a session (meeting or study): realtime support during the session, post-session summarization, and context-aware Q&A with citations. The system prioritizes grounded answers from internal materials, while allowing controlled web-search expansion through policy and user approval.

<p align="center">
  <img src="https://img.shields.io/badge/Client-Web%20App%20%2B%20Vite%20%2B%20React-1f6feb" alt="Client">
  <img src="https://img.shields.io/badge/Backend-WebSocket%20%2B%20FastAPI%20%2B%20Postgres-2da44e" alt="Backend">
  <img src="https://img.shields.io/badge/AI-Gemini%203%20%2B%20LightRAG%20%2B%20Tool--Calling-f97316" alt="AI">
  <img src="https://img.shields.io/badge/Realtime-ASR%20%2B%20Visual%20Timeline%20%2B%20Recap-0ea5e9" alt="Realtime">
</p>

## Table of Contents
- **Product**: [Overview](#overview) | [Problem Summary](#problem-summary) | [Solution Overview (Pre/In/Post)](#solution-overview-preinpost) | [Product Goals & Target Users](#product-goals--target-users)
- **Architecture**: [MINUTE AI Architecture](#minute-ai-architecture) | [System Architecture (5 Layers)](#system-architecture-5-layers) | [AI Components (MINUTE Platform)](#ai-components-minute-platform) | [Architecture Diagrams](#architecture-diagrams)
- **Build & Ops**: [Key Capabilities](#key-capabilities) | [Tech Stack](#tech-stack) | [Repository Structure](#repository-structure) | [Quickstart (1 command)](#quickstart-1-command) | [Development](#development) | [Configuration](#configuration) | [API & Realtime](#api--realtime) | [Data Model](#data-model) | [RAG & Knowledge Hub](#rag--knowledge-hub) | [Security & Compliance](#security--compliance) | [Observability & KPIs](#observability--kpis) | [Deployment](#deployment) | [Test Automation Guide](#test-automation-guide)
- **Project**: [Roadmap](#roadmap) | [Docs](#docs) | [Development Team](#development-team) | [Mentor Acknowledgements](#mentor-acknowledgements) | [Contributing](#contributing)

## Overview
- Task router by `task_type`: `realtime_recap` -> `qna` -> `summary_generate`.
- Multimodal realtime processing: streaming ASR audio + timestamped video/frame events.
- Tiered LightRAG: Tier 0 (session memory), Tier 1 (uploaded docs), Tier 2 (approved web search), Tier 3 (deep research when needed).
- Human-in-the-loop tool-calling: propose -> approve -> execute with audit trail.
- Session-type outputs: meeting (minutes/action/decision/risk) and study (concept/example/quiz).

## Problem Summary
- Manual note-taking delays summary/minutes delivery and often misses key actions/decisions.
- In live sessions, users struggle to track both spoken content and on-screen visual context.
- Post-session Q&A is often weakly grounded because transcript, recording, and references are fragmented.
- There is no controlled knowledge expansion path when internal evidence is insufficient.
- Sensitive actions (web search, export/share, write actions) require policy, retention, and auditable control.

## Solution Overview (Pre/In/Post)
| Stage | Goal | Main Output | Related Systems |
| --- | --- | --- | --- |
| Pre-Session (optional) | Initialize scope + personalization + baseline docs | Session profile, docs context, policy flags | Settings, RAG index, ACL |
| In-Session | Realtime support across audio + video timeline | Live transcript, recap windows, cited Q&A, tool proposals | ASR, WS gateway, realtime AV pipeline |
| Post-Session | Summarize and publish outputs by session type | Versioned summary, meeting minutes or study pack, related artifacts | Gemini 3 (long-context), retrieval + templates |

## Product Goals & Target Users
- Product-ready: MINUTE focuses on an end-to-end demo for meeting/study workflows with realtime recap, post-session outputs, and grounded Q&A.
- Differentiator: multimodal companion agent (hear + see + understand timeline), not only transcript-based assistance.
- Expandability: personalized prompt/model profile, BYO API key, and workflow integrations for tasks/export/share.
- Target users: enterprise teams, PM/BA/engineering roles, internal training, personal learning, and evidence-heavy scenarios.

## MINUTE AI Architecture
MINUTE AI architecture runs with a router + specialized pipelines instead of a single linear flow:
- Unified Task Router: receives `task_type` and dispatches to the relevant pipeline.
- Shared session memory: final transcript, recap windows, visual events, citations.
- Tiered LightRAG retrieval: prioritize in-scope session/internal evidence; escalate to web only when needed.
- Self-check + corrective loop: validate evidence coverage before final response.
- Tool-calling governance: risky actions require proposal/approval and are fully logged.

![AI Architecture SAAR](docs/architecture/assets/saar-architecture.png)


### Stage-aware Router Policy (recommended)
| Stage | SLA | Model Profile | Tools | Notes |
| --- | --- | --- | --- | --- |
| Pre-Session (optional) | Near-realtime/BATCH | Fast + grounded | `rag_search`, `ingest_docs`, `session_setup` | Standardize scope + ACL before session |
| In-Session | Realtime | Fast streaming + multimodal | `realtime_recap`, `qna`, `tool_call_proposal` | 2-minute recap ticks, low-latency priority |
| Post-Session | Batch | Strong long-context | `summary_generate`, `generate_minutes`, `export` | Versioning + review/approve before sharing |

## System Architecture (5 Layers)
- Client Layer: web app (landing/session hub/in-session/post-session/Q&A sidebar).
- Communication Layer: WebSocket for audio/realtime events; REST for management, retrieval, summaries.
- Backend Core & Data: FastAPI services, realtime session store, minutes/summary services, Postgres/pgvector.
- AI/ML Layer: Gemini 3 text + multimodal reasoning, streaming ASR, LightRAG retrieval, LangGraph/LangChain orchestration.
- Cloud/Deployment/Security Layer: Dockerized services, object storage, audit logs, retention policy.

![System Architecture Layers](docs/architecture/assets/system-architecture-4-layers.png)

## AI Components (MINUTE Platform)
- Gemini 3 API: recap generation, grounded Q&A, summary/minutes synthesis.
- Realtime ASR service (SmartVoice/whisper.cpp): partial/final transcript over time.
- Visual understanding pipeline: frame sampling + slide-change detection + visual event extraction.
- LightRAG service: Tier 0/1 retrieval and escalation controller for Tier 2/3.
- Tool orchestration: proposal/approval/execution for web search, action writes, export/share.

## Architecture Diagrams

### System Architecture
![System Architecture](docs/architecture/assets/architecture.png)


### Cloud, Deployment & Security Layer
![Deployment Architecture](docs/architecture/assets/deployment.png)


## Key Capabilities
- Realtime WS flow: `POST /api/v1/sessions` -> `WS /api/v1/ws/audio` -> `WS /api/v1/ws/frontend`.
- Unified realtime AV flow: `WS /api/v1/ws/realtime-av/{id}` for `audio_chunk`, `video_frame_meta`, `user_query`, `approve_tool_call`.
- 2-minute recap windows: merge transcript + visual events into timeline context.
- In-session Q&A with tiered LightRAG, citations, and `no-source-no-answer` for critical claims.
- Post-session outputs: summary versioning, meeting minutes (action/decision/risk), and study outputs.
- Human-in-the-loop tool-calling with audit-ready logs by `session_id`/`meeting_id`.

## Tech Stack
- Client: Vite + React + TypeScript (web app).
- Backend: FastAPI, Uvicorn, SQLAlchemy, Pydantic, WebSocket.
- AI: Gemini API, LangChain + LangGraph, prompt pipelines for recap/Q&A/summary.
- Retrieval: Postgres + pgvector, hybrid retrieval + metadata filters.
- Realtime: ASR microservice (`services/asr`) + realtime AV window builder.
- Infra: Docker Compose (backend + postgres + asr), seeded SQL initialization.

## Repository Structure
```text
google_gemini_hackathon/
+-- backend/
|   +-- app/
|   |   +-- api/v1/
|   |   |   +-- endpoints/            # REST APIs: meetings, minutes, knowledge, realtime-av...
|   |   |   \-- websocket/            # WS: audio ingest, frontend stream, realtime-av
|   |   +-- core/                     # settings, security, logging
|   |   +-- llm/                      # prompts, chains, graphs, tools
|   |   +-- services/                 # business logic + realtime pipelines
|   |   +-- vectorstore/              # pgvector + LightRAG retrieval
|   |   +-- models/                   # SQLAlchemy models
|   |   +-- schemas/                  # Pydantic schemas
|   |   \-- workers/                  # background tasks
|   +-- alembic/
|   +-- tests/
|   +-- requirements.txt
|   \-- Dockerfile
+-- frontend/
|   +-- src/renderer/
|   |   +-- app/                      # routes + layout
|   |   +-- features/                 # meetings, knowledge, settings, tasks...
|   |   +-- components/               # shared UI
|   |   +-- lib/                      # API clients + utils
|   |   \-- store/                    # state
|   +-- public/
|   +-- package.json
|   \-- vite.config.ts
+-- services/
|   \-- asr/                          # whisper.cpp ASR microservice
+-- infra/
|   +-- docker-compose.yml            # postgres + backend + asr
|   +-- env/                          # local env mount
|   \-- postgres/init/                # init SQL + seed
+-- docs/
|   +-- architecture/
|   +-- implementation/
|   +-- reference/Gemini hackathon/
|   \-- archive/
+-- scripts/
|   +-- dev_start.sh
|   +-- migrate.sh
|   +-- run_tests.sh
|   \-- seed_data.py
+-- local_worker/
+-- requirements.txt
\-- README.md
```

## Quickstart (1 command)
### Docker (backend + DB + ASR, recommended)
Prerequisites: Docker 24+, Docker Compose, and available ports `8000` (API), `5433` (Postgres), `9000` (ASR).

```bash
cd infra
docker compose up -d --build
```
- API: `http://localhost:8000`
- DB: `localhost:5433` (user/pass/db: `minute`)
- ASR service: `http://localhost:9000`
- Init SQL: `infra/postgres/init/00_create_role.sql`, `01_init_extensions.sql`, `02_schema.sql`, `03_seed_mock.sql`

Quick checks:
```bash
curl http://localhost:8000/api/v1/health
# or open http://localhost:8000/docs
```
Logs:
```bash
docker compose logs -f backend
```
Stop/cleanup:
```bash
cd infra && docker compose down
```

### Frontend (Web app)
```powershell
cd frontend
npm install
npm run dev
```

## Development
### End-to-end (reviewer quick setup)
1) Create backend env at `infra/env/.env.local`:
```bash
cat > infra/env/.env.local <<'EOF'
ENV=development
DATABASE_URL=postgresql+psycopg2://minute:minute@postgres:5432/minute
GEMINI_API_KEY=
CORS_ORIGINS=*
ASR_URL=http://asr:9000
EOF
```
If running backend without Docker, change DB host to `localhost:5433`.

2) Start Postgres + Backend + ASR:
```bash
cd infra
docker compose up -d --build
```
PowerShell:
```powershell
cd infra
docker compose up -d --build
```

3) Run Web UI (dev):
```bash
cd frontend
npm ci
VITE_API_URL=http://localhost:8000 npm run dev
```
By default, frontend dev server runs at `http://localhost:5173`.

4) Near-production build (without installer):
```bash
cd frontend
VITE_API_URL=http://localhost:8000 npm run build
npm run preview -- --host
```

### Backend (local venv)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r .\requirements.txt
copy .\env.example.txt .\.env.local
rem If running without Docker, set DATABASE_URL to localhost:5433
uvicorn app.main:app --reload --port 8000
```

### Quick helper scripts (optional)
- `scripts/dev_start.sh`: boot infra + backend (macOS/Linux).
- `scripts/setup_local.sh`: full local setup (macOS/Linux).

### Seed data (optional)
```powershell
cd scripts
python seed_data.py
```

### Realtime dev/test
- WS ingest (no audio): `backend/tests/test_ingest_ws.py`
- Audio ingest: `backend/tests/test_audio_ingest_ws.py`, `backend/tests/test_audio_ws.py`
- WhisperX diarization demo: `backend/tests/selfhost_whisperx_diarize.py`

### Demo data & login
Current DB seed still includes a PMO/LPBank demo scenario. All seeded users can use password `demo123` (see `infra/postgres/init/05_add_auth.sql`).

## Configuration
Env is loaded from `backend/.env.local` or `infra/env/.env.local` (if present).

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- Core AI keys: `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`
- `GEMINI_MODEL`, `GEMINI_VISION_MODEL`
- `JINA_API_KEY`, `JINA_EMBED_MODEL`, `JINA_EMBED_DIMENSIONS`
- `SMARTVOICE_GRPC_ENDPOINT`, `SMARTVOICE_ACCESS_TOKEN`, `SMARTVOICE_TOKEN_ID`, `SMARTVOICE_TOKEN_KEY`
- `GOMEET_API_BASE_URL`, `GOMEET_PARTNER_TOKEN`
- `SUPABASE_S3_*` - object storage (optional)
- `SMTP_*`, `EMAIL_ENABLED` - email distribution (optional)
- `CORS_ORIGINS`, `SECRET_KEY`

Env template: `backend/env.example.txt`.

## API & Realtime
Core endpoints:
- `POST /api/v1/sessions` - create realtime session (returns WS URLs)
- `POST /api/v1/sessions/{id}/sources` - get `audio_ingest_token` for bridge
- `WS /api/v1/ws/audio/{id}?token=...` - raw audio ingress (PCM S16LE 16kHz)
- `WS /api/v1/ws/in-meeting/{id}` - dev/test transcript ingest
- `WS /api/v1/ws/frontend/{id}` - live transcript + realtime state for UI
- `WS /api/v1/ws/realtime-av/{id}` - unified realtime AV ingest + in-session Q&A events
- `GET /api/v1/realtime-av/sessions/{id}/snapshot` - realtime AV session state snapshot
- `PUT /api/v1/realtime-av/sessions/{id}/roi` - update ROI for slide-change detection
- `POST /api/v1/rag/query` / `POST /api/v1/knowledge/query` - grounded Q&A
- `POST /api/v1/transcripts/{meeting_id}/chunks` - transcript ingest
- `POST /api/v1/minutes/generate` - minutes generation

Realtime events (major):
- Client -> server: `audio_chunk`, `video_frame_meta`, `user_query`, `approve_tool_call`
- Server -> client: `transcript_event`, `visual_event`, `recap_window`, `tool_call_proposal`, `qna_answer`

Specs: `docs/implementation/api_contracts.md`, `docs/architecture/in_meeting_flow.md`, `docs/architecture/realtime_flow.md`, `docs/implementation/real_time_transcript.md`.

## Data Model
Core entities:
- `Meeting` - metadata, participants, schedule/session context.
- `TranscriptChunk` - time-coded transcript (partial/final pipeline persists final chunks).
- `VisualEvent` - slide/chart/code/whiteboard cues by `ts_ms`.
- `ContextWindow/RecapWindow` - merged transcript + visual context per time window.
- `ActionItem` / `Decision` / `Risk` - structured insights for minutes-grade outputs.
- `Citation` - evidence by doc/timecode/frame/source.

## RAG & Knowledge Hub
- Ingest: upload -> extract text -> chunk -> embed -> pgvector index.
- Retrieval:
  - Tier 0: session memory (recap/transcript/visual moments)
  - Tier 1: uploaded docs (hybrid keyword + vector + filters)
  - Tier 2: web search (optional, gated by user approval/policy)
  - Tier 3: deep research (best-effort with explicit limitations)
- Answering: grounded prompts + citations + `no-source-no-answer` for critical claims.
- Details: `docs/architecture/rag_architecture.md`, `docs/implementation/knowledge_vector_search.md`.

## Security & Compliance
- Demo scope: synthetic/scrubbed data preferred; sensitive real data upload is not recommended.
- Production direction: TLS/mTLS, secrets vaulting, RBAC/ABAC, ACL enforcement at retrieval layer.
- PII masking/redaction before calling external providers.
- Audit logs for query, retrieval, tool proposals/approvals, and state transitions.
- Retention/distribution controls for artifacts (transcript, minutes, exports).

## Observability & KPIs
- Latency: ASR lag, WS latency, recap lag by window, Q&A latency by tier.
- Quality: recap consistency vs transcript/visual events, precision/recall of action extraction.
- Usage: Ask-AI volume, tool-call approval rate, post-session review/approve completion.
- Cost: token usage by session, retrieval/search cache hit rate, model routing efficiency.

## Deployment
- Local dev: Docker Compose (`infra/docker-compose.yml`).
- MVP cloud: Vercel (frontend) + Render/FastAPI + Postgres/pgvector storage (see docs).
- Production orientation: private networking, secure storage, audit + retention enforcement.

### Single-VM production (recommended for self-hosting)
This repository now includes a production stack for one VM:
- App stack: `infra/docker-compose.prod.yml`
- Env template: `infra/env.prod.example` -> copy to `infra/.env.prod`
- HTTPS reverse proxy: `infra/caddy-compose.yml` + `infra/Caddyfile.example`

Characteristics:
- Postgres is internal only (no published host port).
- Backend runs without source mount and without `--reload`.
- ASR is internal (`expose 9000`) and consumed by backend over compose network.
- Caddy reverse proxy reaches backend via Docker network (`minute_backend:8000`).
- Backend host port is still bound to `127.0.0.1:8000` for local health checks.

Quick run:
```bash
cd infra
cp env.prod.example .env.prod
# edit .env.prod with real values
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Important:
- Use `docker compose` (Compose plugin v2), not legacy `docker-compose` v1.
- `docker-compose==1.29.x` can fail on newer Docker Engine with `KeyError: 'ContainerConfig'`.
- If you ever hit that error, remove old containers and recreate with v2:
```bash
cd infra
docker compose -f docker-compose.prod.yml --env-file .env.prod down --remove-orphans || true
docker rm -f minute_backend minute_db minute_asr 2>/dev/null || true
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build --force-recreate
```

Full guide:
- `docs/DEPLOY_VM_COMPOSE.md`

### End-to-end packaging & run guide
Quick reviewer setup to run the full product (Postgres + FastAPI + Frontend):
1) Clone the repo and enter the project folder:
   `git clone <repo-url>` -> `cd google_gemini_hackathon`
2) Minimum requirements: Docker 24+, Node 18+ + npm 9+, Python 3.11+ (if running backend directly).
3) Create `infra/env/.env.local` (sample in Development section).
4) Start services: `cd infra && docker compose up -d --build`.
5) Health check API: `curl http://localhost:8000/api/v1/health`.
6) Run UI: `cd frontend && VITE_API_URL=http://localhost:8000 npm run dev` (PowerShell: set `$env:VITE_API_URL` first).
7) Stop/cleanup: `cd infra && docker compose down` (add `-v` to reset seed data).

## Test Automation Guide
**Criteria**: automated script, stable runs, executed 3 consecutive times. Repo includes `scripts/run_tests.sh` for backend test suites (unit + integration) in 3 loops.

### Scope
- Backend unit tests: `backend/tests/unit`
- Backend integration tests (FastAPI TestClient, no external DB required): `backend/tests/integration`
- Manual audio/WS tests excluded: `backend/tests/test_audio_ws.py`, `backend/tests/test_audio_ingest_ws.py`, `backend/tests/test_ingest_ws.py`

### Environment requirements
- Python 3.11+
- `pip install -r requirements.txt`
- Postgres/Supabase not required for current smoke suite

### How to run
From repo root:
```bash
bash scripts/run_tests.sh
```
The script:
- Sets `PYTHONPATH` so backend imports resolve.
- Runs `pytest -q backend/tests/unit backend/tests/integration` 3 consecutive rounds.
- Stops immediately on first failure.

### Stability notes
- Single run: `PYTHONPATH=backend pytest -q backend/tests/unit backend/tests/integration`
- If adding tests that require network or real DB, update script or mark skip to preserve smoke stability.

## Roadmap
- G0: realtime transcript + recap windows + post-session summary/minutes.
- G1: multimodal timeline (audio + visual events) + grounded in-session Q&A.
- G2: tool-calling governance (proposal/approval/execution), export/share workflows.
- G3: personalization, multi-provider routing, analytics by team/session type.

## Docs
- Product blueprint: `docs/reference/Gemini hackathon/Gemini Hackathon 3 _ Minute's Techinical Blueprint.md`
- Idea proposal: `docs/reference/Gemini hackathon/Gemini Hackathon 3 _ Minute's Idea Proposal.md`
- Realtime flow: `docs/architecture/realtime_flow.md`, `docs/architecture/in_meeting_flow.md`, `docs/implementation/real_time_transcript.md`
- Realtime AV implementation: `docs/implementation/REALTIME_AV_MINUTE_PIPELINE.md`
- API contracts: `docs/implementation/api_contracts.md`
- Transcript ingest: `docs/implementation/transcript_ingest_api.md`
- RAG architecture: `docs/architecture/rag_architecture.md`, `docs/implementation/knowledge_vector_search.md`
- Aiven schema update runbook: `docs/implementation/SCHEMA_UPDATE_AIVEN_RUNBOOK.md`
- Deployment guide: `docs/DEPLOYMENT.md`, `docs/implementation/DEPLOYMENT.md`
- Architecture deep dive: `docs/architecture/`
- Security/test/UX plans: `docs/archive/Techni_docs_2/`

## Development Team
**SAVINAI** - Saigon Vietnam AI
- **Dang Nhu Phuoc (Leader)**: Software Engineer, AI Engineer, Backend Engineer. FastAPI backend architecture, realtime WS pipeline (audio/video context), LangGraph routing, minutes/recap pipeline, and dev infra.
- **Thai Hoai An**: Data Engineer, Software Engineer, AI Engineer. Data model + schema, pgvector/embeddings, document ingest, seed/demo data, and retrieval optimization.
- **Truong Minh Dat**: BA, GTM Analyst. Meeting/study use-case standardization, product KPIs, and go-to-market/documentation direction.
- **Hoang Minh Quan**: End-user Analyst, Product Deployment, BA. UX research, test/validation, deployment planning, and rollout/training support.

## Mentor Acknowledgements
Sincere thanks to the mentors who supported the team during the hackathon, guiding technology direction, solution architecture, and deployment feasibility:
- **Ho Minh Nghia (@nghiahm1989)**: PhD in Computer Science (FSO Academy - Russian Federation), cryptography specialist and AI/GenAI automation expert; former Deputy Head of Software Development at the Government Cipher Committee, digital transformation consultant for TPBank; currently AI domain expert at LPBank.
- **Nguyen Phan Khoa Duc (@dukeng96)**: Director of AI technology, product, and solution development at VNPT AI; studied at the University of Sydney (USYD) and worked in Australia.
- **Lam Vu Duong**: VNPT Director, supported program alignment and overall direction.
- **Thanh Dat**: VNPT GoMeet Software Engineer, supported meeting-platform and integration engineering.

## Contributing
Internal hackathon repository. Open an issue or PR; keep API contracts and docs updated.
