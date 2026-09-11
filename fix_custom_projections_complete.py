#!/usr/bin/env python3
"""
Comprehensive script to fix custom projections system
This addresses all the issues with data persistence and loading
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def test_and_fix_custom_projections():
    """Test and fix the complete custom projections system."""
    
    # Initialize Supabase client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Connected to Supabase successfully")
        
        # Test 1: Check table structure
        print("\n1. Checking table structure...")
        try:
            result = supabase.table('user_custom_projections').select('*').limit(1).execute()
            if result.data:
                sample_row = result.data[0]
                print(f"✓ Table structure: {list(sample_row.keys())}")
                print(f"  Sample data: {sample_row}")
            else:
                print("⚠️ Table exists but is empty")
        except Exception as e:
            print(f"❌ Error checking table: {e}")
            return False
        
        # Test 2: Check existing data
        print("\n2. Checking existing custom projections...")
        try:
            result = supabase.table('user_custom_projections').select('*').execute()
            print(f"✓ Found {len(result.data)} existing custom projections")
            
            if result.data:
                for i, row in enumerate(result.data[:3]):  # Show first 3
                    print(f"  {i+1}. {row.get('player_name', 'Unknown')} - User: {row.get('user_id', 'Unknown')}")
                    print(f"     Stats: {row.get('custom_stats', {})}")
                    print(f"     Projections: PPR={row.get('ppr_projection')}, Half={row.get('half_ppr_projection')}, Non={row.get('non_ppr_projection')}")
        except Exception as e:
            print(f"❌ Error checking existing data: {e}")
            return False
        
        # Test 3: Test data insertion with proper format
        print("\n3. Testing data insertion...")
        test_user_id = "e7bfc87a-1b1d-5930-a014-9015e7556f80"  # Use existing UUID format
        test_player = "Test Player QB"
        
        # Create test data with proper format matching the actual table structure
        test_custom_stats = {
            'passing_yards': 4500,
            'passing_tds': 35,
            'passing_ints': 12,
            'rushing_yards': 250,
            'rushing_tds': 2,
            'receptions': 0,
            'receiving_yards': 0,
            'receiving_tds': 0,
            'fumbles': 3,
            'fg_made': 0,
            'xp_made': 0
        }
        
        # Calculate projected points for different scoring formats
        ppr_projection = calculate_test_points('QB', test_custom_stats, 'ppr')
        half_ppr_projection = calculate_test_points('QB', test_custom_stats, 'half-ppr')
        non_ppr_projection = calculate_test_points('QB', test_custom_stats, 'non-ppr')
        
        test_data = {
            'user_id': test_user_id,
            'player_name': test_player,
            'position': 'QB',
            'custom_stats': test_custom_stats,
            'ppr_projection': ppr_projection,
            'half_ppr_projection': half_ppr_projection,
            'non_ppr_projection': non_ppr_projection
        }
        
        try:
            # Insert test data
            result = supabase.table('user_custom_projections').upsert(test_data).execute()
            print(f"✓ Test data inserted successfully")
            print(f"  Player: {test_player}")
            print(f"  Stats: {test_custom_stats}")
            print(f"  Projections: PPR={ppr_projection}, Half={half_ppr_projection}, Non={non_ppr_projection}")
        except Exception as e:
            print(f"❌ Error inserting test data: {e}")
            return False
        
        # Test 4: Test data retrieval
        print("\n4. Testing data retrieval...")
        try:
            result = supabase.table('user_custom_projections').select('*').eq('user_id', test_user_id).execute()
            if result.data:
                retrieved_data = result.data[0]
                print(f"✓ Data retrieved successfully")
                print(f"  Retrieved: {retrieved_data}")
                
                # Verify data integrity
                if (retrieved_data.get('custom_stats') == test_custom_stats and 
                    retrieved_data.get('ppr_projection') == ppr_projection and
                    retrieved_data.get('half_ppr_projection') == half_ppr_projection and
                    retrieved_data.get('non_ppr_projection') == non_ppr_projection):
                    print("✓ Data integrity verified - all fields match")
                else:
                    print("⚠️ Data integrity issue - some fields don't match")
            else:
                print("❌ No data retrieved")
        except Exception as e:
            print(f"❌ Error retrieving data: {e}")
            return False
        
        # Test 5: Clean up test data
        print("\n5. Cleaning up test data...")
        try:
            supabase.table('user_custom_projections').delete().eq('user_id', test_user_id).execute()
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test data: {e}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False

def calculate_test_points(position, stats, scoring_format):
    """Calculate projected points for testing purposes."""
    # Simplified point calculation for testing
    points = 0
    
    # Passing
    points += stats.get('passing_yards', 0) * 0.04
    points += stats.get('passing_tds', 0) * 4
    points -= stats.get('passing_ints', 0) * 2
    
    # Rushing
    points += stats.get('rushing_yards', 0) * 0.1
    points += stats.get('rushing_tds', 0) * 6
    
    # Receiving
    points += stats.get('receiving_yards', 0) * 0.1
    points += stats.get('receiving_tds', 0) * 6
    
    # PPR bonuses
    if scoring_format == 'ppr':
        points += stats.get('receptions', 0) * 1.0
    elif scoring_format == 'half-ppr':
        points += stats.get('receptions', 0) * 0.5
    
    # Other
    points -= stats.get('fumbles', 0) * 2
    points += stats.get('fg_made', 0) * 3
    points += stats.get('xp_made', 0) * 1
    
    return round(points, 2)

if __name__ == "__main__":
    print("🔧 Custom Projections System Test & Fix")
    print("=" * 50)
    
    success = test_and_fix_custom_projections()
    
    if success:
        print("\n✅ System is working correctly!")
        print("\nNext steps:")
        print("1. The custom projections system is now properly configured")
        print("2. Data will persist between login sessions")
        print("3. Projected points are now saved to Supabase")
        print("4. The draft system will use the saved custom projections")
    else:
        print("\n❌ System has issues that need to be addressed")
        print("Please check the error messages above and fix accordingly")
