-- PickProphet Database Setup
-- Run this in your Supabase SQL Editor

-- Enable Row Level Security on auth.users
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create user_custom_projections table
CREATE TABLE IF NOT EXISTS user_custom_projections (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    draft_session_id INTEGER REFERENCES user_draft_sessions(id) ON DELETE CASCADE,
    team_name VARCHAR(255),
    players JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create completed_drafts table
CREATE TABLE IF NOT EXISTS completed_drafts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own custom projections" ON user_custom_projections;
CREATE POLICY "Users can insert own custom projections" ON user_custom_projections
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own custom projections" ON user_custom_projections;
CREATE POLICY "Users can update own custom projections" ON user_custom_projections
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own custom projections" ON user_custom_projections;
CREATE POLICY "Users can delete own custom projections" ON user_custom_projections
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for user_draft_sessions
DROP POLICY IF EXISTS "Users can view own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can view own draft sessions" ON user_draft_sessions
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can insert own draft sessions" ON user_draft_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can update own draft sessions" ON user_draft_sessions
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can delete own draft sessions" ON user_draft_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for user_rosters
DROP POLICY IF EXISTS "Users can view own rosters" ON user_rosters;
CREATE POLICY "Users can view own rosters" ON user_rosters
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own rosters" ON user_rosters;
CREATE POLICY "Users can insert own rosters" ON user_rosters
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own rosters" ON user_rosters;
CREATE POLICY "Users can update own rosters" ON user_rosters
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own rosters" ON user_rosters;
CREATE POLICY "Users can delete own rosters" ON user_rosters
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for completed_drafts
DROP POLICY IF EXISTS "Users can view own completed drafts" ON completed_drafts;
CREATE POLICY "Users can view own completed drafts" ON completed_drafts
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own completed drafts" ON completed_drafts;
CREATE POLICY "Users can insert own completed drafts" ON completed_drafts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own completed drafts" ON completed_drafts;
CREATE POLICY "Users can update own completed drafts" ON completed_drafts
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own completed drafts" ON completed_drafts;
CREATE POLICY "Users can delete own completed drafts" ON completed_drafts
    FOR DELETE USING (auth.uid() = user_id); 
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create user_rosters table
CREATE TABLE IF NOT EXISTS user_rosters (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    draft_session_id INTEGER REFERENCES user_draft_sessions(id) ON DELETE CASCADE,
    team_name VARCHAR(255),
    players JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create completed_drafts table
CREATE TABLE IF NOT EXISTS completed_drafts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own custom projections" ON user_custom_projections;
CREATE POLICY "Users can insert own custom projections" ON user_custom_projections
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own custom projections" ON user_custom_projections;
CREATE POLICY "Users can update own custom projections" ON user_custom_projections
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own custom projections" ON user_custom_projections;
CREATE POLICY "Users can delete own custom projections" ON user_custom_projections
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for user_draft_sessions
DROP POLICY IF EXISTS "Users can view own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can view own draft sessions" ON user_draft_sessions
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can insert own draft sessions" ON user_draft_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can update own draft sessions" ON user_draft_sessions
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own draft sessions" ON user_draft_sessions;
CREATE POLICY "Users can delete own draft sessions" ON user_draft_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for user_rosters
DROP POLICY IF EXISTS "Users can view own rosters" ON user_rosters;
CREATE POLICY "Users can view own rosters" ON user_rosters
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own rosters" ON user_rosters;
CREATE POLICY "Users can insert own rosters" ON user_rosters
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own rosters" ON user_rosters;
CREATE POLICY "Users can update own rosters" ON user_rosters
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own rosters" ON user_rosters;
CREATE POLICY "Users can delete own rosters" ON user_rosters
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for completed_drafts
DROP POLICY IF EXISTS "Users can view own completed drafts" ON completed_drafts;
CREATE POLICY "Users can view own completed drafts" ON completed_drafts
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own completed drafts" ON completed_drafts;
CREATE POLICY "Users can insert own completed drafts" ON completed_drafts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own completed drafts" ON completed_drafts;
CREATE POLICY "Users can update own completed drafts" ON completed_drafts
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own completed drafts" ON completed_drafts;
CREATE POLICY "Users can delete own completed drafts" ON completed_drafts
    FOR DELETE USING (auth.uid() = user_id); 
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    draft_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, session_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_custom_projections_user_id ON custom_projections(user_id);
CREATE INDEX IF NOT EXISTS idx_custom_projections_player_name ON custom_projections(player_name);
CREATE INDEX IF NOT EXISTS idx_completed_drafts_user_id ON completed_drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_completed_drafts_session_id ON completed_drafts(session_id); 