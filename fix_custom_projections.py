#!/usr/bin/env python3
"""
Script to fix custom projections persistence and test Supabase connection
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def test_supabase_connection():
    """Test Supabase connection and check table structure."""
    
    # Initialize Supabase client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Connected to Supabase successfully")
        
        # Check if users table exists and has data
        try:
            users_result = supabase.table('users').select('*').limit(5).execute()
            print(f"✓ Users table exists with {len(users_result.data)} users")
            if users_result.data:
                print("Sample users:")
                for user in users_result.data[:3]:
                    print(f"  - {user.get('id', 'N/A')}: {user.get('email', 'N/A')}")
        except Exception as e:
            print(f"❌ Error accessing users table: {e}")
        
        # Check if user_custom_projections table exists and has data
        try:
            projections_result = supabase.table('user_custom_projections').select('*').limit(5).execute()
            print(f"✓ user_custom_projections table exists with {len(projections_result.data)} records")
            if projections_result.data:
                print("Sample custom projections:")
                for proj in projections_result.data[:3]:
                    print(f"  - {proj.get('player_name', 'N/A')} for user {proj.get('user_id', 'N/A')}")
        except Exception as e:
            print(f"❌ Error accessing user_custom_projections table: {e}")
        
        # Test inserting a test record
        try:
            test_data = {
                'user_id': 'test-user-123',
                'player_name': 'Test Player',
                'position': 'QB',
                'custom_stats': {
                    'passing_yards': 4000,
                    'passing_tds': 30,
                    'passing_ints': 10
                }
            }
            
            # Try to insert test data
            insert_result = supabase.table('user_custom_projections').insert(test_data).execute()
            print("✓ Successfully inserted test custom projection")
            
            # Clean up test data
            delete_result = supabase.table('user_custom_projections').delete().eq('user_id', 'test-user-123').execute()
            print("✓ Successfully deleted test custom projection")
            
        except Exception as e:
            print(f"❌ Error testing custom projection insert/delete: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return False

def fix_custom_projections_schema():
    """Fix the custom projections table schema if needed."""
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Connected to Supabase for schema fix")
        
        # Check current table structure
        try:
            result = supabase.table('user_custom_projections').select('*').limit(1).execute()
            print("✓ user_custom_projections table is accessible")
            
            # Check if the table has the right columns
            if result.data:
                sample_record = result.data[0]
                print("Current table structure:")
                for key, value in sample_record.items():
                    print(f"  - {key}: {type(value).__name__}")
            
        except Exception as e:
            print(f"❌ Error checking table structure: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during schema fix: {e}")
        return False

if __name__ == "__main__":
    print("Testing Supabase connection and custom projections...")
    print("=" * 50)
    
    # Test connection
    if test_supabase_connection():
        print("\n" + "=" * 50)
        print("Testing schema fixes...")
        fix_custom_projections_schema()
    else:
        print("❌ Cannot proceed without Supabase connection")
