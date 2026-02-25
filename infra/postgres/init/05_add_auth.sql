-- ============================================
-- AUTHENTICATION SCHEMA UPDATE
-- Add password_hash column for user authentication
-- ============================================

-- Add password_hash column to user_account if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_account' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE user_account ADD COLUMN password_hash TEXT;
    END IF;
END $$;

-- Add index on email for faster login lookups
CREATE INDEX IF NOT EXISTS idx_user_email_lower ON user_account(LOWER(email));

-- Add password_changed_at for tracking
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_account' AND column_name = 'password_changed_at'
    ) THEN
        ALTER TABLE user_account ADD COLUMN password_changed_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add is_active for account status
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_account' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE user_account ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- ============================================
-- UPDATE EXISTING DEMO USERS WITH DEFAULT PASSWORD
-- Password: "demo123" (hashed)
-- ============================================

-- bcrypt hash for "demo123"
-- generated from passlib bcrypt: $2b$12$BEuFmL3K9sfqUwl7CkwW7.mThK88O/dX1tK3qQB/cqTJgSBQ2L9Ai
-- In production, users should reset their passwords
UPDATE user_account 
SET password_hash = '$2b$12$BEuFmL3K9sfqUwl7CkwW7.mThK88O/dX1tK3qQB/cqTJgSBQ2L9Ai'
WHERE password_hash IS NULL;

-- ============================================
-- SESSION / REFRESH TOKEN TABLE (Optional)
-- For enhanced security with token revocation
-- ============================================

CREATE TABLE IF NOT EXISTS user_session (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_account(id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL,
    device_info TEXT,
    ip_address TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_session_user ON user_session(user_id);
CREATE INDEX IF NOT EXISTS idx_session_token ON user_session(refresh_token_hash);
CREATE INDEX IF NOT EXISTS idx_session_expires ON user_session(expires_at);

-- ============================================
-- PASSWORD RESET TOKEN TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS password_reset_token (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_account(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reset_token ON password_reset_token(token_hash);
CREATE INDEX IF NOT EXISTS idx_reset_user ON password_reset_token(user_id);

COMMENT ON TABLE user_session IS 'Stores refresh tokens for session management';
COMMENT ON TABLE password_reset_token IS 'Stores password reset tokens';
COMMENT ON COLUMN user_account.password_hash IS 'bcrypt hashed password';
COMMENT ON COLUMN user_account.is_active IS 'Account active status for soft disable';
