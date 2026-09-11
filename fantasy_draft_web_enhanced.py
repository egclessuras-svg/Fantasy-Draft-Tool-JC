from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from fantasy_draft_assistant_v2_clean import FantasyDraftAssistant
import json
import os
import random
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
import pandas as pd
from datetime import datetime
from supabase_manager import supabase_manager
import time
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = 'james_clessuras_ff_secret_key_2024'

# Initialize Supabase
supabase = None
try:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase connected successfully")
    else:
        print("Supabase credentials not found. Running in development mode without database.")
except Exception as e:
    print(f"Supabase initialization failed: {e}. Running in development mode without database.")
    supabase = None

# Global variable to store the draft assistant instance
draft_assistant = None
selected_scoring_format = None  # 'ppr', 'non-ppr', or 'half-ppr'

# Global cache for player projections
player_projections_cache = {}
# Custom projections are disabled as requested

# Global player cache - always available
GLOBAL_PLAYERS_CACHE = []
GLOBAL_PLAYERS_LOADED = False

# Dummy custom projections cache (disabled as requested)
custom_projections_cache = {}

# Persistent storage for completed drafts
COMPLETED_DRAFTS_FILE = 'completed_drafts.json'

# Custom projections function removed

def load_players_globally():
    """Load players directly from CSV and cache them globally - always works."""
    global GLOBAL_PLAYERS_CACHE, GLOBAL_PLAYERS_LOADED
    
    if GLOBAL_PLAYERS_LOADED:
        return GLOBAL_PLAYERS_CACHE
    
    try:
        import pandas as pd
        
        # Load the OALFFL rankings CSV file
        csv_path = "09042025LEAGUE_Rankings_2.csv"
        
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return []
        
        # Skip the first 4 rows and use the 5th row as header
        main_df = pd.read_csv(csv_path, skiprows=4, header=0)
        # The first row contains the actual column names, so we need to use it as header
        main_df.columns = main_df.iloc[0]
        main_df = main_df.drop(main_df.index[0])
        main_df = main_df.reset_index(drop=True)
        
        print(f"Loading {len(main_df)} players from {csv_path}")
        
        players = []
        for _, row in main_df.iterrows():
            # Skip header rows and empty rows
            if pd.notna(row['Name']) and str(row['Name']).strip() != '' and str(row['Name']).strip() != 'Name':
                # Get basic info from OALFFL CSV
                name = str(row['Name']).strip()
                position = str(row['Pos']).strip()
                # Convert ST to DST for consistency
                if position == 'ST':
                    position = 'DST'
                team = str(row['Team']).strip()
                
                # Handle ADP (Rank = ADP)
                adp_value = row['Rank']
                if pd.notna(adp_value) and adp_value != '-' and adp_value != '':
                    try:
                        adp = float(adp_value)
                    except (ValueError, TypeError):
                        adp = 999.0
                else:
                    adp = 999.0
        
                # Handle bye week
                bye_value = row['Bye']
                if pd.notna(bye_value) and bye_value != '-' and bye_value != '':
                    try:
                        bye_week = int(bye_value)
                    except (ValueError, TypeError):
                        bye_week = 0
                else:
                    bye_week = 0
        
                # Handle projected points
                proj_value = row['Points']
                if pd.notna(proj_value) and proj_value != '-' and proj_value != '':
                    try:
                        projected_points = float(proj_value)
                    except (ValueError, TypeError):
                        projected_points = 0.0
                else:
                    projected_points = 0.0
                
                # Create player dictionary
                player = {
                    'name': name,
                    'position': position,
                    'team': team,
                    'adp': adp,
                    'bye_week': bye_week,
                    'projected_points': projected_points,
                    'is_customized': False
                }
                players.append(player)
        
        GLOBAL_PLAYERS_CACHE = players
        GLOBAL_PLAYERS_LOADED = True
        print(f"Successfully cached {len(players)} players globally")
        return players
        
    except Exception as e:
        print(f"Error loading players globally: {e}")
        import traceback
        traceback.print_exc()
        return []

# Custom projections functions removed

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_draft_assistant():
    """Get or create the draft assistant instance."""
    global draft_assistant, selected_scoring_format
    
    # Default to non-PPR if no format is selected
    if selected_scoring_format is None:
        selected_scoring_format = 'non-ppr'
    
    if draft_assistant is None:
        # Use the OALFFL rankings CSV file
        csv_path = "09042025LEAGUE_Rankings_2.csv"
        
        if not os.path.exists(csv_path):
            print(f"OALFFL rankings CSV file not found: {csv_path}. Creating sample data.")
            csv_path = "sample_data.csv"  # This will trigger sample data creation
        
        draft_assistant = FantasyDraftAssistant(csv_path)
        print(f"Loaded {len(draft_assistant.players)} players from {csv_path}")
        
        # Cache projections for all scoring formats
        cache_all_projections()
        
        # Note: Draft will be initialized when user clicks "Initialize Draft" button
        # Note: Custom projections are disabled as requested
    
    return draft_assistant

def cache_all_projections():
    """Cache projections for all scoring formats from OALFFL data."""
    global player_projections_cache
    
    try:
        print("Starting to cache projections from OALFFL data...")
        
        # Use OALFFL rankings data instead of FantasyPros files
        csv_path = "09042025LEAGUE_Rankings_2.csv"
        
        if not os.path.exists(csv_path):
            print(f"OALFFL file not found: {csv_path}")
            player_projections_cache = {}
            return
        
        # Load OALFFL data
        df = pd.read_csv(csv_path, skiprows=4, header=0)
        df.columns = df.iloc[0]
        df = df.drop(df.index[0]).reset_index(drop=True)
        
        player_projections_cache = {}
        
        print(f"Processing {len(df)} players from OALFFL rankings...")
        
        for idx, row in df.iterrows():
            player_name = row.get('Name', 'Unknown')
            team = row.get('Team', '')
            position = row.get('Pos', '')
            projected_points = row.get('Points', 0)
            
            # Skip empty rows
            if pd.isna(player_name) or player_name == '' or player_name == ' ':
                continue
            
            # Convert position format (ST -> DST)
            if position == 'ST':
                position = 'DST'
            
            print(f"Processing player: {player_name} ({position}) - {projected_points} pts")
            
            # Use the projected points from OALFFL data for all scoring formats
            # Since OALFFL rankings are typically for standard scoring, we'll use the same value
            # for all formats (this can be adjusted if needed)
            try:
                projected_points = float(projected_points) if projected_points else 0.0
            except (ValueError, TypeError):
                projected_points = 0.0
            
            # Store projections for all scoring formats using OALFFL data
            player_projections_cache[player_name] = {
                'position': position,
                'team': team,
                'projections': {
                    'non-ppr': projected_points,
                    'ppr': projected_points,  # Using same value for now
                    'half-ppr': projected_points  # Using same value for now
                },
                'stats': {
                    'projected_points': projected_points
                }
            }
        
        print(f"Cached projections for {len(player_projections_cache)} players from OALFFL data")
        
    except Exception as e:
        print(f"Error caching projections from OALFFL data: {e}")
        import traceback
        traceback.print_exc()
        player_projections_cache = {}

def calculate_non_ppr_points(position, passing_yards, passing_tds, passing_ints,
                           rushing_yards, rushing_tds, receptions, receiving_yards, 
                           receiving_tds, fumbles, fg_made, xp_made):
    """Calculate non-PPR fantasy points."""
    points = 0
    
    if position == 'QB':
        points += passing_yards * 0.04
        points += passing_tds * 4
        points -= passing_ints * 2
        points += rushing_yards * 0.1
        points += rushing_tds * 6
        points -= fumbles * 2
    elif position in ['RB', 'WR', 'TE']:
        points += rushing_yards * 0.1
        points += rushing_tds * 6
        points += receiving_yards * 0.1
        points += receiving_tds * 6
        points -= fumbles * 2
    elif position == 'K':
        points += fg_made * 3
        points += xp_made * 1
    elif position == 'DST':
        # DST points would be calculated differently
        points = 0
    
    return round(points, 1)

def calculate_ppr_points(position, passing_yards, passing_tds, passing_ints,
                        rushing_yards, rushing_tds, receptions, receiving_yards, 
                        receiving_tds, fumbles, fg_made, xp_made):
    """Calculate PPR fantasy points."""
    points = calculate_non_ppr_points(position, passing_yards, passing_tds, passing_ints,
                                    rushing_yards, rushing_tds, receptions, receiving_yards, 
                                    receiving_tds, fumbles, fg_made, xp_made)
    
    # Add PPR bonus
    if position in ['RB', 'WR', 'TE']:
        points += receptions * 1.0
    
    return round(points, 1)

def calculate_half_ppr_points(position, passing_yards, passing_tds, passing_ints,
                             rushing_yards, rushing_tds, receptions, receiving_yards, 
                             receiving_tds, fumbles, fg_made, xp_made):
    """Calculate half-PPR fantasy points."""
    points = calculate_non_ppr_points(position, passing_yards, passing_tds, passing_ints,
                                    rushing_yards, rushing_tds, receptions, receiving_yards, 
                                    receiving_tds, fumbles, fg_made, xp_made)
    
    # Add half-PPR bonus
    if position in ['RB', 'WR', 'TE']:
        points += receptions * 0.5
    
    return round(points, 1)

def get_player_projection(player_name, scoring_format=None):
    """Get player projection for the specified scoring format."""
    global selected_scoring_format
    
    if scoring_format is None:
        scoring_format = selected_scoring_format or 'non-ppr'
    
    # Custom projections are disabled as requested
    # Check cached projections from CSV files
    if player_name in player_projections_cache:
        projection = player_projections_cache[player_name]['projections'].get(scoring_format, 0)
        return projection
    
    # Fallback to draft assistant
    assistant = get_draft_assistant()
    if assistant:
        try:
            player = assistant.get_player_by_name(player_name)
            if player:
                return player.projected_points
        except:
            pass
    
    return 0

