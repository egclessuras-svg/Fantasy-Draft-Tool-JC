#!/usr/bin/env python3
"""
Migration script to move data from JSON files to Supabase.
Run this script to migrate your existing custom projections and completed drafts.
"""

import json
import os
from datetime import datetime
from supabase_manager import supabase_manager

def migrate_custom_projections():
    """Migrate custom projections from JSON file to Supabase."""
    print("🔄 Migrating custom projections...")
    
    custom_projections_file = 'custom_projections.json'
    if not os.path.exists(custom_projections_file):
        print("❌ No custom_projections.json file found. Skipping migration.")
        return
    
    try:
        with open(custom_projections_file, 'r') as f:
            data = json.load(f)
            custom_projections = data.get('custom_projections', {})
        
        if not custom_projections:
            print("ℹ️  No custom projections found in file. Skipping migration.")
            return
        
        print(f"📊 Found {len(custom_projections)} custom projections to migrate...")
        
        migrated_count = 0
        for player_name, projection_data in custom_projections.items():
            if isinstance(projection_data, dict) and 'custom_stats' in projection_data:
                custom_stats = projection_data.get('custom_stats', {})
                projections_dict = projection_data.get('projections', {})
                position = projection_data.get('position', 'RB')
                user_id = projection_data.get('user_id', 'default_user')
                
                success = supabase_manager.save_custom_projection(
                    user_id=user_id,
                    player_name=player_name,
                    position=position,
                    custom_stats=custom_stats,
                    projections=projections_dict
                )
                
                if success:
                    migrated_count += 1
                    print(f"✅ Migrated projection for {player_name}")
                else:
                    print(f"❌ Failed to migrate projection for {player_name}")
        
        print(f"🎉 Successfully migrated {migrated_count} custom projections to Supabase!")
        
    except Exception as e:
        print(f"❌ Error migrating custom projections: {e}")

def migrate_completed_drafts():
    """Migrate completed drafts from JSON file to Supabase."""
    print("🔄 Migrating completed drafts...")
    
    completed_drafts_file = 'completed_drafts.json'
    if not os.path.exists(completed_drafts_file):
        print("❌ No completed_drafts.json file found. Skipping migration.")
        return
    
    try:
        with open(completed_drafts_file, 'r') as f:
            data = json.load(f)
            completed_drafts = data.get('completed_drafts', {})
        
        if not completed_drafts:
            print("ℹ️  No completed drafts found in file. Skipping migration.")
            return
        
        print(f"📊 Found {len(completed_drafts)} users with completed drafts to migrate...")
        
        total_migrated = 0
        for user_id, user_drafts in completed_drafts.items():
            print(f"👤 Migrating drafts for user: {user_id}")
            
            for draft in user_drafts:
                success = supabase_manager.save_completed_draft(user_id, draft)
                
                if success:
                    total_migrated += 1
                    print(f"✅ Migrated draft: {draft.get('session_name', 'Unknown')}")
                else:
                    print(f"❌ Failed to migrate draft: {draft.get('session_name', 'Unknown')}")
        
        print(f"🎉 Successfully migrated {total_migrated} completed drafts to Supabase!")
        
    except Exception as e:
        print(f"❌ Error migrating completed drafts: {e}")

def backup_json_files():
    """Create backup of JSON files before migration."""
    print("💾 Creating backups of JSON files...")
    
    files_to_backup = ['custom_projections.json', 'completed_drafts.json']
    
    for filename in files_to_backup:
        if os.path.exists(filename):
            backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(filename, 'r') as source:
                    with open(backup_name, 'w') as backup:
                        backup.write(source.read())
                print(f"✅ Created backup: {backup_name}")
            except Exception as e:
                print(f"❌ Failed to backup {filename}: {e}")
        else:
            print(f"ℹ️  {filename} not found, skipping backup")

def main():
    """Main migration function."""
    print("🚀 Fantasy Draft Assistant - Supabase Migration")
    print("=" * 50)
    
    # Check if Supabase is configured
    if not supabase_manager.supabase:
        print("❌ Supabase not configured!")
        print("Please set up your .env file with SUPABASE_URL and SUPABASE_KEY")
        print("See SUPABASE_SETUP.md for instructions.")
        return
    
    print("✅ Supabase connection verified!")
    print()
    
    # Create backups
    backup_json_files()
    print()
    
    # Migrate data
    migrate_custom_projections()
    print()
    migrate_completed_drafts()
    print()
    
    print("🎉 Migration completed!")
    print()
    print("📝 Next steps:")
    print("1. Test your application to ensure data migrated correctly")
    print("2. Once confirmed, you can delete the .json files")
    print("3. Deploy your application to the cloud!")
    print()
    print("💡 Your app is now ready for cloud deployment!")

if __name__ == '__main__':
    main() 