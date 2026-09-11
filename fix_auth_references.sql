-- Fix database schema to use Supabase's built-in auth.users table
-- Run this in your Supabase SQL Editor

-- Drop the custom users table since we're using Supabase's built-in auth.users
DROP TABLE IF EXISTS users CASCADE;

-- Update user_custom_projections table to reference auth.users instead
ALTER TABLE user_custom_projections 
DROP CONSTRAINT IF EXISTS user_custom_projections_user_id_fkey;

ALTER TABLE user_custom_projections 
ADD CONSTRAINT user_custom_projections_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update user_draft_sessions table to reference auth.users instead
ALTER TABLE user_draft_sessions 
DROP CONSTRAINT IF EXISTS user_draft_sessions_user_id_fkey;

ALTER TABLE user_draft_sessions 
ADD CONSTRAINT user_draft_sessions_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update user_rosters table to reference auth.users instead
ALTER TABLE user_rosters 
DROP CONSTRAINT IF EXISTS user_rosters_user_id_fkey;

ALTER TABLE user_rosters 
ADD CONSTRAINT user_rosters_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update completed_drafts table to reference auth.users instead
ALTER TABLE completed_drafts 
DROP CONSTRAINT IF EXISTS completed_drafts_user_id_fkey;

ALTER TABLE completed_drafts 
ADD CONSTRAINT completed_drafts_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update RLS policies to use auth.uid() instead of custom user_id
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

-- Update RLS policies for user_draft_sessions
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

-- Update RLS policies for user_rosters
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

-- Update RLS policies for completed_drafts
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

-- Verify the changes
SELECT 
    table_name,
    constraint_name,
    constraint_type
FROM information_schema.table_constraints 
WHERE table_name IN ('user_custom_projections', 'user_draft_sessions', 'user_rosters', 'completed_drafts')
AND constraint_type = 'FOREIGN KEY';

-- Database schema updated successfully to use Supabase auth.users table!
SELECT 'Database schema updated successfully to use Supabase auth.users table!' as status;