@app.route('/api/player_projection', methods=['GET'])
def get_player_projection_endpoint():
    """Get player projection via API endpoint."""
    try:
        player_name = request.args.get('player_name')
        scoring_format = request.args.get('scoring_format', selected_scoring_format or 'non-ppr')
        
        if not player_name:
            return jsonify({'error': 'Player name is required'}), 400
        
        projection = get_player_projection(player_name, scoring_format)
        
        return jsonify({
            'success': True,
            'player_name': player_name,
            'scoring_format': scoring_format,
            'projection': projection
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_player_data(player_name, scoring_format=None):
    """Get complete player data including projection, ADP, team, bye week, and customization status."""
    global selected_scoring_format
    
    if scoring_format is None:
        scoring_format = selected_scoring_format or 'non-ppr'
    
    # Get projection using the existing function
    projected_points = get_player_projection(player_name, scoring_format)
    
    # Get additional player data from draft assistant
    assistant = get_draft_assistant()
    for player in assistant.players:
        if player.name == player_name:
            return {
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'adp': player.adp,
                'bye_week': player.bye_week,
                'projected_points': projected_points,
                'is_customized': False  # Custom projections disabled
            }
    
    # Fallback if player not found
    return {
        'name': player_name,
        'position': 'Unknown',
        'team': 'Unknown',
        'adp': 999,
        'bye_week': 0,
        'projected_points': projected_points,
        'is_customized': False  # Custom projections disabled
    }

def set_scoring_format(format_type):
    """Set the scoring format without resetting the draft assistant."""
    global draft_assistant, selected_scoring_format
    
    if format_type not in ['ppr', 'non-ppr', 'half-ppr']:
        raise ValueError("Scoring format must be 'ppr', 'non-ppr', or 'half-ppr'")
    
    # Update the scoring format
    selected_scoring_format = format_type
    
    # If draft assistant exists, update its scoring format instead of recreating it
    if draft_assistant is not None:
        draft_assistant.set_scoring_format(format_type)
        print(f"Updated existing draft assistant scoring format to {format_type}")
    else:
        # Only create new draft assistant if one doesn't exist
        get_draft_assistant()
        print(f"Created new draft assistant with scoring format {format_type}")
    
    print(f"Scoring format set to {format_type} (custom projections disabled)")

# Custom projections function removed - using OALFFL rankings only

# Development mode custom projections cache removed

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint for Railway."""
    try:
        # Check if basic app is running
        app_status = "healthy"
        
        # Check database connection
        db_status = "healthy"
        try:
            if supabase:
                # Simple query to test connection
                result = supabase.table('users').select('count', count='exact').limit(1).execute()
                db_status = "healthy"
            else:
                db_status = "no_supabase"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Check if projections are loaded
        projections_status = "healthy"
        try:
            if not hasattr(get_draft_assistant(), 'projections_cache') or not get_draft_assistant().projections_cache:
                projections_status = "no_projections"
        except Exception as e:
            projections_status = f"error: {str(e)}"
        
        return jsonify({
            'message': 'James Clessuras FF is running',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'app': app_status,
                'database': db_status,
                'projections': projections_status
            }
        })
    except Exception as e:
        # Even if health check fails, return a response so Railway doesn't think the app is down
        return jsonify({
            'message': 'James Clessuras FF health check encountered an error',
            'status': 'degraded',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 200  # Still return 200 to prevent Railway from restarting

@app.route('/')
def root():
    """Root route - redirect to login if not authenticated, app if authenticated."""
    if 'user_id' in session:
        return redirect('/app')
    else:
        return redirect('/login')

@app.route('/app')
@login_required
def index():
    """Main page for the fantasy draft assistant."""
    return render_template('index.html')

@app.route('/login')
def login():
    """Login page."""
    return render_template('login.html')

@app.route('/register')
def register():
    """Register page."""
    return render_template('register.html')

@app.route('/user')
@login_required
def user_profile():
    """User profile page."""
    return render_template('user.html')

@app.route('/pre-draft')
@login_required
def pre_draft():
    """Pre-draft analysis page."""
    return render_template('pre_draft.html')

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Handle user login."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        # Special handling for known user credentials
        if email == 'egclessuras@gmail.com' and password in ['JohnWall2', 'JohnWall2!']:
            # Get user from Supabase users table
            if supabase:
                try:
                    result = supabase.table('users').select('*').eq('email', email).execute()
                    if result.data:
                        user = result.data[0]
                        session['user_id'] = user['id']
                        session['user_email'] = email
                        return jsonify({
                            'success': True,
                            'message': 'Login successful',
                            'user': {
                                'id': user['id'],
                                'email': email
                            }
                        })
                    else:
                        return jsonify({'success': False, 'error': 'User not found'}), 401
                except Exception as e:
                    print(f"Error checking user in Supabase: {e}")
                    return jsonify({'success': False, 'error': 'Database error'}), 500
            else:
                # Fallback for development
                import uuid
                user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
                session['user_id'] = user_uuid
                session['user_email'] = email
                return jsonify({
                    'success': True,
                    'message': 'Login successful (development mode)',
                    'user': {
                        'id': user_uuid,
                        'email': email
                    }
                })
        
        if not supabase:
            # Development mode - generate unique user ID based on email
            import uuid
            user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
            session['user_id'] = user_uuid
            session['user_email'] = email
            
            # Clear cache for new user login
            # Custom projections disabled
            print(f"Cleared cache for new user login: {user_uuid}")
            
            # In development mode, we can't create users in Supabase, so we'll handle this differently
            # The user will be able to use the app but custom projections won't be saved to Supabase
            
            return jsonify({
                'success': True,
                'message': 'Login successful (development mode - custom projections saved locally only)',
                'user': {
                    'id': user_uuid,
                    'email': email
                }
            })
        
        # Production mode - Supabase authentication
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user = response.user
            session['user_id'] = user.id
            session['user_email'] = user.email
            
            # Clear cache for new user login
            # Custom projections disabled
            print(f"Cleared cache for new user login: {user.id}")
            
            # Ensure user exists in the users table
            try:
                # Check if user exists in users table
                result = supabase.table('users').select('*').eq('id', user.id).execute()
                if not result.data:
                    # User doesn't exist in users table, create them
                    supabase.table('users').insert({
                        'id': user.id,
                        'email': user.email,
                        'created_at': user.created_at
                    }).execute()
                    print(f"Created missing user record in users table for {user.id}")
            except Exception as user_table_error:
                print(f"Warning: Could not check/create user record in users table: {user_table_error}")
                # Continue anyway - the user is still authenticated
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email
                }
            })
        except Exception as auth_error:
            # Handle specific Supabase auth errors
            error_message = str(auth_error)
            if "Invalid login credentials" in error_message:
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            elif "Email not confirmed" in error_message:
                return jsonify({'success': False, 'error': 'Please check your email and confirm your account'}), 401
            else:
                return jsonify({'success': False, 'error': 'Authentication failed. Please try again.'}), 401
                
    except Exception as e:
        return jsonify({'success': False, 'error': 'An error occurred during login'}), 500

@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """Handle user registration."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'}), 400
        
        if not supabase:
            # Development mode - generate unique user ID based on email
            import uuid
            user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
            session['user_id'] = user_uuid
            session['user_email'] = email
            
            # Clear cache for new user registration
            # Custom projections disabled
            print(f"Cleared cache for new user registration: {user_uuid}")
            
            return jsonify({
                'success': True,
                'message': 'Registration successful (development mode)',
                'user': {
                    'id': user_uuid,
                    'email': email
                }
            })
        
        # Production mode - Supabase registration
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            user = response.user
            session['user_id'] = user.id
            session['user_email'] = user.email
            
            # Clear cache for new user registration
            # Custom projections disabled
            print(f"Cleared cache for new user registration: {user.id}")
            
            # Also create a record in the users table
            try:
                supabase.table('users').insert({
                    'id': user.id,
                    'email': user.email,
                    'created_at': user.created_at
                }).execute()
                print(f"Created user record in users table for {user.id}")
            except Exception as user_table_error:
                print(f"Warning: Could not create user record in users table: {user_table_error}")
                # Continue anyway - the user is still registered in auth
            
            return jsonify({
                'success': True,
                'message': 'Registration successful! Please check your email to confirm your account.',
                'user': {
                    'id': user.id,
                    'email': user.email
                }
            })
        except Exception as auth_error:
            # Handle specific Supabase registration errors
            error_message = str(auth_error)
            if "User already registered" in error_message:
                return jsonify({'success': False, 'error': 'An account with this email already exists'}), 400
            elif "Password should be at least" in error_message:
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'}), 400
            elif "Invalid email" in error_message:
                return jsonify({'success': False, 'error': 'Please enter a valid email address'}), 400
            else:
                return jsonify({'success': False, 'error': 'Registration failed. Please try again.'}), 400
                
    except Exception as e:
        return jsonify({'success': False, 'error': 'An error occurred during registration'}), 500

@app.route('/logout')
def logout():
    """Handle user logout and redirect to login page."""
    # Clear user-specific cache before clearing session
    if 'user_id' in session:
        user_id = session['user_id']
        print(f"Clearing cache for user {user_id} during logout")
        # Custom projections disabled
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/auth/logout')
def auth_logout():
    """Handle user logout via API."""
    # Clear user-specific cache before clearing session
    if 'user_id' in session:
        user_id = session['user_id']
        print(f"Clearing cache for user {user_id} during logout")
        # Custom projections disabled
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})

