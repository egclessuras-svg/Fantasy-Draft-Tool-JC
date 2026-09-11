-- Complete PickProphet Database Setup
-- Run this in your new Supabase SQL Editor

-- Create users table for our custom authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create user_custom_projections table
CREATE TABLE IF NOT EXISTS user_custom_projections (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    player_name VARCHAR(255) NOT NULL,
    position VARCHAR(10) NOT NULL,
    custom_stats JSONB NOT NULL,
    ppr_projection NUMERIC DEFAULT 0,
    half_ppr_projection NUMERIC DEFAULT 0,
    non_ppr_projection NUMERIC DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, player_name)
);

-- Create user_draft_sessions table
CREATE TABLE IF NOT EXISTS user_draft_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(255),
    league_settings JSONB,
    draft_order JSONB,
    drafted_players JSONB,
    current_pick INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create user_rosters table
CREATE TABLE IF NOT EXISTS user_rosters (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    draft_session_id INTEGER,
    team_name VARCHAR(255),
    players JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create completed_drafts table
CREATE TABLE IF NOT EXISTS completed_drafts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE,
    draft_name VARCHAR(255),
    league_settings JSONB,
    draft_order JSONB,
    drafted_players JSONB,
    user_roster JSONB,
    final_roster_value NUMERIC DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert the default user (egclessuras@gmail.com)
INSERT INTO users (id, email, password_hash) VALUES (
    'e7bfc87a-1b1d-5930-a014-9015e7556f80',
    'egclessuras@gmail.com',
    'JohnWall2'
) ON CONFLICT (email) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_custom_projections_user_id ON user_custom_projections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_custom_projections_player_name ON user_custom_projections(player_name);
CREATE INDEX IF NOT EXISTS idx_user_draft_sessions_user_id ON user_draft_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_rosters_user_id ON user_rosters(user_id);
CREATE INDEX IF NOT EXISTS idx_completed_drafts_user_id ON completed_drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_custom_projections ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_draft_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_rosters ENABLE ROW LEVEL SECURITY;
ALTER TABLE completed_drafts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for users (allow all operations for now)
DROP POLICY IF EXISTS "Allow all operations on users" ON users;
CREATE POLICY "Allow all operations on users" ON users FOR ALL USING (true);

-- Create RLS policies for user_custom_projections
DROP POLICY IF EXISTS "Users can view own custom projections" ON user_custom_projections;
CREATE POLICY "Users can view own custom projections" ON user_custom_projections
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own custom projections" ON user_custom_projections;
CREATE POLICY "Users can insert own custom projections" ON user_custom_projections
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own custom projections" ON user_custom_projections;
CREATE POLICY "Users can update own custom projections" ON user_custom_projections
    FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own custom projections" ON user_custom_projections;
CREATE POLICY "Users can delete own custom projections" ON user_custom_projections
    FOR DELETE USING (true);

-- Create RLS policies for user_draft_sessions
DROP POLICY IF EXISTS "Users can view own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can view own draft sessions" ON user_draft_sessions
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can insert own draft sessions" ON user_draft_sessions
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can update own draft sessions" ON user_draft_sessions
    FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can delete own draft sessions" ON user_draft_sessions
    FOR DELETE USING (true);

-- Create RLS policies for user_rosters
DROP POLICY IF EXISTS "Users can view own rosters" ON user_rosters;
CREATE POLICY "Users can view own rosters" ON user_rosters
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own rosters" ON user_rosters;
CREATE POLICY "Users can insert own rosters" ON user_rosters
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own rosters" ON user_rosters;
CREATE POLICY "Users can update own rosters" ON user_rosters
    FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own rosters" ON user_rosters;
CREATE POLICY "Users can delete own rosters" ON user_rosters
    FOR DELETE USING (true);

-- Create RLS policies for completed_drafts
DROP POLICY IF EXISTS "Users can view own completed drafts" ON completed_drafts;
CREATE POLICY "Users can view own completed drafts" ON completed_drafts
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own completed drafts" ON completed_drafts;
CREATE POLICY "Users can insert own completed drafts" ON completed_drafts
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own completed drafts" ON completed_drafts;
CREATE POLICY "Users can update own completed drafts" ON completed_drafts
    FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own completed drafts" ON completed_drafts;
CREATE POLICY "Users can delete own completed drafts" ON completed_drafts
    FOR DELETE USING (true); 