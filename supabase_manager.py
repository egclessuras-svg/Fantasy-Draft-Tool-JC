from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, List, Optional

load_dotenv()

class SupabaseManager:
    def __init__(self):
        self.supabase = None
        self.initialize_supabase()
    
    def initialize_supabase(self):
        """Initialize Supabase connection."""
        try:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                self.supabase: Client = create_client(supabase_url, supabase_key)
                print("Supabase connected successfully")
                self.setup_tables()
            else:
                print("Supabase credentials not found. Running in development mode without database.")
                self.supabase = None
        except Exception as e:
            print(f"Supabase initialization failed: {e}. Running in development mode without database.")
            self.supabase = None
    
    def setup_tables(self):
        """Setup database tables if they don't exist."""
        if not self.supabase:
            return
        
        try:
            # Create user_custom_projections table
            self.supabase.table('user_custom_projections').select('*').limit(1).execute()
            print("Custom projections table exists")
        except Exception as e:
            print(f"Table setup error (this is normal for new databases): {e}")
    
    # Custom Projections Methods
    def save_custom_projection(self, user_id: str, player_name: str, position: str, 
                              custom_stats: Dict, projections: Dict) -> bool:
        """Save custom projection to Supabase."""
        if not self.supabase:
            return False
        
        try:
            data = {
                'user_id': user_id,
                'player_name': player_name,
                'position': position,
                'custom_stats': custom_stats,
                'ppr_projection': projections.get('ppr', 0.0),
                'half_ppr_projection': projections.get('half-ppr', 0.0),
                'non_ppr_projection': projections.get('non-ppr', 0.0),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if projection already exists for this user and player
            existing = self.supabase.table('user_custom_projections').select('*').eq('user_id', user_id).eq('player_name', player_name).execute()
            
            if existing.data:
                # Update existing record
                self.supabase.table('user_custom_projections').update(data).eq('user_id', user_id).eq('player_name', player_name).execute()
            else:
                # Insert new record
                self.supabase.table('user_custom_projections').insert(data).execute()
            
            print(f"Saved custom projection for {player_name} to Supabase")
            return True
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False
    
    def get_custom_projections(self, user_id: str) -> Dict:
        """Get all custom projections for a user."""
        if not self.supabase:
            return {}
        
        try:
            result = self.supabase.table('user_custom_projections').select('*').eq('user_id', user_id).execute()
            projections = {}
            
            for record in result.data:
                player_name = record['player_name']
                projections[player_name] = {
                    'position': record['position'],
                    'custom_stats': record['custom_stats'],
                    'projections': {
                        'ppr': record['ppr_projection'],
                        'half-ppr': record['half_ppr_projection'],
                        'non-ppr': record['non_ppr_projection']
                    }
                }
            
            print(f"Loaded {len(projections)} custom projections from Supabase")
            return projections
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
            return {}
    
    def delete_custom_projection(self, user_id: str, player_name: str) -> bool:
        """Delete custom projection for a player."""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table('user_custom_projections').delete().eq('user_id', user_id).eq('player_name', player_name).execute()
            print(f"Deleted custom projection for {player_name} from Supabase")
            return True
        except Exception as e:
            print(f"Error deleting from Supabase: {e}")
            return False
    
    def delete_all_custom_projections(self, user_id: str) -> bool:
        """Delete all custom projections for a user."""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table('user_custom_projections').delete().eq('user_id', user_id).execute()
            print(f"Deleted all custom projections for user {user_id} from Supabase")
            return True
        except Exception as e:
            print(f"Error deleting all projections from Supabase: {e}")
            return False

    # Completed Drafts Methods
    def save_completed_draft(self, user_id: str, draft_data: Dict) -> bool:
        """Save completed draft to Supabase."""
        if not self.supabase:
            return False
        
        try:
            data = {
                'user_id': user_id,
                'session_id': draft_data.get('session_id'),
                'draft_data': draft_data,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if draft already exists for this user and session
            existing = self.supabase.table('completed_drafts').select('*').eq('user_id', user_id).eq('session_id', draft_data.get('session_id')).execute()
            
            if existing.data:
                # Update existing record
                self.supabase.table('completed_drafts').update(data).eq('user_id', user_id).eq('session_id', draft_data.get('session_id')).execute()
            else:
                # Insert new record
                self.supabase.table('completed_drafts').insert(data).execute()
            
            print(f"Saved completed draft {draft_data.get('session_id')} to Supabase")
            return True
        except Exception as e:
            print(f"Error saving draft to Supabase: {e}")
            return False
    
    def get_completed_drafts(self, user_id: str) -> List[Dict]:
        """Get all completed drafts for a user."""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('completed_drafts').select('*').eq('user_id', user_id).execute()
            drafts = []
            
            for record in result.data:
                drafts.append(record['draft_data'])
            
            print(f"Loaded {len(drafts)} completed drafts from Supabase")
            return drafts
        except Exception as e:
            print(f"Error loading drafts from Supabase: {e}")
            return []
    
    def get_completed_draft(self, user_id: str, session_id: str) -> Optional[Dict]:
        """Get a specific completed draft."""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('completed_drafts').select('*').eq('user_id', user_id).eq('session_id', session_id).execute()
            
            if result.data:
                return result.data[0]['draft_data']
            else:
                return None
        except Exception as e:
            print(f"Error loading draft from Supabase: {e}")
            return None
    
    def delete_completed_draft(self, user_id: str, session_id: str) -> bool:
        """Delete a completed draft."""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table('completed_drafts').delete().eq('user_id', user_id).eq('session_id', session_id).execute()
            print(f"Deleted completed draft {session_id} from Supabase")
            return True
        except Exception as e:
            print(f"Error deleting draft from Supabase: {e}")
            return False
    
    def delete_all_completed_drafts(self, user_id: str) -> bool:
        """Delete all completed drafts for a user."""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table('completed_drafts').delete().eq('user_id', user_id).execute()
            print(f"Deleted all completed drafts for user {user_id} from Supabase")
            return True
        except Exception as e:
            print(f"Error deleting all drafts from Supabase: {e}")
            return False

# Global instance
supabase_manager = SupabaseManager() 