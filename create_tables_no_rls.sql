-- PickProphet Database Setup (No RLS)
-- Run this in your Supabase SQL Editor
-- This version doesn't use Row Level Security for testing

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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_custom_projections_user_id ON user_custom_projections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_custom_projections_player_name ON user_custom_projections(player_name);
CREATE INDEX IF NOT EXISTS idx_user_draft_sessions_user_id ON user_draft_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_rosters_user_id ON user_rosters(user_id);
CREATE INDEX IF NOT EXISTS idx_completed_drafts_user_id ON completed_drafts(user_id);

-- Note: RLS is disabled for testing purposes
-- In production, you would enable RLS and create appropriate policies 