-- Ensure meeting_recording table exists for video upload metadata.
-- This is additive and safe on existing DBs.

CREATE TABLE IF NOT EXISTS meeting_recording (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meeting(id) ON DELETE CASCADE,
    file_url TEXT,
    storage_key TEXT,
    provider TEXT,
    original_filename TEXT,
    content_type TEXT,
    size_bytes INTEGER,
    duration_sec DOUBLE PRECISION,
    uploaded_by UUID REFERENCES user_account(id),
    status TEXT DEFAULT 'uploaded',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meeting_recording_meeting_id
    ON meeting_recording(meeting_id);
