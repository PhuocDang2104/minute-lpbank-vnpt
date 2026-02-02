-- Add description and objective columns to project table
-- Run this migration if upgrading from older schema

-- Add description column if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='project' AND column_name='description'
    ) THEN
        ALTER TABLE project ADD COLUMN description TEXT;
        COMMENT ON COLUMN project.description IS 'Project description - scope, milestones, stakeholders';
    END IF;
END $$;

-- Add objective column if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='project' AND column_name='objective'
    ) THEN
        ALTER TABLE project ADD COLUMN objective TEXT;
        COMMENT ON COLUMN project.objective IS 'Project objectives and goals';
    END IF;
END $$;

-- Update existing projects with sample data (optional)
-- UPDATE project SET objective = 'Sample objective' WHERE objective IS NULL;

