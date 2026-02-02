# RAG Design (stub)

- Ingestion: SmartReader/OCR ? chunk 400-800 tokens with overlap; metadata includes department, project, access scope.
- Storage: pgvector client + BM25 hybrid search placeholder; permission filter hook per user/meeting.
- Query: `rag_chain` wrapper to ground responses with citations; `no-source, no-answer` rule enforced in prompts.
- Freshness: hooks for recency boosting and meeting-specific context windows.