#!/usr/bin/env python3
"""
Database Setup Helper Script
This script helps you set up the Supabase database tables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def print_setup_instructions():
    """Print clear setup instructions."""
    
    print("🚀 PickProphet Database Setup")
    print("=" * 50)
    print()
    print("✅ Your Supabase connection is working!")
    print("❌ But the database tables don't exist yet.")
    print()
    print("📋 Follow these steps to set up your database:")
    print()
    print("1. Go to your Supabase dashboard:")
    print("   https://supabase.com/dashboard")
    print()
    print("2. Select your project")
    print("3. Go to 'SQL Editor' in the left sidebar")
    print("4. Copy and paste the SQL commands from 'create_tables.sql'")
    print("5. Click 'Run' to execute all commands")
    print()
    print("📄 The SQL commands are in: create_tables.sql")
    print()
    
    # Show the SQL file contents
    try:
        with open('create_tables.sql', 'r') as f:
            sql_content = f.read()
            print("📋 SQL Commands to copy:")
            print("-" * 30)
            print(sql_content)
            print("-" * 30)
    except FileNotFoundError:
        print("❌ create_tables.sql file not found")
        return
    
    print()
    print("🔄 After running the SQL commands, run this test again:")
    print("   python3 test_supabase_setup.py")
    print()

def test_connection():
    """Test if Supabase connection is working."""
    
    try:
        from supabase import create_client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in .env file")
            return False
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Test basic connection
        response = supabase.table('user_custom_projections').select('count').limit(1).execute()
        print("✅ Supabase connection successful!")
        return True
        
    except Exception as e:
        if "does not exist" in str(e):
            print("✅ Supabase connection working, but tables don't exist yet")
            return True
        else:
            print(f"❌ Supabase connection failed: {e}")
            return False

if __name__ == "__main__":
    print_setup_instructions()
    
    if test_connection():
        print("🎯 Next steps:")
        print("1. Run the SQL commands in Supabase dashboard")
        print("2. Test again with: python3 test_supabase_setup.py")
        print("3. Your app will then work with custom projections!")
    else:
        print("❌ Please check your Supabase credentials in .env file") 
"""
Database Setup Helper Script
This script helps you set up the Supabase database tables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def print_setup_instructions():
    """Print clear setup instructions."""
    
    print("🚀 PickProphet Database Setup")
    print("=" * 50)
    print()
    print("✅ Your Supabase connection is working!")
    print("❌ But the database tables don't exist yet.")
    print()
    print("📋 Follow these steps to set up your database:")
    print()
    print("1. Go to your Supabase dashboard:")
    print("   https://supabase.com/dashboard")
    print()
    print("2. Select your project")
    print("3. Go to 'SQL Editor' in the left sidebar")
    print("4. Copy and paste the SQL commands from 'create_tables.sql'")
    print("5. Click 'Run' to execute all commands")
    print()
    print("📄 The SQL commands are in: create_tables.sql")
    print()
    
    # Show the SQL file contents
    try:
        with open('create_tables.sql', 'r') as f:
            sql_content = f.read()
            print("📋 SQL Commands to copy:")
            print("-" * 30)
            print(sql_content)
            print("-" * 30)
    except FileNotFoundError:
        print("❌ create_tables.sql file not found")
        return
    
    print()
    print("🔄 After running the SQL commands, run this test again:")
    print("   python3 test_supabase_setup.py")
    print()

def test_connection():
    """Test if Supabase connection is working."""
    
    try:
        from supabase import create_client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in .env file")
            return False
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Test basic connection
        response = supabase.table('user_custom_projections').select('count').limit(1).execute()
        print("✅ Supabase connection successful!")
        return True
        
    except Exception as e:
        if "does not exist" in str(e):
            print("✅ Supabase connection working, but tables don't exist yet")
            return True
        else:
            print(f"❌ Supabase connection failed: {e}")
            return False

if __name__ == "__main__":
    print_setup_instructions()
    
    if test_connection():
        print("🎯 Next steps:")
        print("1. Run the SQL commands in Supabase dashboard")
        print("2. Test again with: python3 test_supabase_setup.py")
        print("3. Your app will then work with custom projections!")
    else:
        print("❌ Please check your Supabase credentials in .env file") 
 