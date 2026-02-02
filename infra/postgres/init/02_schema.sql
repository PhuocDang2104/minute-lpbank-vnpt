-- ============================================
-- MEETMATE FULL DATABASE SCHEMA
-- PostgreSQL + pgvector
-- ============================================

-- ============================================
-- 1. USER & ORGANIZATION
-- ============================================

-- Organization table
CREATE TABLE IF NOT EXISTS organization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Project table
CREATE TABLE IF NOT EXISTS project (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organization(id),
    name TEXT NOT NULL,
    code TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Department table
CREATE TABLE IF NOT EXISTS department (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organization(id),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User account (extended)
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE user_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    password_hash TEXT,
    role TEXT DEFAULT 'user', -- user / chair / PMO / admin
    organization_id UUID REFERENCES organization(id),
    department_id UUID REFERENCES department(id),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_email ON user_account(email);
CREATE INDEX idx_user_org ON user_account(organization_id);

-- ============================================
-- 2. MEETING CORE
-- ============================================

DROP TABLE IF EXISTS meetings CASCADE;
CREATE TABLE meeting (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_event_id TEXT, -- sync từ Outlook/Teams
    title TEXT NOT NULL,
    description TEXT,
    organizer_id UUID REFERENCES user_account(id),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    meeting_type TEXT, -- status, steering, risk, sprint, daily...
    phase TEXT DEFAULT 'pre', -- pre / in / post
    project_id UUID REFERENCES project(id),
    department_id UUID REFERENCES department(id),
    location TEXT,
    teams_link TEXT,
    recording_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_meeting_organizer ON meeting(organizer_id);
CREATE INDEX idx_meeting_start ON meeting(start_time);
CREATE INDEX idx_meeting_project ON meeting(project_id);
CREATE INDEX idx_meeting_type ON meeting(meeting_type);

-- Meeting participants
CREATE TABLE meeting_participant (
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'attendee', -- organizer / required / optional / attendee
    response_status TEXT DEFAULT 'pending', -- accepted / declined / tentative / pending
    attended BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMPTZ,
    left_at TIMESTAMPTZ,
    PRIMARY KEY (meeting_id, user_id)
);

CREATE INDEX idx_participant_user ON meeting_participant(user_id);

-- ============================================
-- 3. PRE-MEETING MODULE
-- ============================================

-- A1. Agenda proposed by AI
CREATE TABLE agenda_proposed (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    generated_agenda JSONB, -- [{item: "...", duration_min: 10, presenter: "..."}, ...]
    status TEXT DEFAULT 'draft', -- draft / approved / rejected
    approved_by UUID REFERENCES user_account(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pre-read documents suggested by RAG
CREATE TABLE preread_document (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    source TEXT, -- SharePoint / LOffice / wiki / local
    url TEXT,
    snippet TEXT, -- preview text
    relevance_score FLOAT DEFAULT 0.0,
    status TEXT DEFAULT 'suggested', -- suggested / accepted / ignored
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_preread_meeting ON preread_document(meeting_id);

-- A2. Pre-meeting questions/risks from participants
CREATE TABLE pre_meeting_question (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id),
    question TEXT NOT NULL,
    type TEXT DEFAULT 'question', -- question / risk / demo_request / concern
    status TEXT DEFAULT 'open', -- open / addressed / deferred
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prequestion_meeting ON pre_meeting_question(meeting_id);

-- A3. AI Suggestions (documents / people)
CREATE TABLE meeting_suggestion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    suggestion_type TEXT NOT NULL, -- document / person / policy / action
    content TEXT NOT NULL,
    reference_url TEXT,
    reason TEXT, -- why AI suggested this
    confidence_score FLOAT DEFAULT 0.0,
    status TEXT DEFAULT 'pending', -- pending / accepted / ignored
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_suggestion_meeting ON meeting_suggestion(meeting_id);

-- ============================================
-- 4. IN-MEETING MODULE
-- ============================================

-- B1. Transcript chunks (ASR + diarization)
CREATE TABLE transcript_chunk (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL, -- thứ tự chunk
    start_time FLOAT NOT NULL, -- giây từ đầu cuộc họp
    end_time FLOAT NOT NULL,
    speaker TEXT, -- speaker label from diarization
    speaker_user_id UUID REFERENCES user_account(id), -- mapped user if identified
    text TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    language TEXT DEFAULT 'vi',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transcript_meeting ON transcript_chunk(meeting_id);
CREATE INDEX idx_transcript_time ON transcript_chunk(meeting_id, start_time);
CREATE INDEX idx_transcript_speaker ON transcript_chunk(speaker_user_id);

-- Live recap snapshots
CREATE TABLE live_recap_snapshot (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    snapshot_time TIMESTAMPTZ NOT NULL,
    from_chunk_id UUID REFERENCES transcript_chunk(id),
    to_chunk_id UUID REFERENCES transcript_chunk(id),
    summary TEXT NOT NULL,
    key_points JSONB, -- ["point1", "point2", ...]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recap_meeting ON live_recap_snapshot(meeting_id);

-- B2. Action Items (truy vết từ transcript)
CREATE TABLE action_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    owner_user_id UUID REFERENCES user_account(id),
    description TEXT NOT NULL,
    deadline DATE,
    priority TEXT DEFAULT 'medium', -- low / medium / high / critical
    source_chunk_id UUID REFERENCES transcript_chunk(id), -- truy vết
    source_text TEXT, -- đoạn transcript gốc
    status TEXT DEFAULT 'proposed', -- proposed / confirmed / in_progress / completed / cancelled
    external_task_link TEXT, -- link Jira/Planner
    external_task_id TEXT,
    confirmed_by UUID REFERENCES user_account(id),
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_action_meeting ON action_item(meeting_id);
CREATE INDEX idx_action_owner ON action_item(owner_user_id);
CREATE INDEX idx_action_status ON action_item(status);
CREATE INDEX idx_action_deadline ON action_item(deadline);

-- Decision Items
CREATE TABLE decision_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    rationale TEXT, -- lý do quyết định
    source_chunk_id UUID REFERENCES transcript_chunk(id),
    source_text TEXT,
    status TEXT DEFAULT 'proposed', -- proposed / confirmed / revised
    confirmed_by UUID REFERENCES user_account(id),
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_decision_meeting ON decision_item(meeting_id);

-- Risk Items
CREATE TABLE risk_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    severity TEXT DEFAULT 'medium', -- low / medium / high / critical
    mitigation TEXT, -- proposed mitigation
    source_chunk_id UUID REFERENCES transcript_chunk(id),
    source_text TEXT,
    status TEXT DEFAULT 'proposed', -- proposed / confirmed / mitigated / closed
    owner_user_id UUID REFERENCES user_account(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_risk_meeting ON risk_item(meeting_id);
CREATE INDEX idx_risk_severity ON risk_item(severity);

-- B3. Ask-AI queries (RAG trong meeting)
CREATE TABLE ask_ai_query (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id),
    query_text TEXT NOT NULL,
    answer_text TEXT,
    citations JSONB, -- [{doc_id, title, snippet, page}, ...]
    context_chunk_ids UUID[], -- transcript chunks used as context
    model_used TEXT,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_askai_meeting ON ask_ai_query(meeting_id);
CREATE INDEX idx_askai_user ON ask_ai_query(user_id);

-- B4. Tool-calling logs
CREATE TABLE tool_call_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id),
    tool_name TEXT NOT NULL, -- planner, jira, outlook, sharepoint, loffice
    action TEXT, -- create_task, get_calendar, open_document...
    request_payload JSONB,
    response_payload JSONB,
    status TEXT DEFAULT 'pending', -- pending / success / failed
    error_message TEXT,
    execution_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_toolcall_meeting ON tool_call_log(meeting_id);
CREATE INDEX idx_toolcall_tool ON tool_call_log(tool_name);

-- B5. Agenda progress tracking (timeboxing)
CREATE TABLE agenda_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    agenda_item TEXT NOT NULL,
    item_index INT,
    planned_start_time FLOAT, -- giây từ đầu meeting
    planned_end_time FLOAT,
    actual_start_time FLOAT,
    actual_end_time FLOAT,
    status TEXT DEFAULT 'pending', -- pending / in_progress / completed / skipped
    reminder_sent BOOLEAN DEFAULT FALSE,
    overtime_minutes INT DEFAULT 0
);

CREATE INDEX idx_agendaprog_meeting ON agenda_progress(meeting_id);

-- ============================================
-- 5. POST-MEETING MODULE
-- ============================================

-- C1. Meeting Minutes
CREATE TABLE meeting_minutes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    version INT DEFAULT 1,
    minutes_text TEXT, -- plain text
    minutes_html TEXT, -- formatted HTML
    minutes_markdown TEXT,
    minutes_doc_url TEXT, -- exported doc link
    executive_summary TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    edited_by UUID REFERENCES user_account(id),
    edited_at TIMESTAMPTZ,
    status TEXT DEFAULT 'draft', -- draft / reviewed / approved / distributed
    approved_by UUID REFERENCES user_account(id),
    approved_at TIMESTAMPTZ
);

CREATE INDEX idx_minutes_meeting ON meeting_minutes(meeting_id);

-- Minutes distribution log
CREATE TABLE minutes_distribution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    minutes_id UUID REFERENCES meeting_minutes(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id),
    channel TEXT NOT NULL, -- email / teams / sharepoint
    recipient_email TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'sent', -- sent / delivered / read / failed
    error_message TEXT
);

CREATE INDEX idx_distlog_meeting ON minutes_distribution_log(meeting_id);

-- C2. Task sync logs
CREATE TABLE task_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_item_id UUID REFERENCES action_item(id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- planner / jira / asana
    external_task_id TEXT,
    sync_type TEXT, -- create / update / delete
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'success', -- success / failed
    request_payload JSONB,
    response_payload JSONB,
    error_message TEXT
);

CREATE INDEX idx_tasksync_action ON task_sync_log(action_item_id);

-- Deadline reminder logs
CREATE TABLE deadline_reminder_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_item_id UUID REFERENCES action_item(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id),
    reminder_type TEXT, -- 1day / 3day / overdue
    channel TEXT, -- email / teams / push
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX idx_reminder_action ON deadline_reminder_log(action_item_id);

-- C3. Highlight clips
CREATE TABLE highlight_clip (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    reason TEXT, -- action-density / keyword / decision / risk
    title TEXT,
    description TEXT,
    video_url TEXT,
    thumbnail_url TEXT,
    transcript_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_highlight_meeting ON highlight_clip(meeting_id);

-- C4. Post-meeting Q&A
CREATE TABLE qa_post_meeting (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id),
    question_text TEXT NOT NULL,
    answer_text TEXT,
    citations JSONB,
    helpful_rating INT, -- 1-5
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_qapost_meeting ON qa_post_meeting(meeting_id);

-- ============================================
-- 6. VECTOR STORE (RAG)
-- ============================================

-- Document embeddings
DROP TABLE IF EXISTS documents CASCADE;
CREATE TABLE document (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    source TEXT, -- sharepoint / loffice / upload / wiki
    source_url TEXT,
    file_type TEXT, -- pdf / docx / pptx / xlsx
    file_size_bytes BIGINT,
    content_text TEXT, -- extracted text
    metadata JSONB, -- {department, project, tags, access_level}
    organization_id UUID REFERENCES organization(id),
    uploaded_by UUID REFERENCES user_account(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_doc_org ON document(organization_id);
CREATE INDEX idx_doc_source ON document(source);

-- Document chunk embeddings
CREATE TABLE document_embedding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES document(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 / text-embedding-3-small
    metadata JSONB, -- {page, section, heading}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_docemb_doc ON document_embedding(document_id);

-- Transcript embeddings (for meeting search)
CREATE TABLE transcript_embedding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID REFERENCES transcript_chunk(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transemb_meeting ON transcript_embedding(meeting_id);

-- ============================================
-- 7. CHAT / SESSION MANAGEMENT
-- ============================================

CREATE TABLE chat_session (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meeting(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id),
    session_type TEXT DEFAULT 'in_meeting', -- pre_meeting / in_meeting / post_meeting / knowledge
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    message_count INT DEFAULT 0
);

CREATE INDEX idx_chatsess_meeting ON chat_session(meeting_id);
CREATE INDEX idx_chatsess_user ON chat_session(user_id);

CREATE TABLE chat_message (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_session(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- user / assistant / system
    content TEXT NOT NULL,
    citations JSONB,
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chatmsg_session ON chat_message(session_id);

-- ============================================
-- 8. AUDIT & HISTORY
-- ============================================

-- Edit history for minutes
CREATE TABLE minutes_edit_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    minutes_id UUID REFERENCES meeting_minutes(id) ON DELETE CASCADE,
    edited_by UUID REFERENCES user_account(id),
    edited_at TIMESTAMPTZ DEFAULT NOW(),
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT
);

CREATE INDEX idx_minedit_minutes ON minutes_edit_history(minutes_id);

-- Item confirmation history
CREATE TABLE item_confirmation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_type TEXT NOT NULL, -- action / decision / risk
    item_id UUID NOT NULL,
    confirmed_by UUID REFERENCES user_account(id),
    action TEXT NOT NULL, -- confirm / reject / edit
    previous_status TEXT,
    new_status TEXT,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_itemconf_item ON item_confirmation_log(item_type, item_id);

-- ============================================
-- VECTOR SEARCH INDEXES (pgvector)
-- ============================================

-- IVFFlat index for document embeddings (faster approximate search)
CREATE INDEX IF NOT EXISTS idx_docemb_vector ON document_embedding 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- IVFFlat index for transcript embeddings
CREATE INDEX IF NOT EXISTS idx_transemb_vector ON transcript_embedding 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);