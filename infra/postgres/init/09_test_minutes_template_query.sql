-- ============================================
-- TEST QUERIES FOR MINUTES TEMPLATE
-- ============================================

-- 1. Check if table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'minutes_template'
) AS table_exists;

-- 2. Check table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'minutes_template'
ORDER BY ordinal_position;

-- 3. Count templates
SELECT COUNT(*) as total_templates FROM minutes_template;

-- 4. List all templates (simple)
SELECT 
    id::text,
    name,
    code,
    is_default,
    is_active,
    created_at
FROM minutes_template
ORDER BY is_default DESC, name ASC
LIMIT 10;

-- 5. Check if there are any templates
SELECT 
    id::text,
    name,
    code,
    description,
    is_default,
    is_active,
    meeting_types,
    created_at
FROM minutes_template
WHERE is_active = TRUE
ORDER BY is_default DESC, name ASC;

-- 6. Check default template
SELECT 
    id::text,
    name,
    code,
    is_default
FROM minutes_template
WHERE is_default = TRUE
LIMIT 1;

