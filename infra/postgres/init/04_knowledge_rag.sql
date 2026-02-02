-- Enable pgvector (idempotent)
CREATE EXTENSION IF NOT EXISTS "vector";

-- Knowledge document metadata
CREATE TABLE IF NOT EXISTS knowledge_document (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT,
    category TEXT,
    tags TEXT[],
    file_type TEXT,
    file_size BIGINT,
    storage_key TEXT,
    file_url TEXT,
    org_id UUID,
    project_id UUID,
    meeting_id UUID,
    visibility TEXT, -- public|org|project|meeting|private
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Chunks + embeddings
-- Using 1024 dims to match jina-embeddings-v3 (text-matching). Adjust if model changes.
CREATE TABLE IF NOT EXISTS knowledge_chunk (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES knowledge_document(id) ON DELETE CASCADE,
    chunk_index INT,
    content TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    lang TEXT,
    section TEXT,
    page INT,
    scope_org UUID,
    scope_project UUID,
    scope_meeting UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunk_doc ON knowledge_chunk(document_id);
CREATE INDEX IF NOT EXISTS idx_chunk_scope_org ON knowledge_chunk(scope_org);
CREATE INDEX IF NOT EXISTS idx_chunk_scope_project ON knowledge_chunk(scope_project);
CREATE INDEX IF NOT EXISTS idx_chunk_scope_meeting ON knowledge_chunk(scope_meeting);

-- Vector index (ivfflat); adjust lists as data grows
-- Note: table should be analyzed before creating ivfflat for best performance
CREATE INDEX IF NOT EXISTS idx_chunk_embedding
ON knowledge_chunk USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
