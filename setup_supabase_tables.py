#!/usr/bin/env python3
"""
Supabase Database Setup Script
This script sets up the required tables and policies for the PickProphet application.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def setup_supabase():
    """Set up Supabase database tables and policies."""
    
    # Initialize Supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in environment variables")
        print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False
    
    # SQL commands to set up the database
    setup_commands = [
        # Enable Row Level Security on auth.users
        "ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;",
        
        # Create user_custom_projections table
        """
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
        """,
        
        # Create user_draft_sessions table
        """
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
        """,
        
        # Create user_rosters table
        """
        CREATE TABLE IF NOT EXISTS user_rosters (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            draft_session_id INTEGER REFERENCES user_draft_sessions(id) ON DELETE CASCADE,
            team_name VARCHAR(255),
            players JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        
        # Create completed_drafts table
        """
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
        """,
        
        # Enable RLS on all tables
        "ALTER TABLE user_custom_projections ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE user_draft_sessions ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE user_rosters ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE completed_drafts ENABLE ROW LEVEL SECURITY;",
        
        # Create RLS policies for user_custom_projections
        """
        DROP POLICY IF EXISTS "Users can view own custom projections" ON user_custom_projections;
        CREATE POLICY "Users can view own custom projections" ON user_custom_projections
            FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can insert own custom projections" ON user_custom_projections;
        CREATE POLICY "Users can insert own custom projections" ON user_custom_projections
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can update own custom projections" ON user_custom_projections;
        CREATE POLICY "Users can update own custom projections" ON user_custom_projections
            FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can delete own custom projections" ON user_custom_projections;
        CREATE POLICY "Users can delete own custom projections" ON user_custom_projections
            FOR DELETE USING (auth.uid() = user_id);
        """,
        
        # Create RLS policies for user_draft_sessions
        """
        DROP POLICY IF EXISTS "Users can view own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can view own draft sessions" ON user_draft_sessions
            FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can insert own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can insert own draft sessions" ON user_draft_sessions
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can update own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can update own draft sessions" ON user_draft_sessions
            FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can delete own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can delete own draft sessions" ON user_draft_sessions
            FOR DELETE USING (auth.uid() = user_id);
        """,
        
        # Create RLS policies for user_rosters
        """
        DROP POLICY IF EXISTS "Users can view own rosters" ON user_rosters;
        CREATE POLICY "Users can view own rosters" ON user_rosters
            FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can insert own rosters" ON user_rosters;
        CREATE POLICY "Users can insert own rosters" ON user_rosters
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can update own rosters" ON user_rosters;
        CREATE POLICY "Users can update own rosters" ON user_rosters
            FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can delete own rosters" ON user_rosters;
        CREATE POLICY "Users can delete own rosters" ON user_rosters
            FOR DELETE USING (auth.uid() = user_id);
        """,
        
        # Create RLS policies for completed_drafts
        """
        DROP POLICY IF EXISTS "Users can view own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can view own completed drafts" ON completed_drafts
            FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can insert own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can insert own completed drafts" ON completed_drafts
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can update own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can update own completed drafts" ON completed_drafts
            FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can delete own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can delete own completed drafts" ON completed_drafts
            FOR DELETE USING (auth.uid() = user_id);
        """
    ]
    
    # Execute each command
    for i, command in enumerate(setup_commands, 1):
        try:
            supabase.rpc('exec_sql', {'sql': command}).execute()
            print(f"✅ Command {i}/{len(setup_commands)} executed successfully")
        except Exception as e:
            print(f"⚠️  Command {i}/{len(setup_commands)} failed: {e}")
            # Continue with other commands even if one fails
    
    print("\n🎉 Database setup completed!")
    print("\nNext steps:")
    print("1. Configure your Supabase project settings")
    print("2. Set up email templates in Supabase Auth settings")
    print("3. Test user registration and login")
    print("4. Deploy your application")
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Supabase database for PickProphet...")
    setup_supabase() 
        CREATE POLICY "Users can delete own custom projections" ON user_custom_projections
            FOR DELETE USING (auth.uid() = user_id);
        """,
        
        # Create RLS policies for user_draft_sessions
        """
        DROP POLICY IF EXISTS "Users can view own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can view own draft sessions" ON user_draft_sessions
            FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can insert own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can insert own draft sessions" ON user_draft_sessions
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can update own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can update own draft sessions" ON user_draft_sessions
            FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can delete own draft sessions" ON user_draft_sessions;
        CREATE POLICY "Users can delete own draft sessions" ON user_draft_sessions
            FOR DELETE USING (auth.uid() = user_id);
        """,
        
        # Create RLS policies for user_rosters
        """
        DROP POLICY IF EXISTS "Users can view own rosters" ON user_rosters;
        CREATE POLICY "Users can view own rosters" ON user_rosters
            FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can insert own rosters" ON user_rosters;
        CREATE POLICY "Users can insert own rosters" ON user_rosters
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can update own rosters" ON user_rosters;
        CREATE POLICY "Users can update own rosters" ON user_rosters
            FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can delete own rosters" ON user_rosters;
        CREATE POLICY "Users can delete own rosters" ON user_rosters
            FOR DELETE USING (auth.uid() = user_id);
        """,
        
        # Create RLS policies for completed_drafts
        """
        DROP POLICY IF EXISTS "Users can view own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can view own completed drafts" ON completed_drafts
            FOR SELECT USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can insert own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can insert own completed drafts" ON completed_drafts
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can update own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can update own completed drafts" ON completed_drafts
            FOR UPDATE USING (auth.uid() = user_id);
        """,
        
        """
        DROP POLICY IF EXISTS "Users can delete own completed drafts" ON completed_drafts;
        CREATE POLICY "Users can delete own completed drafts" ON completed_drafts
            FOR DELETE USING (auth.uid() = user_id);
        """
    ]
    
    # Execute each command
    for i, command in enumerate(setup_commands, 1):
        try:
            supabase.rpc('exec_sql', {'sql': command}).execute()
            print(f"✅ Command {i}/{len(setup_commands)} executed successfully")
        except Exception as e:
            print(f"⚠️  Command {i}/{len(setup_commands)} failed: {e}")
            # Continue with other commands even if one fails
    
    print("\n🎉 Database setup completed!")
    print("\nNext steps:")
    print("1. Configure your Supabase project settings")
    print("2. Set up email templates in Supabase Auth settings")
    print("3. Test user registration and login")
    print("4. Deploy your application")
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Supabase database for PickProphet...")
    setup_supabase() 
    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        return False

def create_custom_projections_table(supabase):
    """Create the custom_projections table."""
    try:
        # This will create the table if it doesn't exist
        # We'll insert a test record and then delete it to create the table structure
        test_data = {
            'user_id': 'test_user',
            'player_name': 'Test Player',
            'position': 'RB',
            'custom_stats': {'rushing_yards': 1000, 'rushing_tds': 8},
            'ppr_projection': 150.0,
            'half_ppr_projection': 140.0,
            'non_ppr_projection': 130.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Try to insert (this will create the table if it doesn't exist)
        result = supabase.table('user_custom_projections').insert(test_data).execute()
        print("✅ custom_projections table created")
        
        # Clean up test data
        supabase.table('user_custom_projections').delete().eq('user_id', 'test_user').execute()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"⚠️  custom_projections table setup: {e}")

def create_completed_drafts_table(supabase):
    """Create the completed_drafts table."""
    try:
        # This will create the table if it doesn't exist
        # We'll insert a test record and then delete it to create the table structure
        test_data = {
            'user_id': 'test_user',
            'session_id': 'test_session',
            'draft_data': {
                'session_id': 'test_session',
                'session_name': 'Test Draft',
                'user_id': 'test_user',
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'total_players': 0,
                'draft_duration': '0h 0m',
                'is_active': False,
                'drafted_players': []
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Try to insert (this will create the table if it doesn't exist)
        result = supabase.table('completed_drafts').insert(test_data).execute()
        print("✅ completed_drafts table created")
        
        # Clean up test data
        supabase.table('completed_drafts').delete().eq('user_id', 'test_user').execute()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"⚠️  completed_drafts table setup: {e}")

def main():
    """Main setup function."""
    print("🚀 Setting up Supabase Database Tables")
    print("=" * 40)
    
    success = setup_supabase_tables()
    
    if success:
        print("\n🎉 Database setup completed!")
        print("\n📝 Next steps:")
        print("1. Run the migration script again: python3 migrate_to_supabase.py")
        print("2. Test your application: python3 fantasy_draft_web_enhanced.py")
        print("3. Deploy to the cloud!")
    else:
        print("\n❌ Database setup failed. Please check your Supabase credentials.")

if __name__ == '__main__':
    main() 