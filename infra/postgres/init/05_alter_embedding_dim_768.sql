-- Adjust embedding column to 1024 dims for jina-embeddings-v3 (text-matching)
DO $$
BEGIN
    -- Drop vector index if exists
    IF EXISTS (
        SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'idx_chunk_embedding'
    ) THEN
        EXECUTE 'DROP INDEX IF EXISTS idx_chunk_embedding';
    END IF;

    -- Alter column type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'knowledge_chunk' AND column_name = 'embedding'
    ) THEN
        EXECUTE 'ALTER TABLE knowledge_chunk ALTER COLUMN embedding TYPE vector(1024)';
    END IF;

    -- Recreate ivfflat index
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_chunk_embedding ON knowledge_chunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)';
END$$;
