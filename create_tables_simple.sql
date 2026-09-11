-- PickProphet Database Setup (Simplified)
-- Run this in your Supabase SQL Editor
-- This version doesn't modify auth.users table

-- Create user_custom_projections table
CREATE TABLE IF NOT EXISTS user_custom_projections (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
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
    user_id UUID NOT NULL,
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
    user_id UUID NOT NULL,
    draft_session_id INTEGER,
    team_name VARCHAR(255),
    players JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create completed_drafts table
CREATE TABLE IF NOT EXISTS completed_drafts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    session_id VARCHAR(255) UNIQUE,
    draft_name VARCHAR(255),
    league_settings JSONB,
    draft_order JSONB,
    drafted_players JSONB,
    user_roster JSONB,
    final_roster_value NUMERIC DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE user_custom_projections ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_draft_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_rosters ENABLE ROW LEVEL SECURITY;
ALTER TABLE completed_drafts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for user_custom_projections
DROP POLICY IF EXISTS "Users can view own custom projections" ON user_custom_projections;
CREATE POLICY "Users can view own custom projections" ON user_custom_projections
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own custom projections" ON user_custom_projections;
CREATE POLICY "Users can insert own custom projections" ON user_custom_projections
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own custom projections" ON user_custom_projections;
CREATE POLICY "Users can update own custom projections" ON user_custom_projections
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own custom projections" ON user_custom_projections;
CREATE POLICY "Users can delete own custom projections" ON user_custom_projections
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Create RLS policies for user_draft_sessions
DROP POLICY IF EXISTS "Users can view own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can view own draft sessions" ON user_draft_sessions
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can insert own draft sessions" ON user_draft_sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can update own draft sessions" ON user_draft_sessions
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can delete own draft sessions" ON user_draft_sessions
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Create RLS policies for user_rosters
DROP POLICY IF EXISTS "Users can view own rosters" ON user_rosters;
CREATE POLICY "Users can view own rosters" ON user_rosters
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own rosters" ON user_rosters;
CREATE POLICY "Users can insert own rosters" ON user_rosters
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own rosters" ON user_rosters;
CREATE POLICY "Users can update own rosters" ON user_rosters
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own rosters" ON user_rosters;
CREATE POLICY "Users can delete own rosters" ON user_rosters
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Create RLS policies for completed_drafts
DROP POLICY IF EXISTS "Users can view own completed drafts" ON completed_drafts;
CREATE POLICY "Users can view own completed drafts" ON completed_drafts
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own completed drafts" ON completed_drafts;
CREATE POLICY "Users can insert own completed drafts" ON completed_drafts
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own completed drafts" ON completed_drafts;
CREATE POLICY "Users can update own completed drafts" ON completed_drafts
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own completed drafts" ON completed_drafts;
CREATE POLICY "Users can delete own completed drafts" ON completed_drafts
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_custom_projections_user_id ON user_custom_projections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_custom_projections_player_name ON user_custom_projections(player_name);
CREATE INDEX IF NOT EXISTS idx_user_draft_sessions_user_id ON user_draft_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_rosters_user_id ON user_rosters(user_id);
CREATE INDEX IF NOT EXISTS idx_completed_drafts_user_id ON completed_drafts(user_id); 