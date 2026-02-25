-- ============================================
-- ALIGN LEGACY CLOUD DB TO 02_schema.sql (NON-DESTRUCTIVE)
-- ============================================
-- Purpose:
-- - Keep existing data
-- - Add missing columns/indexes used by current backend/frontend
-- - Backfill from legacy columns where possible

-- ============================================
-- 1) meeting.session_date
-- ============================================
ALTER TABLE meeting
    ADD COLUMN IF NOT EXISTS session_date DATE;

UPDATE meeting
SET session_date = start_time::date
WHERE session_date IS NULL
  AND start_time IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_meeting_session_date ON meeting(session_date);

-- ============================================
-- 2) transcript_chunk modern columns
-- Legacy schema currently has:
-- - time_start / time_end / lang
-- ============================================
ALTER TABLE transcript_chunk
    ADD COLUMN IF NOT EXISTS start_time DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS end_time DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS speaker_user_id UUID,
    ADD COLUMN IF NOT EXISTS language TEXT;

UPDATE transcript_chunk
SET
    start_time = COALESCE(start_time, time_start),
    end_time = COALESCE(end_time, time_end),
    language = COALESCE(language, lang, 'vi')
WHERE
    start_time IS NULL
    OR end_time IS NULL
    OR language IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'transcript_chunk_speaker_user_id_fkey'
          AND conrelid = 'transcript_chunk'::regclass
    ) THEN
        ALTER TABLE transcript_chunk
            ADD CONSTRAINT transcript_chunk_speaker_user_id_fkey
            FOREIGN KEY (speaker_user_id) REFERENCES user_account(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_transcript_time ON transcript_chunk(meeting_id, start_time);
CREATE INDEX IF NOT EXISTS idx_transcript_speaker ON transcript_chunk(speaker_user_id);

-- ============================================
-- 3) ask_ai_query modern columns
-- ============================================
ALTER TABLE ask_ai_query
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS context_chunk_ids UUID[],
    ADD COLUMN IF NOT EXISTS model_used TEXT,
    ADD COLUMN IF NOT EXISTS latency_ms INT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ask_ai_query_user_id_fkey'
          AND conrelid = 'ask_ai_query'::regclass
    ) THEN
        ALTER TABLE ask_ai_query
            ADD CONSTRAINT ask_ai_query_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES user_account(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_askai_user ON ask_ai_query(user_id);

