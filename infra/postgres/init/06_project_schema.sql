-- Project core schema
CREATE TABLE IF NOT EXISTS project (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    description TEXT,
    organization_id UUID REFERENCES organization(id),
    department_id UUID REFERENCES department(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_member (
    project_id UUID REFERENCES project(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_account(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member', -- owner / member / guest
    joined_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (project_id, user_id)
);

-- Extend meeting with project linkage
ALTER TABLE meeting
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES project(id);

-- Extend action_item with project linkage
ALTER TABLE action_item
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES project(id);

-- Extend document with project metadata and visibility
ALTER TABLE document
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES project(id),
    ADD COLUMN IF NOT EXISTS visibility TEXT DEFAULT 'project', -- project / meeting / private / share
    ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES user_account(id),
    ADD COLUMN IF NOT EXISTS tags TEXT[];

-- Index suggestions
CREATE INDEX IF NOT EXISTS idx_project_org ON project(organization_id);
CREATE INDEX IF NOT EXISTS idx_project_dept ON project(department_id);
CREATE INDEX IF NOT EXISTS idx_meeting_project ON meeting(project_id);
CREATE INDEX IF NOT EXISTS idx_action_item_project ON action_item(project_id);
CREATE INDEX IF NOT EXISTS idx_document_project ON document(project_id);

