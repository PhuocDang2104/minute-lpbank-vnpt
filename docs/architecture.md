# Architecture Overview

- Client: Electron desktop (Vite + React) with sidebar/topbar shell; Teams add-in planned later.
- Backend: FastAPI, LangGraph orchestrator per stage (pre | in | post meeting), RAG over pgvector.
- Data: Postgres for OLTP, pgvector for embeddings, object storage placeholder.
- Realtime: WebSocket for in-meeting transcript/events streaming.
- Integrations: Microsoft Graph/LOffice adapters (placeholders) for tasks, calendar, docs.