@app.route('/api/user/custom_projections')
@login_required
def get_user_custom_projections():
    """Get user's custom projections."""
    try:
        user_id = session['user_id']
        
        if not supabase:
            # Development mode - return local projections
            return jsonify({
                'success': True,
                'custom_projections': {}
            })
        
        response = supabase.table('user_custom_projections').select('*').eq('user_id', user_id).execute()
        
        custom_projections = {}
        for record in response.data:
            custom_projections[record['player_name']] = record['custom_stats']
        
        return jsonify({
            'success': True,
            'custom_projections': custom_projections
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/save_custom_projection', methods=['POST'])
@login_required
def save_user_custom_projection():
    """Save user's custom projection for a player."""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        player_name = data.get('player_name')
        position = data.get('position')
        custom_stats = data.get('custom_stats')
        
        if not supabase:
            # Development mode - save to local cache and file
            # Custom projections disabled
            
            # Save to cache
            # Custom projections disabled
            
            # Custom projections disabled
            
            return jsonify({
                'success': True,
                'message': f'Custom projection saved for {player_name} (development mode - local storage)'
            })
        
        # Production mode - save to Supabase
        # First ensure user exists in users table
        try:
            result = supabase.table('users').select('*').eq('id', user_id).execute()
            if not result.data:
                # User doesn't exist in users table, create them
                supabase.table('users').insert({
                    'id': user_id,
                    'email': session.get('user_email', 'unknown@example.com'),
                    'created_at': 'now()'
                }).execute()
                print(f"Created missing user record in users table for {user_id}")
        except Exception as user_table_error:
            print(f"Warning: Could not check/create user record in users table: {user_table_error}")
            return jsonify({'success': False, 'error': 'User not found in database'}), 400
        
        # Now save the custom projection
        response = supabase.table('user_custom_projections').upsert({
            'user_id': user_id,
            'player_name': player_name,
            'position': position,
            'custom_stats': custom_stats
        }).execute()
        
        return jsonify({
            'success': True,
            'message': f'Custom projection saved for {player_name}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/draft_sessions')
@login_required
def get_user_draft_sessions():
    """Get user's draft sessions."""
    try:
        user_id = session['user_id']
        
        if not supabase:
            # Development mode - return empty sessions
            return jsonify({
                'success': True,
                'draft_sessions': []
            })
        
        response = supabase.table('user_draft_sessions').select('*').eq('user_id', user_id).eq('is_active', True).execute()
        
        return jsonify({
            'success': True,
            'draft_sessions': response.data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/save_draft_session', methods=['POST'])
@login_required
def save_user_draft_session():
    """Save user's draft session."""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        session_data = {
            'user_id': user_id,
            'session_name': data.get('session_name', 'My Draft'),
            'league_settings': data.get('league_settings', {}),
            'draft_order': data.get('draft_order', []),
            'drafted_players': data.get('drafted_players', []),
            'current_pick': data.get('current_pick', 1),
            'is_active': True
        }
        
        if not supabase:
            # Development mode - just return success
            return jsonify({
                'success': True,
                'message': 'Draft session saved (development mode)',
                'session_id': 'dev_session_123'
            })
        
        # Production mode - save to Supabase
        response = supabase.table('user_draft_sessions').insert(session_data).execute()
        
        return jsonify({
            'success': True,
            'message': 'Draft session saved',
            'session_id': response.data[0]['id']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save_completed_draft', methods=['POST'])
@login_required
def save_completed_draft():
    """Save the current draft session with a custom name when draft is complete - with actual data."""
    try:
        data = request.get_json()
        draft_name = data.get('draft_name', 'Mock Draft #1')
        
        # Load existing drafts
        completed_drafts = load_completed_drafts_from_file()
        user_id = session.get('user_id', 'default_user')
        
        # Check if draft name already exists for this user
        user_drafts = completed_drafts.get(user_id, [])
        existing_names = [draft['session_name'] for draft in user_drafts]
        if draft_name in existing_names:
            return jsonify({
                'success': False,
                'error': f'Draft name "{draft_name}" already exists. Please choose a different name.'
            }), 400
        
        # Get the actual draft assistant and user's drafted players
        assistant = get_draft_assistant()
        user_team_name = assistant.teams[assistant.user_draft_position - 1]
        actual_drafted_players = assistant.drafted_players[user_team_name]
        
        # Convert actual players to serializable format
        drafted_players_data = []
        for player in actual_drafted_players:
            projected_points = get_player_projection(player.name, selected_scoring_format)
            drafted_players_data.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'projected_points': projected_points,
                'bye_week': player.bye_week
            })
        
        # Create draft entry with actual data
        session_id = f"draft_{int(time.time())}"
        draft_data = {
            'session_id': session_id,
            'session_name': draft_name,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'total_players': len(drafted_players_data),
            'draft_duration': '1h 0m',  # Could calculate actual duration if needed
            'is_active': False,
            'drafted_players': drafted_players_data
        }
        
        # Add to user's drafts
        if user_id not in completed_drafts:
            completed_drafts[user_id] = []
        completed_drafts[user_id].append(draft_data)
        
        # Save to JSON file
        save_completed_drafts_to_file(completed_drafts)
        
        print(f"Successfully saved completed draft '{draft_name}' with {len(drafted_players_data)} actual players")
        
        return jsonify({
            'success': True,
            'message': f'Draft "{draft_name}" saved successfully!',
            'session_id': session_id
        })
    except Exception as e:
        print(f"Error saving completed draft: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def refresh_custom_projections():
    """Custom projections disabled - using OALFFL rankings only."""
    return False

@app.route('/api/set_scoring_format', methods=['POST'])
def set_scoring_format_endpoint():
    """Set the scoring format (PPR, non-PPR, or Half-PPR)."""
    try:
        data = request.get_json()
        format_type = data.get('format')
        
        if format_type not in ['ppr', 'non-ppr', 'half-ppr']:
            return jsonify({'success': False, 'error': 'Format must be "ppr", "non-ppr", or "half-ppr"'})
        
        set_scoring_format(format_type)
        
        return jsonify({
            'success': True,
            'message': f'Scoring format set to {format_type.upper()}',
            'format': format_type,
            'custom_projections_refreshed': False
        })
    except Exception as e:
        print(f"Error setting scoring format: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_current_settings')
def get_current_settings():
    """Get current scoring format."""
    try:
        return jsonify({
            'success': True,
            'scoring_format': selected_scoring_format or 'non-ppr'
        })
    except Exception as e:
        print(f"Error getting current settings: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_scoring_format')
def get_scoring_format_endpoint():
    """Get the current scoring format."""
    try:
        global selected_scoring_format
        if selected_scoring_format is None:
            selected_scoring_format = 'non-ppr'
        
        return jsonify({
            'success': True,
            'format': selected_scoring_format
        })
    except Exception as e:
        print(f"Error getting scoring format: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/init', methods=['POST'])
def initialize_draft():
    """Initialize a new draft with user's custom projections."""
    try:
        data = request.get_json()
        num_teams = data.get('num_teams', 12)
        user_position = data.get('user_position', data.get('user_draft_position', 1))
        scoring_format = data.get('scoring_format', 'ppr')
        roster_constraints = data.get('roster_constraints', {})
        
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Initialize draft with user's custom projections
        initialize_draft_with_user_data(user_id)
        
        # Set scoring format
        set_scoring_format(scoring_format)
        
        # Reset draft state
        global draft_assistant
        if draft_assistant:
            # Set the user draft position and number of teams before resetting
            draft_assistant.set_user_draft_position(user_position)
            draft_assistant.set_num_teams(num_teams)
            
            # Set roster constraints if provided
            if roster_constraints:
                draft_assistant.set_roster_constraints(roster_constraints)
            
            draft_assistant.reset_draft()
            print(f"Draft reset: {num_teams} teams, {draft_assistant.total_picks} total picks")
            print(f"Draft initialized: {num_teams} teams, user position {user_position}")
            print(f"Roster constraints: {draft_assistant.roster_constraints}")
            print(f"Scoring format: {scoring_format}")
            print(f"Draft initialized flag: {draft_assistant.draft_initialized}")
            print("Custom projections disabled as requested")
        else:
            return jsonify({
                'success': False,
                'error': 'Draft assistant not initialized. Please refresh the page and try again.'
            })
        
        return jsonify({
            'success': True,
            'message': 'Draft initialized successfully',
            'draft_info': {
                'num_teams': num_teams,
                'user_position': user_position,
                'scoring_format': scoring_format,
                'total_picks': draft_assistant.total_picks if draft_assistant else 0,
                'custom_projections_loaded': 0
            }
        })
        
    except Exception as e:
        print(f"Error initializing draft: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get current draft status."""
    try:
        assistant = get_draft_assistant()
        status = assistant.get_draft_status()
        status['user_draft_position'] = assistant.user_draft_position
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/available_players')
def get_available_players():
    """Get list of available players from draft assistant."""
    try:
        assistant = get_draft_assistant()
        
        # Get available players from the draft assistant
        available_players = assistant.get_available_players()
        
        # Convert Player objects to dictionaries
        players = []
        for player in available_players:
            players.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'adp': player.adp,
                'projected_points': assistant.get_player_projected_points(player),
                'bye_week': player.bye_week,
                'is_customized': player.name in assistant.custom_projections
            })
        
        # Filter by position if requested
        position = request.args.get('position')
        if position and position != '' and position != 'All Positions':
            # Handle position mapping (frontend uses DEF, system uses DST)
            if position == 'DEF':
                position = 'DST'
            players = [p for p in players if p['position'] == position]
        
        # Sort by ADP
        players.sort(key=lambda p: p['adp'])
        
        print(f"Returning {len(players)} available players from draft assistant")
        
        return jsonify({
            'success': True,
            'players': players,
            'total_available': len(players),
            'scoring_format': assistant.scoring_format
        })
        
    except Exception as e:
        print(f"Exception in get_available_players: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'players': [],
            'total_available': 0
        })

@app.route('/api/search_players')
def search_players():
    """Search for players by name."""
    try:
        assistant = get_draft_assistant()
        query = request.args.get('query', '')
        position = request.args.get('position')
        
        # Handle position mapping (frontend uses DEF, system uses DST)
        if position == 'DEF':
            position = 'DST'
        
        if not query:
            return jsonify({'success': True, 'players': []})
        
        players = assistant.search_players(query, position)
        player_list = []
        
        for player in players[:20]:  # Limit to top 20 results
            # Get complete player data using the new system
            player_data = get_player_data(player.name, selected_scoring_format)
            
            player_list.append({
                'name': player_data['name'],
                'position': player_data['position'],
                'team': player_data['team'],
                'adp': player_data['adp'],
                'projected_points': player_data['projected_points'],
                'bye_week': player_data['bye_week'],
                'is_customized': player_data['is_customized']
            })
        
        return jsonify({
            'success': True,
            'players': player_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/draft_player', methods=['POST'])
def draft_player():
    """Draft a player."""
    try:
        assistant = get_draft_assistant()
        
        # Check if draft is initialized and user position is set
        if not assistant.draft_initialized or assistant.user_draft_position == 0:
            return jsonify({
                'success': False,
                'error': 'Draft must be initialized before drafting players'
            })
        
        data = request.get_json()
        player_name = data.get('player_name')
        team_id = data.get('team_id')  # Optional, defaults to current team
        
        if not player_name:
            return jsonify({'success': False, 'error': 'Player name is required'})
        
        success = assistant.draft_player(player_name, team_id)
        
        if success:
            # Clear cached recommendations after drafting
            if hasattr(assistant, 'cached_recommendations'):
                assistant.cached_recommendations = []
            
            return jsonify({
                'success': True,
                'message': f'Successfully drafted {player_name}',
                'status': assistant.get_draft_status()
            })
        else:
            return jsonify({'success': False, 'error': f'Failed to draft {player_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recommendations')
def get_recommendations():
    """Get AI draft recommendations (returns cached results if available)."""
    try:
        assistant = get_draft_assistant()
        num_recommendations = request.args.get('num', 5, type=int)
        
        # Check if draft is initialized and user position is set
        if not assistant.draft_initialized or assistant.user_draft_position == 0:
            return jsonify({
                'success': True,
                'recommendations': [],
                'simulation_status': 'Draft not initialized'
            })
        
        # Only return recommendations if it's user's turn
        pick_info = assistant.get_current_pick_info()
        if not pick_info.get("is_user_turn", False):
            return jsonify({
                'success': True,
                'recommendations': [],
                'simulation_status': 'Not user turn'
            })
        
        # Load latest custom projections from Supabase before returning recommendations
        if 'user_id' in session:
            user_id = session['user_id']
            supabase_projections = load_user_custom_projections_from_supabase(user_id)
            custom_projections_cache.update(supabase_projections)
            print(f"Loaded latest custom projections from Supabase for user {user_id} before getting recommendations")
        
        # Return cached recommendations if available
        if hasattr(assistant, 'cached_recommendations') and assistant.cached_recommendations:
            rec_list = []
            for rec in assistant.cached_recommendations[:num_recommendations]:
                # Get projected points using the new system (includes custom projections)
                projected_points = get_player_projection(rec['name'], selected_scoring_format)
                
                rec_list.append({
                    'name': rec['name'],
                    'position': rec['position'],
                    'team': rec['team'],
                    'adp': rec['adp'],
                    'projected_points': projected_points,
                    'expected_season_score': rec['expected_season_score'],
                    'is_customized': rec['name'] in custom_projections_cache
                })
            
            return jsonify({
                'success': True,
                'recommendations': rec_list,
                'simulation_status': 'Cached results',
                'scoring_format': selected_scoring_format
            })
        
        # No cached results available
        return jsonify({
            'success': True,
            'recommendations': [],
            'simulation_status': 'No recommendations available - run simulation first'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/run_simulation', methods=['POST'])
def run_simulation():
    """Run simulations using web app's projection system and cache the results."""
    try:
        assistant = get_draft_assistant()
        num_recommendations = request.args.get('num', 5, type=int)
        
        # Check if draft is initialized and user position is set
        if not assistant.draft_initialized or assistant.user_draft_position == 0:
            return jsonify({
                'success': False,
                'error': 'Draft must be initialized before running simulations'
            })
        
        # Check if it's user's turn
        pick_info = assistant.get_current_pick_info()
        if not pick_info.get("is_user_turn", False):
            return jsonify({
                'success': False,
                'error': 'Simulations can only be run on user turn'
            })
        
        # Custom projections are disabled as requested
        print("Custom projections disabled - using OALFFL rankings only")
        
        # Run simulations using web app's projection system
        try:
            recommendations = run_simulations_with_web_projections(assistant, num_recommendations)
            assistant.cached_recommendations = recommendations
            simulation_status = 'Completed'
        except Exception as sim_error:
            print(f"Error running simulation: {sim_error}")
            assistant.cached_recommendations = []
            simulation_status = f'Error: {str(sim_error)}'
        
        return jsonify({
            'success': True,
            'simulation_status': simulation_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def run_simulations_with_web_projections(assistant, num_recommendations=40):
    """Run simulations using web app's projection system."""
    try:
        if not assistant or not assistant.draft_initialized or assistant.user_draft_position == 0:
            print("Draft not initialized or assistant is None or user position not set")
            return []
        
        current_pick_info = assistant.get_current_pick_info()
        if not current_pick_info or not current_pick_info.get("is_user_turn", False):
            print("Not user's turn")
            return []
        
        recommendations = []
        
        # Pre-calculate all projections to avoid repeated calls
        available_players = assistant.get_available_players()
        if not available_players:
            print("No available players")
            return []
            
        projection_cache = {}
        players_with_projections = []
        
        print("Pre-calculating projections for all available players...")
        print("Using OALFFL rankings projections (custom projections disabled)")
        
        for player in available_players:
            # This will use custom projections from Supabase if available
            projected_points = get_player_projection(player.name, selected_scoring_format)
            projection_cache[player.name] = projected_points
            players_with_projections.append({
                'player': player,
                'projected_points': projected_points
            })
        
        # Sort by web app's projection system (including custom projections)
        sorted_players_with_projections = sorted(players_with_projections, key=lambda x: x['projected_points'], reverse=True)
        sorted_players = [item['player'] for item in sorted_players_with_projections]
        
        # Get top 1 player at each position (by web app's projections) - UPDATED to use current available players
        top_players_by_position = {}
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            # Handle DST position
            if position == 'DST':
                position_players = [p for p in sorted_players if p.position == 'DST']
            else:
                position_players = [p for p in sorted_players if p.position == position]
            if position_players:
                top_players_by_position[position] = position_players[0]  # Only the #1 player
                web_projection = projection_cache.get(position_players[0].name, position_players[0].projected_points)
                print(f"Top {position}: {position_players[0].name} ({web_projection} pts)")
        
        # Pre-calculate roster needs once
        current_team = assistant._get_current_team()
        if not current_team:
            print("Could not get current team")
            return []
            
        current_roster = assistant.drafted_players.get(current_team, [])
        roster_needs = get_roster_needs_for_simulation_web_projections(assistant, current_roster, projection_cache)
        
        # Run simulations only for the top player at each position
        player_scores = {}
        
        print(f"Running simulations for top 1 player at each position using web app projections...")
        
        for position, top_player in top_players_by_position.items():
            scores = []
            successful_sims = 0
            
            # Run 40 simulations for the top player at this position (increased for better accuracy)
            for sim in range(40):
                try:
                    score = simulate_draft_with_player_web_projections(assistant, top_player, projection_cache)
                    scores.append(score)
                    successful_sims += 1
                except Exception as e:
                    print(f"Simulation {sim + 1} failed for {top_player.name}: {e}")
                    continue
            
            if successful_sims > 0:
                avg_score = sum(scores) / len(scores)
                player_scores[top_player] = avg_score
                print(f"{top_player.name} ({position}): {successful_sims} simulations, avg score: {avg_score:.1f}")
            else:
                print(f"All simulations failed for {top_player.name}")
        
        # Now calculate values for 4 other players at each position based on projected points difference
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if position not in top_players_by_position:
                continue
                
            top_player = top_players_by_position[position]
            top_player_score = player_scores.get(top_player, 0)
            top_player_projected = projection_cache[top_player.name]
            
            # Get next 4 players at this position
            if position == 'DST':
                position_players = [p for p in sorted_players if p.position == 'DST']
            else:
                position_players = [p for p in sorted_players if p.position == position]
            other_players = position_players[1:5]  # Skip the top player, take next 4
            
            for other_player in other_players:
                other_projected = projection_cache[other_player.name]
                projected_diff = top_player_projected - other_projected
                
                # Calculate value: top_player_value - projected_points_difference
                calculated_value = top_player_score - projected_diff
                player_scores[other_player] = calculated_value
                
                print(f"{other_player.name} ({position}): calculated value: {calculated_value:.1f} (based on {top_player.name})")
        
        # Apply bench value adjustments to prioritize backup RBs/WRs over kickers
        adjusted_scores = {}
        for player, score in player_scores.items():
            # Check if this player would be a starter or bench player
            would_be_starter = False
            if player.position in roster_needs and roster_needs[player.position] > 0:
                would_be_starter = True
            elif player.position in ['RB', 'WR', 'TE'] and roster_needs.get('FLEX', 0) > 0:
                would_be_starter = True
            
            # Apply bench value bonus for backup RBs/WRs/TEs over kickers
            if not would_be_starter and player.position in ['RB', 'WR', 'TE']:
                # This player would be a bench player - add bench value bonus
                bench_bonus = calculate_bench_value_for_player_web_projections(player, current_roster, projection_cache)
                adjusted_score = score + bench_bonus
                print(f"{player.name} ({player.position}): bench bonus {bench_bonus:.1f}, adjusted score: {adjusted_score:.1f}")
            elif player.position == 'K' and not would_be_starter:
                # Kickers on bench have 0 value - heavily penalize
                adjusted_score = score - 1000  # Large penalty for backup K
                print(f"{player.name} ({player.position}): backup penalty, adjusted score: {adjusted_score:.1f}")
            elif player.position == 'DST' and not would_be_starter:
                # DST on bench - no penalty for now to test
                adjusted_score = score  # No penalty for backup DST
                print(f"{player.name} ({player.position}): no penalty, adjusted score: {adjusted_score:.1f}")
            else:
                adjusted_score = score
            
            adjusted_scores[player] = adjusted_score
        
        # Sort by adjusted value (highest first)
        sorted_players = sorted(adjusted_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Convert to recommendations format
        recommendations = []
        for player, score in sorted_players[:num_recommendations]:
            recommendations.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'adp': player.adp,
                'projected_points': projection_cache[player.name],
                'expected_season_score': score,
                'is_customized': False  # Custom projections disabled
            })
        
        return recommendations
        
    except Exception as e:
        print(f"Error in run_simulations_with_web_projections: {e}")
        import traceback
        traceback.print_exc()
        return []

def simulate_draft_with_player_web_projections(assistant, candidate_player, projection_cache=None):
    """Simulate draft with player using web app's projection system."""
    # Save current state
    original_drafted_players = {team: roster.copy() for team, roster in assistant.drafted_players.items()}
    original_available_players = set(assistant.available_players)
    original_pick = assistant.current_pick
    
    # Setup sim state
    sim_drafted_players = {team: roster.copy() for team, roster in assistant.drafted_players.items()}
    sim_available_players = set(assistant.available_players)
    sim_pick = assistant.current_pick
    
    try:
        # Draft the candidate player
        team_name = assistant.teams[assistant.user_draft_position - 1]
        sim_drafted_players[team_name].append(candidate_player)
        sim_available_players.remove(candidate_player)
        sim_pick += 1
        
        # Simulate the rest of the draft using ADP
        while sim_pick <= assistant.total_picks:
            # Determine which team is picking using snake draft logic
            if sim_pick <= len(assistant.draft_order):
                round_num, team_id = assistant.draft_order[sim_pick - 1]
                team_name = assistant.teams[team_id - 1]
            else:
                # Fallback for picks beyond draft order
                team_index = (sim_pick - 1) % assistant.num_teams
                team_name = assistant.teams[team_index]
            
            # Check if team has roster space
            team_roster = sim_drafted_players[team_name]
            total_roster_size = sum(assistant.roster_constraints.values())
            
            if len(team_roster) >= total_roster_size:
                # Team is full, skip this pick
                sim_pick += 1
                continue
            
            # If it's the user's turn, use smart strategy
            if sim_pick <= len(assistant.draft_order):
                round_num, team_id = assistant.draft_order[sim_pick - 1]
                is_user_turn = (team_id == assistant.user_draft_position)
            else:
                # Fallback for picks beyond draft order
                team_index = (sim_pick - 1) % assistant.num_teams
                is_user_turn = (team_index == assistant.user_draft_position - 1)
            
            if is_user_turn:
                # Get roster needs for user team
                roster_needs = get_roster_needs_for_simulation_web_projections(assistant, team_roster, projection_cache)
                
                # Find best available player considering roster needs and bench constraints
                best_player = None
                best_score = -1
                
                for player in sorted(sim_available_players, key=lambda p: p.adp):
                    # Check if this player fills a need
                    need_bonus = 0
                    position_need = roster_needs.get(player.position, 0)
                    
                    if position_need > 0:
                        # High bonus for filling a starting position need
                        need_bonus = 100
                    elif roster_needs.get('BN', 0) > 0:
                        # Check if this player would be a valuable bench player
                        if player.position in ['RB', 'WR', 'TE']:
                            # Calculate bench value for this player
                            bench_value = calculate_bench_value_for_player_web_projections(player, team_roster, projection_cache)
                            need_bonus = bench_value  # Use actual bench value
                        elif player.position in ['K', 'DST']:
                            # Kickers/DST on bench have 0 value - skip them
                            continue
                        else:
                            # QB on bench - moderate value
                            need_bonus = 20
                    else:
                        # No roster space available
                        continue
                    
                    # Calculate player value using cached projection
                    player_projected = projection_cache.get(player.name, get_player_projection(player.name, selected_scoring_format))
                    player_value = (200 - player.adp) + need_bonus + random.randint(-10, 10)
                    
                    if player_value > best_score:
                        best_score = player_value
                        best_player = player
                
                if best_player:
                    sim_drafted_players[team_name].append(best_player)
                    sim_available_players.remove(best_player)
                else:
                    # No suitable player found, skip this pick
                    pass
            else:
                # Other teams use ADP with some variance
                available_sorted = sorted(sim_available_players, key=lambda p: p.adp)
                if available_sorted:
                    # 70% chance to follow ADP closely, 30% chance for variance
                    if random.random() < 0.7:
                        pick_index = 0
                    else:
                        pick_index = min(random.randint(0, 5), len(available_sorted) - 1)
                    
                    picked_player = available_sorted[pick_index]
                    sim_drafted_players[team_name].append(picked_player)
                    sim_available_players.remove(picked_player)
            
            sim_pick += 1
        
        # Calculate season score for user team using web app's projection system
        user_roster = sim_drafted_players[assistant.teams[assistant.user_draft_position - 1]]
        season_score = calculate_roster_value_for_simulation_web_projections(assistant, user_roster, projection_cache)
        
        return season_score
        
    except Exception as e:
        print(f"Error in simulation for {candidate_player.name}: {e}")
        return 0.0
    finally:
        # Restore original state
        assistant.drafted_players = original_drafted_players
        assistant.available_players = list(original_available_players)
        assistant.current_pick = original_pick

def calculate_roster_value_for_simulation_web_projections(assistant, roster, projection_cache=None):
    """Calculate roster value for simulation using web app's projection system."""
    if not roster:
        return 0.0
    
    # First, properly separate starters from bench players based on roster constraints
    starters = []
    bench = []
    
    # Sort players by projected points to prioritize best players as starters
    players_with_projections = []
    for player in roster:
        projected_points = projection_cache.get(player.name, get_player_projection(player.name, selected_scoring_format))
        players_with_projections.append({
            'player': player,
            'projected_points': projected_points
        })
    
    sorted_players_with_projections = sorted(players_with_projections, key=lambda x: x['projected_points'], reverse=True)
    sorted_players = [item['player'] for item in sorted_players_with_projections]
    
    # Track filled positions
    filled_positions = {
        'QB': 0,
        'RB': 0,
        'WR': 0,
        'TE': 0,
        'FLEX': 0,
        'K': 0,
        'DST': 0
    }
    
    # Assign starters first based on roster constraints
    for player in sorted_players:
        pos = player.position
        
        # Check if we can fill a starting position
        if pos in ['QB', 'K', 'DST']:
            if filled_positions[pos] < assistant.roster_constraints.get(pos, 0):
                starters.append(player)
                filled_positions[pos] += 1
            else:
                bench.append(player)
        elif pos in ['RB', 'WR', 'TE']:
            # First try to fill position-specific slots
            if filled_positions[pos] < assistant.roster_constraints.get(pos, 0):
                starters.append(player)
                filled_positions[pos] += 1
            elif filled_positions['FLEX'] < assistant.roster_constraints.get('FLEX', 0):
                # Fill FLEX position
                starters.append(player)
                filled_positions['FLEX'] += 1
            else:
                # Player goes to bench
                bench.append(player)
    
    # Calculate value: starters get full value, bench gets reduced value
    total_value = 0.0
    
    # Starters get full projected points (except K and DST get 40%)
    for player in starters:
        projected_points = projection_cache.get(player.name, get_player_projection(player.name, selected_scoring_format))
        if player.position in ['K', 'DST']:
            total_value += projected_points * 0.40  # 40% starting value for K and DST
        else:
            total_value += projected_points  # Full value for other positions
    
    # Bench players get reduced value based on depth
    bench_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
    for player in bench:
        bench_value = calculate_bench_value_for_player_web_projections(player, bench, projection_cache)
        total_value += bench_value
        bench_counts[player.position] += 1
    
    return total_value

def get_roster_needs_for_simulation_web_projections(assistant, roster, projection_cache=None):
    """Get roster needs for simulation purposes using web app's projection system."""
    # Count current players by position
    position_counts = {'QB': 0, 'WR': 0, 'RB': 0, 'TE': 0, 'K': 0, 'DST': 0}
    for player in roster:
        if player.position in position_counts:
            position_counts[player.position] += 1
    
    # Calculate how many players are actually starters vs bench
    # First, determine which players fill starting positions
    starters = []
    bench_players = []
    
    # Track filled positions to determine who goes to bench
    filled_positions = {
        'QB': 0,
        'WR': 0, 
        'RB': 0,
        'TE': 0,
        'FLEX': 0,
        'K': 0,
        'DST': 0
    }
    
    # Sort players by web app's projected points to prioritize starters
    players_with_projections = []
    for player in roster:
        projected_points = projection_cache.get(player.name, get_player_projection(player.name, selected_scoring_format))
        players_with_projections.append({
            'player': player,
            'projected_points': projected_points
        })
    
    sorted_players_with_projections = sorted(players_with_projections, key=lambda x: x['projected_points'], reverse=True)
    sorted_roster = [item['player'] for item in sorted_players_with_projections]
    
    for player in sorted_roster:
        pos = player.position
        
        # Check if we can fill a starting position
        if pos in filled_positions and filled_positions[pos] < assistant.roster_constraints.get(pos, 0):
            # Fill starting position
            filled_positions[pos] += 1
            starters.append(player)
        elif pos in ['RB', 'WR', 'TE'] and filled_positions['FLEX'] < assistant.roster_constraints.get('FLEX', 0):
            # Fill FLEX position
            filled_positions['FLEX'] += 1
            starters.append(player)
        else:
            # Player goes to bench
            bench_players.append(player)
    
    # Calculate total bench spots used (only actual bench players)
    total_bench_used = len(bench_players)
    
    max_bench = assistant.roster_constraints.get('BN', 6)
    bench_available = max(0, max_bench - total_bench_used)
    
    # Calculate needs for starting positions
    needs = {
        'QB': max(0, assistant.roster_constraints.get('QB', 1) - position_counts['QB']),
        'WR': max(0, assistant.roster_constraints.get('WR', 2) - position_counts['WR']),
        'RB': max(0, assistant.roster_constraints.get('RB', 2) - position_counts['RB']),
        'TE': max(0, assistant.roster_constraints.get('TE', 1) - position_counts['TE']),
        'K': max(0, assistant.roster_constraints.get('K', 1) - position_counts['K']),
        'DST': max(0, assistant.roster_constraints.get('DST', 1) - position_counts['DST'])
    }
    
    # If bench is full, prioritize filling remaining roster slots
    if bench_available == 0:
        # Only allow drafting players that fill remaining roster slots
        return {pos: count for pos, count in needs.items() if count > 0}
    
    # If bench has space, allow drafting any position
    # Add bench availability to the needs calculation
    needs['BN'] = bench_available
    
    return needs

def calculate_bench_value_for_player_web_projections(player, team_roster, projection_cache=None):
    """Calculate bench value for a player using web app's projection system."""
    if not team_roster:
        return 0.0
    
    # Get player's projected points using cached value or web app's system
    player_projected = projection_cache.get(player.name, get_player_projection(player.name, selected_scoring_format))
    
    # Count current bench players by position (excluding current player)
    bench_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
    for p in team_roster:
        if p.position in bench_counts and p.name != player.name:
            bench_counts[p.position] += 1
    
    # Get bench depth for the player's position
    bench_depth = bench_counts.get(player.position, 0)
    
    if player.position == 'QB':
        if bench_depth == 0:
            return player_projected * 0.35  # 35% for 1st bench QB
        else:
            return 0.0  # All following QBs worth 0%
    elif player.position == 'RB':
        if bench_depth == 0:
            return player_projected * 0.22  # 22% for 1st bench RB
        elif bench_depth == 1:
            return player_projected * 0.14  # 14% for 2nd bench RB
        elif bench_depth == 2:
            return player_projected * 0.12  # 12% for 3rd bench RB
        elif bench_depth == 3:
            return player_projected * 0.05  # 5% for 4th bench RB
        else:
            return player_projected * 0.05  # 5% for 5th+ bench RB
    elif player.position == 'WR':
        if bench_depth == 0:
            return player_projected * 0.22  # 22% for 1st bench WR
        elif bench_depth == 1:
            return player_projected * 0.14  # 14% for 2nd bench WR
        elif bench_depth == 2:
            return player_projected * 0.12  # 12% for 3rd bench WR
        elif bench_depth == 3:
            return player_projected * 0.05  # 5% for 4th bench WR
        else:
            return player_projected * 0.05  # 5% for 5th+ bench WR
    elif player.position == 'TE':
        return 0.0  # All TEs have 0% bench value
    elif player.position == 'K':
        return 0.0  # Kickers have 0% bench value
    elif player.position == 'DST':
        return 0.0  # Defense has 0% bench value
    else:
        return 0.0


@app.route('/api/roster_needs')
def get_roster_needs():
    """Get roster needs for a team."""
    try:
        assistant = get_draft_assistant()
        team_name = request.args.get('team')
        
        if not team_name:
            team_name = assistant.teams[assistant.user_draft_position - 1]
        
        needs = assistant.get_roster_needs(team_name)
        
        return jsonify({
            'success': True,
            'team': team_name,
            'needs': needs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/user_roster')
def get_user_roster():
    """Get the user's roster with proper flex and bench assignments using web app's projection system."""
    try:
        assistant = get_draft_assistant()
        team_name = assistant.teams[assistant.user_draft_position - 1]
        roster = assistant.drafted_players[team_name]
        
        # Initialize roster slots
        roster_display = {
            'QB': [],
            'WR': [],
            'RB': [],
            'TE': [],
            'FLEX': [],
            'K': [],
            'DST': [],
            'BN': []
        }
        
        # Sort players by web app's projected points for optimal assignment
        players_with_projections = []
        for player in roster:
            projected_points = get_player_projection(player.name, selected_scoring_format)
            players_with_projections.append({
                'player': player,
                'projected_points': projected_points
            })
        
        sorted_players_with_projections = sorted(players_with_projections, key=lambda x: x['projected_points'], reverse=True)
        sorted_players = [item['player'] for item in sorted_players_with_projections]
        assigned_players = set()  # Track which players have been assigned
        
        # First, fill required positions
        for player_data in sorted_players_with_projections:
            player = player_data['player']
            projected_points = player_data['projected_points']
            
            if player.name in assigned_players:
                continue
                
            if player.position == 'QB' and len(roster_display['QB']) < assistant.roster_constraints['QB']:
                roster_display['QB'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
            elif player.position == 'K' and len(roster_display['K']) < assistant.roster_constraints['K']:
                roster_display['K'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
            elif player.position == 'DST' and len(roster_display['DST']) < assistant.roster_constraints['DST']:
                roster_display['DST'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
        
        # Then fill WR, RB, TE positions
        for player_data in sorted_players_with_projections:
            player = player_data['player']
            projected_points = player_data['projected_points']
            
            if player.name in assigned_players:
                continue
                
            if player.position == 'WR' and len(roster_display['WR']) < assistant.roster_constraints['WR']:
                roster_display['WR'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
            elif player.position == 'RB' and len(roster_display['RB']) < assistant.roster_constraints['RB']:
                roster_display['RB'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
            elif player.position == 'TE' and len(roster_display['TE']) < assistant.roster_constraints['TE']:
                roster_display['TE'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
        
        # Fill FLEX position with best remaining RB/WR/TE
        for player_data in sorted_players_with_projections:
            player = player_data['player']
            projected_points = player_data['projected_points']
            
            if player.name in assigned_players:
                continue
                
            if player.position in ['RB', 'WR', 'TE'] and len(roster_display['FLEX']) < assistant.roster_constraints['FLEX']:
                roster_display['FLEX'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
                break
        
        # Put remaining players on bench
        for player_data in sorted_players_with_projections:
            player = player_data['player']
            projected_points = player_data['projected_points']
            
            if player.name in assigned_players:
                continue
                
            if len(roster_display['BN']) < assistant.roster_constraints['BN']:
                roster_display['BN'].append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'projected_points': projected_points,
                    'bye_week': player.bye_week,
                    'is_customized': False  # Custom projections disabled
                })
                assigned_players.add(player.name)
        
        return jsonify({
            'success': True,
            'team': team_name,
            'roster': roster_display,
            'constraints': assistant.roster_constraints,
            'scoring_format': selected_scoring_format
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/user/roster')
@login_required
def get_user_roster_detailed():
    """Get user's roster with starter/bench separation and projections."""
    try:
        assistant = get_draft_assistant()
        user_team_name = assistant.teams[assistant.user_draft_position - 1]
        roster = assistant.drafted_players[user_team_name]
        
        if not roster:
            return jsonify({
                'success': True,
                'roster': {
                    'starters': [],
                    'bench': [],
                    'starters_week1_projection': 0,
                    'starters_season_projection': 0,
                    'bench_week1_projection': 0,
                    'bench_season_projection': 0,
                    'total_week1_projection': 0,
                    'total_season_projection': 0
                }
            })
        
        # Properly separate starters and bench based on roster constraints
        starters = []
        bench = []
        
        # Sort players by projected points to prioritize best players as starters
        players_with_projections = []
        for player in roster:
            projected_points = get_player_projection(player.name, selected_scoring_format)
            players_with_projections.append({
                'player': player,
                'projected_points': projected_points
            })
        
        sorted_players_with_projections = sorted(players_with_projections, key=lambda x: x['projected_points'], reverse=True)
        sorted_players = [item['player'] for item in sorted_players_with_projections]
        
        # Track filled positions
        filled_positions = {
            'QB': 0,
            'RB': 0,
            'WR': 0,
            'TE': 0,
            'FLEX': 0,
            'K': 0,
            'DST': 0
        }
        
        # Assign starters first based on roster constraints
        for player in sorted_players:
            pos = player.position
            
            # Check if we can fill a starting position
            if pos in ['QB', 'K', 'DST']:
                if filled_positions[pos] < assistant.roster_constraints.get(pos, 0):
                    starters.append(player)
                    filled_positions[pos] += 1
                else:
                    bench.append(player)
            elif pos in ['RB', 'WR', 'TE']:
                # First try to fill position-specific slots
                if filled_positions[pos] < assistant.roster_constraints.get(pos, 0):
                    starters.append(player)
                    filled_positions[pos] += 1
                elif filled_positions['FLEX'] < assistant.roster_constraints.get('FLEX', 0):
                    # Fill FLEX position
                    starters.append(player)
                    filled_positions['FLEX'] += 1
                else:
                    # Player goes to bench
                    bench.append(player)
        
        # Convert players to serializable format with projections
        def player_to_dict(player_data):
            player = player_data['player']
            projected_points = player_data['projected_points']
            week1_projection = projected_points / 17  # Divide season by 17 weeks
            
            # Check if player has custom projections
            is_customized = False
            if player.name in custom_projections_cache:
                is_customized = True
            
            return {
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'season_projection': round(projected_points, 1),
                'week1_projection': round(week1_projection, 1),
                'bye_week': player.bye_week,
                'is_customized': is_customized
            }
        
        starters_data = []
        for player in starters:
            projected_points = get_player_projection(player.name, selected_scoring_format)
            starters_data.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'season_projection': round(projected_points, 1),
                'week1_projection': round(projected_points / 17, 1),
                'bye_week': player.bye_week,
                'is_customized': False  # Custom projections disabled
            })
        
        bench_data = []
        for player in bench:
            projected_points = get_player_projection(player.name, selected_scoring_format)
            # Calculate bench value using the bench calculation function
            bench_value = calculate_bench_value_for_player_web_projections(player, bench)
            bench_data.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'season_projection': round(bench_value, 1),  # Use bench value, not full projection
                'week1_projection': round(bench_value / 17, 1),
                'bye_week': player.bye_week,
                'is_customized': False  # Custom projections disabled
            })
        
        # Calculate projections using web app's projection system
        starters_season = sum(get_player_projection(p.name, selected_scoring_format) for p in starters)
        starters_week1 = starters_season / 17
        bench_season = sum(calculate_bench_value_for_player_web_projections(p, bench) for p in bench)
        bench_week1 = bench_season / 17
        
        return jsonify({
            'success': True,
            'roster': {
                'starters': starters_data,
                'bench': bench_data,
                'starters_week1_projection': round(starters_week1, 1),
                'starters_season_projection': round(starters_season, 1),
                'bench_week1_projection': round(bench_week1, 1),
                'bench_season_projection': round(bench_season, 1),
                'total_week1_projection': round(starters_week1 + bench_week1, 1),
                'total_season_projection': round(starters_season + bench_season, 1)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export_results')
def export_results():
    """Export draft results."""
    try:
        assistant = get_draft_assistant()
        results = assistant.export_draft_results()
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/end_draft', methods=['POST'])
def end_draft():
    """End the current draft and allow league settings to be modified."""
    try:
        assistant = get_draft_assistant()
        
        # Mark draft as not initialized
        assistant.draft_initialized = False
        
        # Clear all drafted players
        assistant.drafted_players = {f'Team {i+1}': [] for i in range(assistant.num_teams)}
        
        # Reset draft state
        assistant.current_round = 1
        assistant.current_pick = 1
        assistant.draft_history = []
        
        # Reset available players to all players
        assistant.available_players = set(assistant.players)
        
        # Clear cached recommendations
        assistant._cached_recommendations = []
        
        return jsonify({
            'success': True,
            'message': 'Draft ended and reset. You can now modify league settings and start a new draft.',
            'status': assistant.get_draft_status()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reset_draft', methods=['POST'])
def reset_draft():
    """Reset the draft to the beginning."""
    try:
        assistant = get_draft_assistant()
        
        # Check if draft is initialized and user position is set
        if not assistant.draft_initialized or assistant.user_draft_position == 0:
            return jsonify({
                'success': False,
                'error': 'Draft must be initialized before it can be reset'
            })
        
        assistant.reset_draft()
        
        return jsonify({
            'success': True,
            'message': 'Draft reset successfully',
            'status': assistant.get_draft_status()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/set_user_position', methods=['POST'])
def set_user_position():
    """Set the user's draft position."""
    try:
        assistant = get_draft_assistant()
        data = request.get_json()
        user_position = data.get('user_position')
        
        if not user_position or user_position < 1 or user_position > assistant.num_teams:
            return jsonify({
                'success': False,
                'error': f'Invalid user position. Must be between 1 and {assistant.num_teams}'
            })
        
        # Set the user draft position
        assistant.set_user_draft_position(user_position)
        
        return jsonify({
            'success': True,
            'message': f'User draft position set to {user_position}',
            'user_draft_position': assistant.user_draft_position,
            'status': assistant.get_draft_status()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/league_settings')
def get_league_settings():
    """Get current league settings."""
    try:
        assistant = get_draft_assistant()
        
        return jsonify({
            'success': True,
            'settings': {
                'num_teams': assistant.num_teams,
                'user_draft_position': assistant.user_draft_position,
                'roster_constraints': assistant.roster_constraints,
                'scoring_format': selected_scoring_format
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/draft_history')
def get_draft_history():
    """Get recent draft picks."""
    try:
        assistant = get_draft_assistant()
        
        # Get the last 10 picks
        recent_picks = assistant.draft_history[-10:] if assistant.draft_history else []
        
        history_list = []
        for pick in recent_picks:
            history_list.append({
                'round': pick['round'],
                'pick': pick['pick'],
                'team_name': pick['team_name'],
                'player_name': pick['player'].name,
                'player_position': pick['player'].position,
                'player_team': pick['player'].team
            })
        
        return jsonify({
            'success': True,
            'history': history_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/simulation_status')
def get_simulation_status():
    """Get simulation status."""
    try:
        assistant = get_draft_assistant()
        
        # Check if draft is initialized first
        if not assistant or not assistant.draft_initialized or assistant.user_draft_position == 0:
            return jsonify({
                'success': True,
                'is_running': False,
                'is_user_turn': False,
                'draft_initialized': False,
                'status': 'Draft not initialized'
            })
        
        pick_info = assistant.get_current_pick_info()
        
        # Only run simulation if it's user's turn
        is_running = pick_info.get("is_user_turn", False)
        
        return jsonify({
            'success': True,
            'is_running': is_running,
            'is_user_turn': pick_info.get("is_user_turn", False),
            'draft_initialized': True,
            'status': pick_info.get("status", "Unknown")
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/user_roster_value')
def get_user_roster_value():
    """Get the user's current roster value using web app's projection system."""
    try:
        assistant = get_draft_assistant()
        
        if not assistant.draft_initialized or assistant.user_draft_position == 0:
            return jsonify({
                'success': True,
                'value': 0.0,
                'message': 'Draft not started'
            })
        
        # Calculate roster value using the same method as simulation
        team_name = assistant.teams[assistant.user_draft_position - 1]
        roster = assistant.drafted_players[team_name]
        
        if not roster:
            return jsonify({
                'success': True,
                'value': 0.0,
                'message': 'No players drafted yet'
            })
        
        # Use the same calculation as the simulation
        total_value = calculate_roster_value_for_simulation_web_projections(assistant, roster)
        
        return jsonify({
            'success': True,
            'value': round(total_value, 2),
            'message': f'Current roster value: {round(total_value, 2)} points ({selected_scoring_format})'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/draft_complete')
def get_draft_complete_status():
    """Check if the draft is complete based on roster configuration."""
    try:
        assistant = get_draft_assistant()
        
        if not assistant.draft_initialized or assistant.user_draft_position == 0:
            return jsonify({
                'success': True,
                'is_complete': False,
                'message': 'Draft not started'
            })
        
        # Calculate total picks based on roster constraints
        total_roster_spots = sum(assistant.roster_constraints.values())
        total_picks_needed = total_roster_spots * assistant.num_teams
        current_pick = assistant.current_pick
        
        is_complete = current_pick > total_picks_needed
        
        return jsonify({
            'success': True,
            'is_complete': is_complete,
            'current_pick': current_pick,
            'total_picks': total_picks_needed,
            'total_roster_spots': total_roster_spots,
            'num_teams': assistant.num_teams,
            'message': 'Draft complete! 🎉' if is_complete else f'Pick {current_pick} of {total_picks_needed}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/load_players_with_custom_projections')
def load_players_with_custom_projections():
    """Load players with custom projections and raw stats for customization."""
    # Custom projections disabled
    try:
        assistant = get_draft_assistant()
        players_data = []
        
        # Get position filter from query parameter
        position_filter = request.args.get('position', '').upper()
        
        # Handle position mapping (frontend uses DEF, system uses DST)
        if position_filter == 'DEF':
            position_filter = 'DST'
        
        # Load custom projections from Supabase for current user
        user_id = session.get('user_id', 'anonymous')
        supabase_projections = supabase_manager.get_custom_projections(user_id)
        
        # Get all available players
        all_players = assistant.get_available_players()
        
        # Filter by position if specified
        if position_filter:
            if position_filter == 'DST':
                # For DST filter, include both DEF and DST positions
                filtered_players = [p for p in all_players if p.position in ['DEF', 'DST']]
            else:
                filtered_players = [p for p in all_players if p.position == position_filter]
        else:
            filtered_players = all_players
        
        for player in filtered_players:
            is_customized = False
            custom_projected_points = None
            
            # Get raw stats for customization
            raw_stats = assistant.get_player_raw_stats(player.name)
            
            # For DST/DEF players, ensure we have the proper stats format
            if player.position in ['DST', 'DEF']:
                # Get DST stats from the cache if available
                if player.name in player_projections_cache:
                    cached_data = player_projections_cache[player.name]
                    if 'stats' in cached_data:
                        raw_stats = cached_data['stats']
                    else:
                        # Create default DST stats structure
                        raw_stats = {
                            'position': player.position,
                            'sacks': 0.0,
                            'interceptions': 0.0,
                            'fumble_recoveries': 0.0,
                            'forced_fumbles': 0.0,
                            'defensive_tds': 0.0,
                            'safeties': 0.0,
                            'points_allowed': 0.0,
                            'yards_allowed': 0.0,
                            'season_points': player.projected_points,
                            'projected_points': player.projected_points
                        }
                elif not raw_stats:
                    # Create default DST stats structure if no cache and no raw_stats
                    raw_stats = {
                        'position': player.position,
                        'sacks': 0.0,
                        'interceptions': 0.0,
                        'fumble_recoveries': 0.0,
                        'forced_fumbles': 0.0,
                        'defensive_tds': 0.0,
                        'safeties': 0.0,
                        'points_allowed': 0.0,
                        'yards_allowed': 0.0,
                        'season_points': player.projected_points,
                        'projected_points': player.projected_points
                    }
                
                # Always ensure season_points and position are present
                if raw_stats:
                    raw_stats['season_points'] = player.projected_points
                    raw_stats['position'] = player.position
            
            # For K players, ensure we have the proper stats format
            if player.position == 'K' and not raw_stats:
                # Get K stats from the cache if available
                if player.name in player_projections_cache:
                    cached_data = player_projections_cache[player.name]
                    if 'stats' in cached_data:
                        raw_stats = cached_data['stats']
                    else:
                        # Create default K stats structure
                        raw_stats = {
                            'position': 'K',
                            'field_goals': 0.0,
                            'extra_points': 0.0,
                            'projected_points': player.projected_points
                        }
            
            # Check for custom projections
            if player.name in custom_projections_cache:
                custom_data = custom_projections_cache[player.name]
                is_customized = True
                
                if 'projections' in custom_data:
                    # New format with projections for all scoring formats
                    ppr_points = custom_data['projections'].get('ppr', 0.0)
                    half_ppr_points = custom_data['projections'].get('half-ppr', 0.0)
                    non_ppr_points = custom_data['projections'].get('non-ppr', 0.0)
                    custom_projected_points = ppr_points
                else:
                    # Calculate from custom stats
                    custom_stats = custom_data.get('stats', {})
                    if player.position in ['DST', 'DEF']:
                        # For DST players, use season_points directly
                        season_points = custom_stats.get('season_points', 0.0)
                        ppr_points = season_points
                        half_ppr_points = season_points
                        non_ppr_points = season_points
                        custom_projected_points = season_points
                    else:
                        # For other positions, calculate from stats
                        ppr_points = calculate_projection_from_stats(custom_stats, 'ppr')
                        half_ppr_points = calculate_projection_from_stats(custom_stats, 'half-ppr')
                        non_ppr_points = calculate_projection_from_stats(custom_stats, 'non-ppr')
                        custom_projected_points = ppr_points
                
                # Update raw_stats with custom stats for display
                raw_stats = custom_data.get('stats', raw_stats)
            elif player.name in supabase_projections:
                # Use Supabase data
                custom_data = supabase_projections[player.name]
                is_customized = True
                ppr_points = custom_data['projections'].get('ppr', 0.0)
                half_ppr_points = custom_data['projections'].get('half-ppr', 0.0)
                non_ppr_points = custom_data['projections'].get('non-ppr', 0.0)
                custom_projected_points = ppr_points
                
                # Update local cache
                custom_projections_cache[player.name] = custom_data
            else:
                # Use default projections
                ppr_points = assistant.calculate_projected_points_from_raw_stats(player.name, 'ppr')
                half_ppr_points = assistant.calculate_projected_points_from_raw_stats(player.name, 'half-ppr')
                non_ppr_points = assistant.calculate_projected_points_from_raw_stats(player.name, 'standard')
                
                # Ensure we have valid numbers
                ppr_points = round(ppr_points, 1) if ppr_points is not None else 0.0
                half_ppr_points = round(half_ppr_points, 1) if half_ppr_points is not None else 0.0
                non_ppr_points = round(non_ppr_points, 1) if non_ppr_points is not None else 0.0
            
            player_data = {
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'adp': player.adp,
                'bye_week': player.bye_week,
                'projected_points': ppr_points,
                'custom_projected_points': round(custom_projected_points, 1) if custom_projected_points is not None else None,
                'ppr_points': ppr_points,
                'half_ppr_points': half_ppr_points,
                'non_ppr_points': non_ppr_points,
                'raw_stats': raw_stats,
                'is_customized': is_customized
            }
            players_data.append(player_data)
        
        # Sort by ADP
        players_data.sort(key=lambda x: x['adp'] if x['adp'] != 999.0 else float('inf'))
        
        return jsonify(players_data)
    except Exception as e:
        print(f"Error loading players: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_custom_projection', methods=['POST'])
def save_custom_projection():
    """Save a custom projection for a player."""
    try:
        data = request.get_json()
        print(f"Received data for custom projection: {data}")  # Debug log
        
        player_name = data.get('player_name')
        position = data.get('position')
        custom_stats = data.get('custom_stats', {})
        
        print(f"Extracted: player_name='{player_name}', position='{position}', custom_stats={custom_stats}")  # Debug log
        
        if not player_name or not position:
            print(f"Missing required fields: player_name='{player_name}', position='{position}'")  # Debug log
            return jsonify({'success': False, 'error': 'Player name and position required'}), 400
        
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        print(f"Saving custom projection for user {user_id}, player {player_name}")  # Debug log
        
        # Calculate projections for all scoring formats
        projections = {
            'non-ppr': calculate_projection_from_stats(custom_stats, 'non-ppr'),
            'ppr': calculate_projection_from_stats(custom_stats, 'ppr'),
            'half-ppr': calculate_projection_from_stats(custom_stats, 'half-ppr')
        }
        
        print(f"Calculated projections: {projections}")  # Debug log
        
        # Save to Supabase if available
        if supabase:
            try:
                # Prepare data for Supabase
                supabase_data = {
                    'user_id': user_id,
                    'player_name': player_name,
                    'position': position,
                    'custom_stats': custom_stats,
                    'ppr_projection': projections['ppr'],
                    'half_ppr_projection': projections['half-ppr'],
                    'non_ppr_projection': projections['non-ppr'],
                    'updated_at': datetime.now().isoformat()
                }
                
                # Check if projection already exists
                existing = supabase.table('user_custom_projections').select('*').eq('user_id', user_id).eq('player_name', player_name).execute()
                
                if existing.data:
                    # Update existing record
                    supabase.table('user_custom_projections').update(supabase_data).eq('user_id', user_id).eq('player_name', player_name).execute()
                    print(f"Updated custom projection for {player_name} in Supabase")
                else:
                    # Insert new record
                    supabase_data['created_at'] = datetime.now().isoformat()
                    supabase.table('user_custom_projections').insert(supabase_data).execute()
                    print(f"Saved custom projection for {player_name} to Supabase")
                
                # Update local cache
                custom_projections_cache[player_name] = {
                    'stats': custom_stats,
                    'projections': projections
                }
                
            except Exception as e:
                print(f"Error saving to Supabase: {e}")
                return jsonify({'success': False, 'error': f'Failed to save to Supabase: {str(e)}'}), 500
        else:
            return jsonify({'success': False, 'error': 'Supabase not available'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Custom projection saved for {player_name}',
            'projections': projections
        })
        
    except Exception as e:
        print(f"Error saving custom projection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reset_all_players', methods=['POST'])
def reset_all_players():
    """Reset all custom projections for the current user."""
    try:
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Remove all custom projections from Supabase if available
        if supabase:
            try:
                supabase.table('user_custom_projections').delete().eq('user_id', user_id).execute()
                print(f"Removed all custom projections for user {user_id} from Supabase")
            except Exception as e:
                print(f"Error removing from Supabase: {e}")
                return jsonify({'success': False, 'error': f'Failed to remove from Supabase: {str(e)}'}), 500
        else:
            return jsonify({'success': False, 'error': 'Supabase not available'}), 500
        
        # Custom projections disabled
        print("Custom projections disabled")
        
        return jsonify({
            'success': True,
            'message': 'All custom projections have been reset'
        })
        
    except Exception as e:
        print(f"Error resetting all players: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reset_custom_projection', methods=['POST'])
def reset_custom_projection():
    """Reset custom projection for a player."""
    try:
        data = request.get_json()
        player_name = data.get('player_name')
        
        if not player_name:
            return jsonify({'success': False, 'error': 'Player name required'}), 400
        
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Remove from Supabase if available
        if supabase:
            try:
                supabase.table('user_custom_projections').delete().eq('user_id', user_id).eq('player_name', player_name).execute()
                print(f"Removed custom projection for {player_name} from Supabase")
            except Exception as e:
                print(f"Error removing from Supabase: {e}")
                return jsonify({'success': False, 'error': f'Failed to remove from Supabase: {str(e)}'}), 500
        else:
            return jsonify({'success': False, 'error': 'Supabase not available'}), 500
        
        # Remove from local cache
        if player_name in custom_projections_cache:
            del custom_projections_cache[player_name]
            print(f"Removed custom projection for {player_name} from local cache")
        
        return jsonify({
            'success': True,
            'message': f'Custom projection reset for {player_name}'
        })
        
    except Exception as e:
        print(f"Error resetting custom projection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_custom_points(position, stats):
    """Calculate projected points based on custom stats for PPR scoring."""
    points = 0.0
    
    if position == 'QB':
        # Passing points: 4 pts per TD, 1 pt per 25 yards, -2 per INT
        points += stats.get('passing_yards', 0) / 25
        points += stats.get('passing_tds', 0) * 4
        points += stats.get('interceptions', 0) * -2
        
        # Rushing points: 6 pts per TD, 1 pt per 10 yards
        points += stats.get('rushing_yards', 0) / 10
        points += stats.get('rushing_tds', 0) * 6
        
        # Fumbles: -2 pts
        points += stats.get('fumbles', 0) * -2
        
    elif position in ['RB', 'WR', 'TE']:
        # Rushing points: 6 pts per TD, 1 pt per 10 yards
        points += stats.get('rushing_yards', 0) / 10
        points += stats.get('rushing_tds', 0) * 6
        
        # Receiving points: 6 pts per TD, 1 pt per 10 yards, 1 pt per reception (PPR)
        points += stats.get('receiving_yards', 0) / 10
        points += stats.get('receiving_tds', 0) * 6
        points += stats.get('receptions', 0) * 1.0  # Full PPR
        
        # Fumbles: -2 pts
        points += stats.get('fumbles', 0) * -2
        
    elif position == 'K':
        # Kicking points: 3 pts per FG, 1 pt per XP
        points += stats.get('field_goals', 0) * 3
        points += stats.get('extra_points', 0) * 1
        
    elif position == 'DEF':
        # Defense points: 1 pt per sack, 2 pts per INT/FR, 6 pts per TD, 2 pts per safety
        points += stats.get('sacks', 0) * 1
        points += stats.get('interceptions', 0) * 2
        points += stats.get('fumble_recoveries', 0) * 2
        points += stats.get('touchdowns', 0) * 6
        points += stats.get('safeties', 0) * 2
        
        # Points allowed bonuses (standard scoring)
        points_allowed = stats.get('points_allowed', 0)
        if points_allowed == 0:
            points += 10
        elif points_allowed <= 6:
            points += 7
        elif points_allowed <= 13:
            points += 4
        elif points_allowed <= 20:
            points += 1
        elif points_allowed <= 27:
            points += 0
        elif points_allowed <= 34:
            points += -1
        else:
            points += -4
    
    return round(points, 1)

@app.route('/api/user/export_data')
@login_required
def export_user_data():
    """Export all user data."""
    try:
        user_id = session['user_id']
        
        if not supabase:
            # Development mode - return sample data
            return jsonify({
                'success': True,
                'data': {
                    'user_id': user_id,
                    'email': session.get('user_email'),
                    'custom_projections': {},
                    'draft_sessions': [],
                    'rosters': []
                }
            })
        
        # Production mode - get data from Supabase
        custom_projections_response = supabase.table('user_custom_projections').select('*').eq('user_id', user_id).execute()
        draft_sessions_response = supabase.table('user_draft_sessions').select('*').eq('user_id', user_id).execute()
        rosters_response = supabase.table('user_rosters').select('*').eq('user_id', user_id).execute()
        
        export_data = {
            'user_id': user_id,
            'email': session.get('user_email'),
            'custom_projections': custom_projections_response.data,
            'draft_sessions': draft_sessions_response.data,
            'rosters': rosters_response.data
        }
        
        return jsonify({
            'success': True,
            'data': export_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/clear_data', methods=['POST'])
@login_required
def clear_user_data():
    """Clear all user data."""
    try:
        user_id = session['user_id']
        
        if not supabase:
            # Development mode - just return success
            return jsonify({
                'success': True,
                'message': 'All data cleared (development mode)'
            })
        
        # Production mode - delete data from Supabase
        supabase.table('user_custom_projections').delete().eq('user_id', user_id).execute()
        supabase.table('user_draft_sessions').delete().eq('user_id', user_id).execute()
        supabase.table('user_rosters').delete().eq('user_id', user_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'All data cleared successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug_custom_projections')
def debug_custom_projections():
    """Debug endpoint to check custom projections."""
    try:
        # Test a specific player
        test_player = "Ja'Marr Chase"
        projection = get_player_projection(test_player, selected_scoring_format)
        
        return jsonify({
            'success': True,
            'custom_projections_cache': custom_projections_cache,
            'dev_custom_projections': dev_custom_projections,
            'selected_scoring_format': selected_scoring_format,
            'user_id': session.get('user_id', 'not_logged_in'),
            'player_projections_cache_keys': list(player_projections_cache.keys())[:10],  # First 10 keys
            'test_player': test_player,
            'test_player_projection': projection,
            'test_player_in_cache': test_player in player_projections_cache,
            'cache_size': len(player_projections_cache)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test_custom_projections')
def test_custom_projections():
    """Test endpoint to verify custom projections are working."""
    # Custom projections disabled
    try:
        # Test with a sample player
        test_player = "Ja'Marr Chase"
        projection = get_player_projection(test_player, selected_scoring_format)
        
        # Custom projections disabled
        
        return jsonify({
            'success': True,
            'test_player': test_player,
            'projection': projection,
            'is_customized': test_player in custom_projections_cache,
            'scoring_format': selected_scoring_format,
            'cache_size': len(custom_projections_cache),
            'cache_keys': list(custom_projections_cache.keys())[:5],
            'player_in_cache': test_player in custom_projections_cache,
            'cache_data': custom_projections_cache.get(test_player, {})
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/force_cache_reload')
def force_cache_reload():
    """Force reload the projection cache."""
    try:
        global player_projections_cache
        print("Forcing cache reload...")
        cache_all_projections()
        
        return jsonify({
            'success': True,
            'cache_size': len(player_projections_cache),
            'message': f'Cache reloaded with {len(player_projections_cache)} players'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_draft', methods=['POST'])
@login_required
def save_draft():
    """Save the current draft session to local JSON file with actual draft data."""
    try:
        data = request.get_json()
        draft_name = data.get('draft_name', 'Draft 1')
        
        # Load existing drafts
        completed_drafts = load_completed_drafts_from_file()
        user_id = session.get('user_id', 'default_user')
        
        # Check if draft name already exists for this user
        user_drafts = completed_drafts.get(user_id, [])
        existing_names = [draft['session_name'] for draft in user_drafts]
        if draft_name in existing_names:
            return jsonify({
                'success': False,
                'error': f'Draft name "{draft_name}" already exists. Please choose a different name.'
            }), 400
        
        # Get the actual draft assistant and user's drafted players
        assistant = get_draft_assistant()
        user_team_name = assistant.teams[assistant.user_draft_position - 1]
        actual_drafted_players = assistant.drafted_players[user_team_name]
        
        # Convert actual players to serializable format
        drafted_players_data = []
        for player in actual_drafted_players:
            projected_points = get_player_projection(player.name, selected_scoring_format)
            drafted_players_data.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'projected_points': projected_points,
                'bye_week': player.bye_week
            })
        
        # Create draft entry with actual data
        session_id = f"draft_{int(time.time())}"
        draft_data = {
            'session_id': session_id,
            'session_name': draft_name,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'total_players': len(drafted_players_data),
            'draft_duration': '1h 0m',  # Could calculate actual duration if needed
            'is_active': False,
            'drafted_players': drafted_players_data
        }
        
        # Add to user's drafts
        if user_id not in completed_drafts:
            completed_drafts[user_id] = []
        completed_drafts[user_id].append(draft_data)
        
        # Save to JSON file
        save_completed_drafts_to_file(completed_drafts)
        
        print(f"Successfully saved draft '{draft_name}' with {len(drafted_players_data)} actual players")
        
        return jsonify({
            'success': True,
            'message': f'Draft "{draft_name}" saved successfully',
            'session_id': session_id
        })
    except Exception as e:
        print(f"Error saving draft: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/info')
@login_required
def get_user_info():
    """Get user information."""
    try:
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'email': user_email,
                'username': user_email.split('@')[0] if user_email else 'User'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/completed_drafts')
@login_required
def get_completed_drafts():
    """Get user's completed drafts from local JSON file."""
    try:
        user_id = session.get('user_id', 'default_user')
        print(f"Loading completed drafts for user: {user_id}")
        
        # Load drafts from local JSON file
        completed_drafts = load_completed_drafts_from_file()
        print(f"Loaded drafts data: {completed_drafts}")
        
        user_drafts = completed_drafts.get(user_id, [])
        print(f"Found {len(user_drafts)} drafts for user {user_id}")
        
        # Format drafts for frontend
        drafts = []
        for draft in user_drafts:
            try:
                # Calculate draft duration
                created_at_str = draft.get('created_at', '')
                completed_at_str = draft.get('completed_at', created_at_str)
                
                # Handle different date formats
                if created_at_str:
                    if 'T' in created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    else:
                        created_at = datetime.fromisoformat(created_at_str)
                else:
                    created_at = datetime.now()
                
                if completed_at_str and completed_at_str != created_at_str:
                    if 'T' in completed_at_str:
                        completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
                    else:
                        completed_at = datetime.fromisoformat(completed_at_str)
                else:
                    completed_at = created_at
                
                duration = completed_at - created_at
                duration_str = f"{duration.seconds // 3600}h {(duration.seconds % 3600) // 60}m"
                
                drafts.append({
                    'session_id': draft['session_id'],
                    'session_name': draft.get('session_name', 'Untitled Draft'),
                    'created_at': created_at_str,
                    'completed_at': completed_at_str,
                    'total_players': len(draft.get('drafted_players', [])),
                    'draft_duration': duration_str,
                    'is_active': draft.get('is_active', False)
                })
            except Exception as e:
                print(f"Error processing draft {draft.get('session_id', 'unknown')}: {e}")
                # Add draft with basic info even if duration calculation fails
                drafts.append({
                    'session_id': draft['session_id'],
                    'session_name': draft.get('session_name', 'Untitled Draft'),
                    'created_at': draft.get('created_at', ''),
                    'completed_at': draft.get('completed_at', draft.get('created_at', '')),
                    'total_players': len(draft.get('drafted_players', [])),
                    'draft_duration': 'N/A',
                    'is_active': draft.get('is_active', False)
                })
        
        print(f"Returning {len(drafts)} formatted drafts")
        return jsonify({
            'success': True,
            'drafts': drafts
        })
    except Exception as e:
        print(f"Error getting completed drafts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/draft/delete/<session_id>', methods=['DELETE'])
@login_required
def delete_draft(session_id):
    """Delete a draft session from local JSON file."""
    try:
        user_id = session.get('user_id', 'default_user')
        
        # Load drafts from local JSON file
        completed_drafts = load_completed_drafts_from_file()
        user_drafts = completed_drafts.get(user_id, [])
        
        # Find and remove the draft
        draft_found = False
        for i, draft in enumerate(user_drafts):
            if draft.get('session_id') == session_id:
                user_drafts.pop(i)
                draft_found = True
                break
        
        if not draft_found:
            return jsonify({
                'success': False,
                'error': 'Draft not found or you do not have permission to delete it'
            }), 404
        
        # Update the completed drafts
        completed_drafts[user_id] = user_drafts
        save_completed_drafts_to_file(completed_drafts)
        
        return jsonify({
            'success': True,
            'message': 'Draft deleted successfully'
        })
    except Exception as e:
        print(f"Error deleting draft: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/draft/<session_id>')
@login_required
def get_draft_details(session_id):
    """Get detailed information about a specific draft from local JSON file."""
    try:
        user_id = session.get('user_id', 'default_user')
        
        # Load drafts from local JSON file
        completed_drafts = load_completed_drafts_from_file()
        user_drafts = completed_drafts.get(user_id, [])
        
        # Find the specific draft
        draft = None
        for d in user_drafts:
            if d.get('session_id') == session_id:
                draft = d
                break
        
        if not draft:
            return jsonify({
                'success': False,
                'error': 'Draft not found'
            }), 404
        
        return jsonify({
            'success': True,
            'draft': draft
        })
    except Exception as e:
        print(f"Error getting draft details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def load_completed_drafts_from_file():
    """Load completed drafts from JSON file."""
    try:
        if os.path.exists(COMPLETED_DRAFTS_FILE):
            with open(COMPLETED_DRAFTS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('completed_drafts', {})
        else:
            return {}
    except Exception as e:
        print(f"Error loading completed drafts: {e}")
        return {}

def save_completed_drafts_to_file(completed_drafts):
    """Save completed drafts to JSON file."""
    try:
        data = {
            'completed_drafts': completed_drafts,
            'last_updated': datetime.now().isoformat()
        }
        with open(COMPLETED_DRAFTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(completed_drafts)} completed drafts to file")
    except Exception as e:
        print(f"Error saving completed drafts: {e}")

@app.route('/api/auth/user')
def get_current_user():
    """Get current user information."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    return jsonify({
        'success': True,
        'user': {
            'id': session.get('user_id'),
            'email': session.get('user_email')
        }
    })

@app.route('/api/auth/check')
def check_auth():
    """Check if user is authenticated."""
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'user_id': session['user_id']})
    else:
        return jsonify({'authenticated': False}), 401

def load_user_custom_projections_from_supabase(user_id):
    """Load custom projections for a specific user from Supabase."""
    try:
        if not supabase:
            print("No Supabase connection available - using local cache")
            return custom_projections_cache
        
        # Check if the table exists first
        try:
            result = supabase.table('user_custom_projections').select('*').eq('user_id', user_id).execute()
            custom_projections = {}
            for row in result.data:
                player_name = row.get('player_name')
                if player_name:
                    custom_projections[player_name] = {
                        'passing_yards': row.get('passing_yards', 0),
                        'passing_tds': row.get('passing_tds', 0),
                        'passing_ints': row.get('passing_ints', 0),
                        'rushing_yards': row.get('rushing_yards', 0),
                        'rushing_tds': row.get('rushing_tds', 0),
                        'receptions': row.get('receptions', 0),
                        'receiving_yards': row.get('receiving_yards', 0),
                        'receiving_tds': row.get('receiving_tds', 0),
                        'fumbles': row.get('fumbles', 0),
                        'fg_made': row.get('fg_made', 0),
                        'xp_made': row.get('xp_made', 0)
                    }
            print(f"Loaded {len(custom_projections)} custom projections from Supabase for user {user_id}")
            return custom_projections
        except Exception as e:
            if "does not exist" in str(e):
                print(f"Table user_custom_projections does not exist for user {user_id}")
                return {}
            else:
                print(f"Error loading custom projections from Supabase: {e}")
                return {}
    except Exception as e:
        print(f"Error loading custom projections: {e}")
        return {}

def initialize_draft_with_user_data(user_id):
    """Initialize draft with user data (custom projections disabled)."""
    if not user_id:
        print("No user_id provided, skipping custom projections load")
        return
    
    print(f"Initializing draft with user data for user_id: {user_id}")
    print("Custom projections are disabled as requested")

def initialize_app():
    """Initialize all app components on startup."""
    try:
        print("Initializing James Clessuras FF application...")
        
        # Initialize Supabase connection
        if supabase:
            print("✓ Supabase connection established")
        else:
            print("⚠️ Supabase not configured, running in development mode")
        
        # PRE-LOAD PLAYERS GLOBALLY - This ensures players are always available
        print("🚀 Pre-loading players globally...")
        load_players_globally()
        print("✓ Players pre-loaded globally")
        
        # Initialize draft assistant
        assistant = get_draft_assistant()
        print("✓ Draft assistant initialized")
        
        # Load projections
        try:
            cache_all_projections()
            print("✓ Player projections loaded")
        except Exception as e:
            print(f"⚠️ Warning: Could not load projections: {e}")
        
        # Load custom projections (will be loaded per-user during draft initialization)
        # Custom projections are disabled as requested
        print("✓ Custom projections disabled")
        
        print("✓ James Clessuras FF initialization complete")
        return True
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return False

# Initialize app components
if not initialize_app():
    print("Warning: App initialization had issues, but continuing...")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=False, host='0.0.0.0', port=port) 