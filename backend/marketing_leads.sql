-- Create the marketing_leads table
CREATE TABLE IF NOT EXISTS marketing_leads (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_marketing_leads_id ON marketing_leads (id);
CREATE INDEX IF NOT EXISTS ix_marketing_leads_email ON marketing_leads (email);
