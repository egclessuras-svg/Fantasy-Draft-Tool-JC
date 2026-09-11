import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass
from collections import defaultdict
import random
import os

@dataclass(frozen=True)
class Player:
    name: str
    position: str
    team: str
    adp: float
    bye_week: int
    projected_points: float
    weekly_projections: tuple
    
    def __str__(self):
        return f"{self.name} ({self.position}, {self.team}) - Rank: {self.adp:.0f}, Proj: {self.projected_points:.1f}"

class FantasyDraftAssistant:
    def __init__(self, csv_file_path: str):
        """Initialize the fantasy draft assistant with player data from CSV."""
        self.csv_file_path = csv_file_path
        self.players = []
        self.raw_stats = {}  # Store raw FantasyPros stats for customization
        self.oalffl_rankings = {}  # Store OALFFL rankings
        self.load_players()
        self.load_oalffl_rankings()
        
        # League settings (configurable)
        self.num_teams = 12
        self.user_draft_position = 1
        self.current_round = 1
        self.current_pick = 1
        self.draft_order = []
        
        # Calculate total picks (20 rounds * num_teams)
        self.total_picks = 20 * self.num_teams
        
        # Roster constraints (configurable) - James Clessuras OALFFL League
        self.roster_constraints = {
            'QB': 2,  # 2 Quarterbacks
            'WR': 2,  # 2 Wide Receivers
            'RB': 2,  # 2 Running Backs
            'TE': 1,  # 1 Tight End
            'FLEX': 1,  # 1 Flex (RB/WR/TE)
            'K': 1,    # 1 Kicker
            'DST': 1,  # 1 Defense/Special Teams
            'BN': 6    # 6 Bench spots
        }
        
        # Draft state
        self.drafted_players = {f'Team {i+1}': [] for i in range(self.num_teams)}
        self.available_players = set(self.players)
        self.draft_history = []
        
        # Cached recommendations
        self._cached_recommendations = []
        
        # Team names
        self.teams = [f'Team {i+1}' for i in range(self.num_teams)]
        
        # Draft initialization state
        self.draft_initialized = False
        
        self.scoring_format = 'ppr'  # Default scoring format - James Clessuras OALFFL League
        
        self._generate_draft_order()
    
    def load_oalffl_rankings(self):
        """Load OALFFL rankings from CSV file."""
        oalffl_file = "09012025Rankings_updated_oalffl (1).csv"
        if not os.path.exists(oalffl_file):
            print(f"OALFFL rankings file not found: {oalffl_file}")
            return
        
        try:
            with open(oalffl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip header lines and find the data section
            data_start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('Rank,Pos,Team,Name,Bye,Points'):
                    data_start = i + 1
                    break
            
            # Parse the rankings data
            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith(','):
                    continue
                
                parts = line.split(',')
                if len(parts) >= 6:
                    try:
                        rank = int(parts[0])
                        position = parts[1].strip()
                        team = parts[2].strip()
                        name = parts[3].strip()
                        bye = parts[4].strip()
                        points = float(parts[5]) if parts[5] else 0.0
                        
                        # Store ranking data
                        self.oalffl_rankings[name] = {
                            'rank': rank,
                            'position': position,
                            'team': team,
                            'bye': bye,
                            'points': points
                        }
                    except (ValueError, IndexError) as e:
                        continue
            
            print(f"Loaded {len(self.oalffl_rankings)} OALFFL rankings")
            
        except Exception as e:
            print(f"Error loading OALFFL rankings: {e}")
    
    def get_player_raw_stats(self, player_name: str) -> dict:
        """Get raw stats for a player from FantasyPros data."""
        return self.raw_stats.get(player_name, {})
    
    def set_player_raw_stats(self, player_name: str, stats: dict):
        """Set raw stats for a player."""
        self.raw_stats[player_name] = stats
    

    
    def set_scoring_format(self, scoring_format: str):
        """Set the scoring format for the draft assistant."""
        self.scoring_format = scoring_format
    
    def get_player_projected_points(self, player: Player, scoring_format: Optional[str] = None) -> float:
        """Get projected points for a player from OALFFL rankings."""
        # Use the player's default projected points from OALFFL rankings
        return player.projected_points if player.projected_points is not None else 0.0
    

    
    def _calculate_qb_points(self, row, scoring_format):
        """Calculate QB points based on scoring format."""
        try:
            # Get stats from row and handle comma-separated numbers
            def safe_float(value):
                if pd.isna(value) or value == '':
                    return 0.0
                # Remove commas and convert to float
                return float(str(value).replace(',', ''))
            
            passing_yards = safe_float(row['YDS'])
            passing_tds = safe_float(row['TDS'])
            interceptions = safe_float(row['INTS'])
            rushing_yards = safe_float(row['YDS.1'])
            rushing_tds = safe_float(row['TDS.1'])
            fumbles = safe_float(row['FL'])
            
            # QB scoring is the same for all formats (no receptions)
            points = (passing_yards / 25) + (passing_tds * 4) + (interceptions * -2) + \
                    (rushing_yards / 10) + (rushing_tds * 6) + (fumbles * -2)
            
            return points
        except Exception as e:
            print(f"Error calculating QB points: {e}")
            return 0.0
    
    def _calculate_rb_points(self, row, scoring_format):
        """Calculate RB points based on scoring format."""
        try:
            # Get stats from row and handle comma-separated numbers
            def safe_float(value):
                if pd.isna(value) or value == '':
                    return 0.0
                # Remove commas and convert to float
                return float(str(value).replace(',', ''))
            
            rushing_yards = safe_float(row['YDS'])
            rushing_tds = safe_float(row['TDS'])
            receiving_yards = safe_float(row['YDS.1'])
            receiving_tds = safe_float(row['TDS.1'])
            receptions = safe_float(row['REC'])
            fumbles = safe_float(row['FL'])
            
            # Calculate base points
            rushing_points = (rushing_yards / 10) + (rushing_tds * 6)
            receiving_points = (receiving_yards / 10) + (receiving_tds * 6)
            
            # Add reception points based on format
            if scoring_format == 'ppr':
                receiving_points += receptions * 1.0
            elif scoring_format == 'half-ppr':
                receiving_points += receptions * 0.5
            # standard: no reception points
            
            points = rushing_points + receiving_points + (fumbles * -2)
            return points
        except Exception as e:
            print(f"Error calculating RB points: {e}")
            return 0.0
    
    def _calculate_wr_points(self, row, scoring_format):
        """Calculate WR points based on scoring format."""
        try:
            # Get stats from row and handle comma-separated numbers
            def safe_float(value):
                if pd.isna(value) or value == '':
                    return 0.0
                # Remove commas and convert to float
                return float(str(value).replace(',', ''))
            
            receiving_yards = safe_float(row['YDS'])
            receiving_tds = safe_float(row['TDS'])
            receptions = safe_float(row['REC'])
            rushing_yards = safe_float(row['YDS.1'])
            rushing_tds = safe_float(row['TDS.1'])
            fumbles = safe_float(row['FL'])
            
            # Calculate base points
            rushing_points = (rushing_yards / 10) + (rushing_tds * 6)
            receiving_points = (receiving_yards / 10) + (receiving_tds * 6)
            
            # Add reception points based on format
            if scoring_format == 'ppr':
                receiving_points += receptions * 1.0
            elif scoring_format == 'half-ppr':
                receiving_points += receptions * 0.5
            # standard: no reception points
            
            points = rushing_points + receiving_points + (fumbles * -2)
            return points
        except Exception as e:
            print(f"Error calculating WR points: {e}")
            return 0.0
    
    def _calculate_te_points(self, row, scoring_format):
        """Calculate TE points based on scoring format."""
        try:
            # Get stats from row and handle comma-separated numbers
            def safe_float(value):
                if pd.isna(value) or value == '':
                    return 0.0
                # Remove commas and convert to float
                return float(str(value).replace(',', ''))
            
            receiving_yards = safe_float(row['YDS'])
            receiving_tds = safe_float(row['TDS'])
            receptions = safe_float(row['REC'])
            fumbles = safe_float(row['FL'])
            
            # Calculate base points
            receiving_points = (receiving_yards / 10) + (receiving_tds * 6)
            
            # Add reception points based on format
            if scoring_format == 'ppr':
                receiving_points += receptions * 1.0
            elif scoring_format == 'half-ppr':
                receiving_points += receptions * 0.5
            # standard: no reception points
            
            points = receiving_points + (fumbles * -2)
            return points
        except Exception as e:
            print(f"Error calculating TE points: {e}")
            return 0.0
    
    def load_players(self):
        """Load player data from OALFFL rankings CSV file."""
        try:
            # Load players directly from OALFFL rankings
            all_players = []
            
            # Use the OALFFL rankings data that was already loaded
            for name, data in self.oalffl_rankings.items():
                try:
                    # Get player data from OALFFL rankings
                    rank = data['rank']
                    position = data['position']
                    team = data['team']
                    bye = data['bye']
                    points = data['points']
                    
                    # Map ST position to DEF
                    if position == 'ST':
                        position = 'DEF'
                    
                    # Handle bye week
                    try:
                        bye_week = int(bye) if bye and bye != '' else 0
                    except (ValueError, TypeError):
                        bye_week = 0
                    
                    # Create player object
                    player = Player(
                        name=name,
                        position=position,
                        team=team,
                        adp=float(rank),  # Use rank as ADP
                        projected_points=float(points),  # Use points as projected points
                        bye_week=bye_week
                    )
                    
                    all_players.append(player)
                    
                except (ValueError, TypeError) as e:
                    print(f"Error processing player {name}: {e}")
                    continue
            
            # Set the players list
            self.players = all_players
            print(f"Loaded {len(self.players)} players from OALFFL rankings")
            
        except Exception as e:
            print(f"Error loading OALFFL rankings: {e}")
            self.players = []
                        
                        # Create player object
                        player = Player(
                            name=name,
                            position=position,
                            team=team,
                            adp=adp,
                            bye_week=bye_week,
                            projected_points=projected_points,
                            weekly_projections=tuple([projected_points/17] * 18)
                        )
                        all_players.append(player)
                        
            except Exception as e:
                print(f"Error loading main CSV: {e}")
            
            # Now enhance with FantasyPros data for better scoring calculations
            try:
                # Load QB data for enhanced scoring
                qb_df = pd.read_csv('FantasyPros_Fantasy_Football_Projections_QB (1).csv')
                for _, row in qb_df.iterrows():
                    if pd.notna(row['Player']) and str(row['Player']).strip() != '':
                        player_name = str(row['Player']).strip()
                        
                        # Store raw stats for customization
                        raw_stats = {
                            'passing_yards': self._safe_float(row['YDS']),
                            'passing_tds': self._safe_float(row['TDS']),
                            'interceptions': self._safe_float(row['INTS']),
                            'rushing_yards': self._safe_float(row['YDS.1']),
                            'rushing_tds': self._safe_float(row['TDS.1']),
                            'fumbles': self._safe_float(row['FL'])
                        }
                        self.raw_stats[player_name] = raw_stats
                        
                        # Find matching player in our list and update team if needed
                        for player in all_players:
                            if player.name == player_name and player.position == 'QB':
                                # Note: We can't modify frozen Player fields, so we'll use raw_stats for team info
                                break
            except Exception as e:
                print(f"Error loading QB data: {e}")
            
            # Load RB data for enhanced scoring
            try:
                rb_df = pd.read_csv('FantasyPros_Fantasy_Football_Projections_RB (2).csv')
                for _, row in rb_df.iterrows():
                    if pd.notna(row['Player']) and str(row['Player']).strip() != '':
                        player_name = str(row['Player']).strip()
                        
                        # Store raw stats for customization
                        raw_stats = {
                            'rushing_yards': self._safe_float(row['YDS']),
                            'rushing_tds': self._safe_float(row['TDS']),
                            'receiving_yards': self._safe_float(row['YDS.1']),
                            'receiving_tds': self._safe_float(row['TDS.1']),
                            'receptions': self._safe_float(row['REC']),
                            'fumbles': self._safe_float(row['FL'])
                        }
                        self.raw_stats[player_name] = raw_stats
                        
                        # Find matching player in our list
                        for player in all_players:
                            if player.name == player_name and player.position == 'RB':
                                break
            except Exception as e:
                print(f"Error loading RB data: {e}")
            
            # Load WR data for enhanced scoring
            try:
                wr_df = pd.read_csv('FantasyPros_Fantasy_Football_Projections_WR (1).csv')
                for _, row in wr_df.iterrows():
                    if pd.notna(row['Player']) and str(row['Player']).strip() != '':
                        player_name = str(row['Player']).strip()
                        
                        # Store raw stats for customization
                        raw_stats = {
                            'receiving_yards': self._safe_float(row['YDS']),
                            'receiving_tds': self._safe_float(row['TDS']),
                            'receptions': self._safe_float(row['REC']),
                            'rushing_yards': self._safe_float(row['YDS.1']),
                            'rushing_tds': self._safe_float(row['TDS.1']),
                            'fumbles': self._safe_float(row['FL'])
                        }
                        self.raw_stats[player_name] = raw_stats
                        
                        # Find matching player in our list
                        for player in all_players:
                            if player.name == player_name and player.position == 'WR':
                                break
            except Exception as e:
                print(f"Error loading WR data: {e}")
            
            # Load TE data for enhanced scoring
            try:
                te_df = pd.read_csv('FantasyPros_Fantasy_Football_Projections_TE (2) (1).csv')
                for _, row in te_df.iterrows():
                    if pd.notna(row['Player']) and str(row['Player']).strip() != '':
                        player_name = str(row['Player']).strip()
                        
                        # Store raw stats for customization
                        raw_stats = {
                            'receiving_yards': self._safe_float(row['YDS']),
                            'receiving_tds': self._safe_float(row['TDS']),
                            'receptions': self._safe_float(row['REC']),
                            'fumbles': self._safe_float(row['FL'])
                        }
                        self.raw_stats[player_name] = raw_stats
                        
                        # Find matching player in our list
                        for player in all_players:
                            if player.name == player_name and player.position == 'TE':
                                break
            except Exception as e:
                print(f"Error loading TE data: {e}")
            
            # Load K data
            try:
                k_df = pd.read_csv('FantasyPros_Fantasy_Football_Projections_K.csv')
                for _, row in k_df.iterrows():
                    if pd.notna(row['Player']) and str(row['Player']).strip() != '':
                        player_name = str(row['Player']).strip()
                        
                        # Store raw stats for customization
                        raw_stats = {
                            'field_goals': self._safe_float(row.get('FG', 0)),
                            'extra_points': self._safe_float(row.get('XP', 0)),
                            'projected_points': self._safe_float(row['FPTS'])
                        }
                        self.raw_stats[player_name] = raw_stats
                        
                        # Find matching player in our list and update projected points
                        for player in all_players:
                            if player.name == player_name and player.position == 'K':
                                # We can't modify frozen Player fields, so we'll use raw_stats for projected points
                                break
            except Exception as e:
                print(f"Error loading K data: {e}")
            
            # Load DEF data
            try:
                def_df = pd.read_csv('FantasyPros_Fantasy_Football_Projections_DST.csv')
                for _, row in def_df.iterrows():
                    if pd.notna(row['Player']) and str(row['Player']).strip() != '':
                        player_name = str(row['Player']).strip()
                        
                        # Store raw stats for customization
                        raw_stats = {
                            'sacks': self._safe_float(row.get('SACK', 0)),
                            'interceptions': self._safe_float(row.get('INT', 0)),
                            'fumble_recoveries': self._safe_float(row.get('FR', 0)),
                            'touchdowns': self._safe_float(row.get('TD', 0)),
                            'safeties': self._safe_float(row.get('SAFETY', 0)),
                            'points_allowed': self._safe_float(row.get('PA', 0)),
                            'projected_points': self._safe_float(row['FPTS'])
                        }
                        self.raw_stats[player_name] = raw_stats
                        
                        # Find matching player in our list
                        for player in all_players:
                            if player.name == player_name and player.position == 'DEF':
                                break
            except Exception as e:
                print(f"Error loading DEF data: {e}")
            
            self.players = all_players
            print(f"Loaded {len(self.players)} players from comprehensive data sources")
            print(f"Stored raw stats for {len(self.raw_stats)} players")
            
        except Exception as e:
            print(f"Error loading CSV files: {e}")
            # Create some sample data if CSV loading fails
            self._create_sample_data()
    
    def _safe_float(self, value):
        """Safely convert value to float, handling comma-separated numbers."""
        if pd.isna(value) or value == '':
            return 0.0
        # Remove commas and convert to float
        return float(str(value).replace(',', ''))
    
    def _create_sample_data(self):
        """Create sample player data if CSV loading fails."""
        sample_players = [
            # QBs
            Player("Patrick Mahomes", "QB", "KC", 21.0, 10, 364.1, tuple([21.4] * 18)),
            Player("Josh Allen", "QB", "BUF", 23.5, 7, 371.1, tuple([21.8] * 18)),
            Player("Jalen Hurts", "QB", "PHI", 25.0, 9, 350.2, tuple([20.6] * 18)),
            Player("Lamar Jackson", "QB", "BAL", 28.0, 13, 340.5, tuple([20.0] * 18)),
            Player("Justin Herbert", "QB", "LAC", 30.0, 5, 330.8, tuple([19.5] * 18)),
            
            # RBs
            Player("Christian McCaffrey", "RB", "SF", 9.5, 14, 203.1, tuple([11.9] * 18)),
            Player("Saquon Barkley", "RB", "PHI", 3.0, 9, 259.9, tuple([15.3] * 18)),
            Player("Bijan Robinson", "RB", "ATL", 5.0, 11, 245.6, tuple([14.4] * 18)),
            Player("Jonathan Taylor", "RB", "IND", 8.0, 11, 235.2, tuple([13.8] * 18)),
            Player("Derrick Henry", "RB", "BAL", 12.0, 13, 225.8, tuple([13.3] * 18)),
            Player("Nick Chubb", "RB", "CLE", 15.0, 5, 215.4, tuple([12.7] * 18)),
            Player("Austin Ekeler", "RB", "WAS", 18.0, 7, 205.1, tuple([12.1] * 18)),
            
            # WRs
            Player("Ja'Marr Chase", "WR", "CIN", 1.0, 10, 226.1, tuple([13.3] * 18)),
            Player("Justin Jefferson", "WR", "MIN", 4.5, 6, 196.3, tuple([11.5] * 18)),
            Player("Tyreek Hill", "WR", "MIA", 6.0, 10, 185.7, tuple([10.9] * 18)),
            Player("CeeDee Lamb", "WR", "DAL", 7.0, 7, 175.2, tuple([10.3] * 18)),
            Player("Amon-Ra St. Brown", "WR", "DET", 10.0, 9, 165.8, tuple([9.8] * 18)),
            Player("Davante Adams", "WR", "LV", 13.0, 13, 155.4, tuple([9.1] * 18)),
            Player("Stefon Diggs", "WR", "HOU", 16.0, 7, 145.1, tuple([8.5] * 18)),
            Player("AJ Brown", "WR", "PHI", 19.0, 9, 135.7, tuple([8.0] * 18)),
            
            # TEs
            Player("Travis Kelce", "TE", "KC", 78.0, 10, 104.6, tuple([6.2] * 18)),
            Player("George Kittle", "TE", "SF", 43.5, 14, 149.6, tuple([8.8] * 18)),
            Player("Mark Andrews", "TE", "BAL", 50.0, 13, 140.2, tuple([8.2] * 18)),
            Player("T.J. Hockenson", "TE", "MIN", 55.0, 6, 130.8, tuple([7.7] * 18)),
            Player("Sam LaPorta", "TE", "DET", 60.0, 9, 120.4, tuple([7.1] * 18)),
            
            # Ks
            Player("Justin Tucker", "K", "BAL", 120.0, 13, 150.0, tuple([8.8] * 18)),
            Player("Harrison Butker", "K", "KC", 125.0, 10, 145.0, tuple([8.5] * 18)),
            Player("Evan McPherson", "K", "CIN", 130.0, 10, 140.0, tuple([8.2] * 18)),
            
            # DEFs
            Player("San Francisco 49ers", "DEF", "SF", 140.0, 14, 180.0, tuple([10.6] * 18)),
            Player("Dallas Cowboys", "DEF", "DAL", 145.0, 7, 175.0, tuple([10.3] * 18)),
            Player("Buffalo Bills", "DEF", "BUF", 150.0, 7, 170.0, tuple([10.0] * 18)),
        ]
        self.players = sample_players
        print("Created sample player data")
    
    def _generate_draft_order(self):
        """Generate snake draft order based on roster constraints."""
        self.draft_order = []
        
        # Calculate total picks needed per team based on roster constraints
        total_picks_per_team = sum(self.roster_constraints.values())
        
        for round_num in range(1, total_picks_per_team + 1):
            if round_num % 2 == 1:  # Odd rounds: 1, 2, 3, ..., num_teams
                round_order = list(range(1, self.num_teams + 1))
            else:  # Even rounds: num_teams, num_teams-1, ..., 1
                round_order = list(range(self.num_teams, 0, -1))
            
            for team_id in round_order:
                self.draft_order.append((round_num, team_id))
        
        # Update total picks
        self.total_picks = len(self.draft_order)
    
    def get_current_pick_info(self) -> Dict:
        """Get information about the current pick."""
        # If draft is not initialized, return a status indicating it's not started
        if not self.draft_initialized:
            return {
                "status": "Draft Not Started",
                "is_user_turn": False,
                "round": 0,
                "pick": 0,
                "team_id": 0,
                "team_name": "None"
            }
        
        if self.current_pick > len(self.draft_order):
            return {"status": "Draft Complete"}
        
        round_num, team_id = self.draft_order[self.current_pick - 1]
        team_name = self.teams[team_id - 1]
        is_user_turn = (team_id == self.user_draft_position)
        
        return {
            "round": round_num,
            "pick": self.current_pick,
            "team_id": team_id,
            "team_name": team_name,
            "is_user_turn": is_user_turn,
            "status": "User Turn" if is_user_turn else "Other Team Turn"
        }
    
    def get_available_players(self, position: Optional[str] = None) -> List[Player]:
        """Get list of available players, optionally filtered by position."""
        available = list(self.available_players)
        
        if position:
            available = [p for p in available if p.position == position]
        
        # Sort by ADP
        available.sort(key=lambda p: p.adp)
        return available
    
    def search_players(self, query: str, position: Optional[str] = None) -> List[Player]:
        """Search for players by name."""
        query = query.lower()
        available = self.get_available_players(position)
        
        matches = []
        for player in available:
            if query in player.name.lower():
                matches.append(player)
        
        return matches
    
    def draft_player(self, player_name: str, team_id: Optional[str] = None) -> bool:
        """Draft a player for the specified team (or current team if not specified)."""
        # Normalize player name for comparison
        player_name_norm = player_name.strip().lower()
        player = None
        for p in self.available_players:
            if p.name.strip().lower() == player_name_norm:
                player = p
                break
        
        if not player:
            print(f"Player '{player_name}' not found or already drafted")
            return False
        
        # Handle team_id as int or string
        if team_id is None:
            current_team = self._get_current_team()
            team_id = current_team
        else:
            # Convert int team_id to string if needed
            if isinstance(team_id, int) or (isinstance(team_id, str) and team_id.isdigit()):
                team_id = f'Team {int(team_id)}'
            elif not isinstance(team_id, str):
                team_id = str(team_id)
            # Validate team_id
            if team_id not in self.drafted_players:
                print(f"Invalid team_id: {team_id}")
                return False
        
        # Add player to team
        self.drafted_players[team_id].append(player)
        self.available_players.remove(player)
        
        # Record the pick with correct round and pick information
        if self.current_pick <= len(self.draft_order):
            round_num, team_id_from_order = self.draft_order[self.current_pick - 1]
            pick_info = {
                'round': round_num,
                'pick': self.current_pick,
                'team_name': team_id,
                'player': player
            }
        else:
            # Fallback for picks beyond draft order
            pick_info = {
                'round': self.current_round,
                'pick': self.current_pick,
                'team_name': team_id,
                'player': player
            }
        self.draft_history.append(pick_info)
        
        # Move to next pick
        self._advance_pick()
        
        # Clear cached recommendations since the draft state changed
        self._cached_recommendations = []
        
        return True
    
    def _can_draft_player(self, player: Player, team_name: str) -> bool:
        """Check if a player can be drafted based on roster constraints."""
        current_roster = self.drafted_players[team_name]
        
        # Count current positions
        position_counts = defaultdict(int)
        for p in current_roster:
            position_counts[p.position] += 1
        
        # Check specific position constraints
        if player.position in ['QB', 'K', 'DEF']:
            if position_counts[player.position] >= self.roster_constraints[player.position]:
                return False
        
        # Check WR/RB/TE constraints
        elif player.position in ['WR', 'RB', 'TE']:
            # Check if we can add to FLEX
            flex_used = min(position_counts['WR'], self.roster_constraints['WR']) + \
                       min(position_counts['RB'], self.roster_constraints['RB']) + \
                       min(position_counts['TE'], self.roster_constraints['TE'])
            
            # Check if we can add to specific position
            if position_counts[player.position] >= self.roster_constraints[player.position]:
                # Check if we can add to FLEX
                if flex_used >= self.roster_constraints['WR'] + self.roster_constraints['RB'] + self.roster_constraints['TE'] + self.roster_constraints['FLEX']:
                    return False
        
        # Check total roster size
        total_players = len(current_roster) + 1
        max_players = sum(self.roster_constraints.values())
        
        return total_players <= max_players
    
    def get_roster_needs(self, team_name: str) -> Dict[str, int]:
        """Get the roster needs for a specific team, considering bench constraints."""
        current_roster = self.drafted_players[team_name]
        position_counts = defaultdict(int)
        
        for player in current_roster:
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
            'DEF': 0
        }
        
        # Sort players by projected points to prioritize starters
        sorted_roster = sorted(current_roster, key=lambda p: p.projected_points, reverse=True)
        
        for player in sorted_roster:
            pos = player.position
            
            # Check if we can fill a starting position
            if pos in filled_positions and filled_positions[pos] < self.roster_constraints.get(pos, 0):
                # Fill starting position
                filled_positions[pos] += 1
                starters.append(player)
            elif pos in ['RB', 'WR', 'TE'] and filled_positions['FLEX'] < self.roster_constraints.get('FLEX', 0):
                # Fill FLEX position
                filled_positions['FLEX'] += 1
                starters.append(player)
            else:
                # Player goes to bench
                bench_players.append(player)
        
        # Calculate total bench spots used (only actual bench players)
        bench_used = len(bench_players)
        bench_available = max(0, self.roster_constraints.get('BN', 6) - bench_used)
        
        # Calculate needs for starting positions
        needs = {}
        for position, max_count in self.roster_constraints.items():
            if position == 'FLEX':
                continue
            current = position_counts.get(position, 0)
            needs[position] = max(0, max_count - current)
        
        # Add bench availability
        if bench_available > 0:
            needs['BN'] = bench_available
        
        return needs
    
    def calculate_vorp(self, player: Player, position: str) -> float:
        """Calculate Value Over Replacement Player (VORP) for a player, accounting for bye week fill-ins."""
        available_players = self.get_available_players(position)
        
        if not available_players:
            return 0.0
        
        # Find replacement level player (typically the 12th best at position for 12-team league)
        replacement_index = min(self.num_teams - 1, len(available_players) - 1)
        if replacement_index < 0:
            return 0.0
        
        replacement_player = available_players[replacement_index]
        
        # Calculate base VORP
        base_vorp = player.projected_points - replacement_player.projected_points
        
        # Check if player contributes during bye weeks (starts in any week)
        bye_week_contribution = 0
        if player.bye_week > 0:
            # Sample a few weeks to see if player would start
            sample_weeks = [1, 5, 10, 15]  # Sample different parts of season
            for week in sample_weeks:
                if week != player.bye_week:
                    # This is a simplified check - in reality you'd compare to other available players
                    bye_week_contribution += player.projected_points / 17 * 0.1  # Small bonus for bye week flexibility
        
        return base_vorp + bye_week_contribution
    
    def get_optimal_lineup(self, team_name: str, week: int) -> Dict[str, Player]:
        """Get the optimal lineup for a team in a specific week."""
        roster = self.drafted_players[team_name]
        
        # Filter out players on bye
        available = [p for p in roster if p.bye_week != week]
        
        # Sort by weekly projection
        available.sort(key=lambda p: p.weekly_projections[week-1] if week <= len(p.weekly_projections) else 0, reverse=True)
        
        lineup = {}
        
        # Fill QB, K, DEF
        for pos in ['QB', 'K', 'DEF']:
            for player in available:
                if player.position == pos and pos not in lineup:
                    lineup[pos] = player
                    break
        
        # Fill WR, RB, TE, FLEX
        wr_count = 0
        rb_count = 0
        te_count = 0
        flex_filled = False
        
        for player in available:
            if player in lineup.values():
                continue
                
            if player.position == 'WR' and wr_count < self.roster_constraints['WR']:
                lineup[f'WR{wr_count + 1}'] = player
                wr_count += 1
            elif player.position == 'RB' and rb_count < self.roster_constraints['RB']:
                lineup[f'RB{rb_count + 1}'] = player
                rb_count += 1
            elif player.position == 'TE' and te_count < self.roster_constraints['TE']:
                lineup['TE'] = player
                te_count += 1
            elif not flex_filled and player.position in ['RB', 'WR', 'TE']:
                lineup['FLEX'] = player
                flex_filled = True
        
        return lineup
    
    def calculate_team_score(self, team_name: str, week: int) -> float:
        """Calculate the projected score for a team in a specific week."""
        lineup = self.get_optimal_lineup(team_name, week)
        total_score = 0.0
        
        for position, player in lineup.items():
            if week <= len(player.weekly_projections):
                total_score += player.weekly_projections[week-1]
        
        return total_score
    
    def calculate_season_score(self, team_name: str) -> float:
        """Calculate the projected season score for a team."""
        total_score = 0.0
        for week in range(1, 19):  # 18-week season
            total_score += self.calculate_team_score(team_name, week)
        return total_score
    
    def run_simulations(self, num_recommendations: int = 5) -> List[Dict]:
        """Run optimized simulations to generate recommendations."""
        if not self.draft_initialized:
            return []
        
        if not self.get_current_pick_info()["is_user_turn"]:
            return []
        
        recommendations = []
        
        # Get all available players sorted by projected points
        available_players = sorted(self.get_available_players(), key=lambda p: self.get_player_projected_points(p, self.scoring_format), reverse=True)
        
        # Get top 1 player at each position (by projected points)
        top_players_by_position = {}
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            position_players = [p for p in available_players if p.position == position]
            if position_players:
                top_players_by_position[position] = position_players[0]
        
        # Run simulations only for the top player at each position
        player_scores = {}
        
        print(f"Running simulations for top 1 player at each position...")
        
        for position, top_player in top_players_by_position.items():
            scores = []
            successful_sims = 0
            
            # Run 50 simulations for the top player at this position
            for sim in range(50):
                try:
                    score = self._simulate_draft_with_player_simple(top_player)
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
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            if position not in top_players_by_position:
                continue
                
            top_player = top_players_by_position[position]
            top_player_score = player_scores.get(top_player, 0)
            top_player_projected = self.get_player_projected_points(top_player, self.scoring_format)
            
            # Get next 4 players at this position
            position_players = [p for p in available_players if p.position == position]
            other_players = position_players[1:5]  # Skip the top player, take next 4
            
            for other_player in other_players:
                other_projected = self.get_player_projected_points(other_player, self.scoring_format)
                projected_diff = top_player_projected - other_projected
                
                # Calculate value: top_player_value - projected_points_difference
                calculated_value = top_player_score - projected_diff
                player_scores[other_player] = calculated_value
                
                print(f"{other_player.name} ({position}): calculated value: {calculated_value:.1f} (based on {top_player.name})")
        
        # Apply bench value adjustments to prioritize backup RBs/WRs over kickers
        adjusted_scores = {}
        for player, score in player_scores.items():
            # Get current roster needs to determine if player would be a starter or bench player
            current_roster = self.drafted_players.get(self._get_current_team(), [])
            roster_needs = self._get_roster_needs_for_simulation(current_roster)
            
            # Check if this player would be a starter or bench player
            would_be_starter = False
            if player.position in roster_needs and roster_needs[player.position] > 0:
                would_be_starter = True
            elif player.position in ['RB', 'WR', 'TE'] and roster_needs.get('FLEX', 0) > 0:
                would_be_starter = True
            
            # Apply bench value bonus for backup RBs/WRs/TEs over kickers
            if not would_be_starter and player.position in ['RB', 'WR', 'TE']:
                # This player would be a bench player - add bench value bonus
                bench_bonus = self._calculate_bench_value_for_player(player, current_roster)
                adjusted_score = score + bench_bonus
                print(f"{player.name} ({player.position}): bench bonus {bench_bonus:.1f}, adjusted score: {adjusted_score:.1f}")
            elif player.position in ['K', 'DEF'] and not would_be_starter:
                # Kickers/DEF on bench have 0 value - heavily penalize
                adjusted_score = score - 1000  # Large penalty for backup K/DEF
                print(f"{player.name} ({player.position}): backup penalty, adjusted score: {adjusted_score:.1f}")
            else:
                adjusted_score = score
            
            adjusted_scores[player] = adjusted_score
        
        # Sort by adjusted value (highest first)
        sorted_players = sorted(adjusted_scores.items(), key=lambda x: x[1], reverse=True)
        
        for player, value in sorted_players[:num_recommendations]:
            # Use custom projections if available
            projected_points = self.get_player_projected_points(player, self.scoring_format)
            recommendations.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'adp': player.adp,
                'projected_points': projected_points,
                'expected_season_score': value
            })
        
        self._cached_recommendations = recommendations
        return recommendations
    
    def get_draft_recommendations(self, num_recommendations: int = 5) -> List[Dict]:
        """Get AI recommendations for the current pick using pure simulation."""
        # Check if draft is initialized
        if not self.draft_initialized:
            return []
        
        # Check if it's user's turn
        if not self.get_current_pick_info()["is_user_turn"]:
            return []
        
        # Return cached recommendations if available
        if self._cached_recommendations:
            return self._cached_recommendations[:num_recommendations]
        
        return []
    
    def _simulate_draft_with_player_simple(self, candidate_player: Player) -> float:
        """
        Pure simulation: Draft the candidate player, then use ADP for remaining picks.
        Calculate season score by summing projected points for optimal lineup each week.
        """
        # Save current state
        original_drafted_players = {team: roster.copy() for team, roster in self.drafted_players.items()}
        original_available_players = set(self.available_players)
        original_pick = self.current_pick
        
        # Setup sim state
        sim_drafted_players = {team: roster.copy() for team, roster in self.drafted_players.items()}
        sim_available_players = set(self.available_players)
        sim_pick = self.current_pick
        
        try:
            # Draft the candidate player
            team_name = self.teams[self.user_draft_position - 1]
            sim_drafted_players[team_name].append(candidate_player)
            sim_available_players.remove(candidate_player)
            sim_pick += 1
            
            # Simulate the rest of the draft using ADP
            while sim_pick <= self.total_picks:
                # Determine which team is picking using snake draft logic
                if sim_pick <= len(self.draft_order):
                    round_num, team_id = self.draft_order[sim_pick - 1]
                    team_name = self.teams[team_id - 1]
                else:
                    # Fallback for picks beyond draft order
                    team_index = (sim_pick - 1) % self.num_teams
                    team_name = self.teams[team_index]
                
                # Check if team has roster space
                team_roster = sim_drafted_players[team_name]
                total_roster_size = sum(self.roster_constraints.values())
                
                if len(team_roster) >= total_roster_size:
                    # Team is full, skip this pick
                    sim_pick += 1
                    continue
                
                # If it's the user's turn, use smart strategy
                if sim_pick <= len(self.draft_order):
                    round_num, team_id = self.draft_order[sim_pick - 1]
                    is_user_turn = (team_id == self.user_draft_position)
                else:
                    # Fallback for picks beyond draft order
                    team_index = (sim_pick - 1) % self.num_teams
                    is_user_turn = (team_index == self.user_draft_position - 1)
                
                if is_user_turn:
                    # Get roster needs for user team
                    roster_needs = self._get_roster_needs_for_simulation(team_roster)
                    
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
                                bench_value = self._calculate_bench_value_for_player(player, team_roster)
                                need_bonus = bench_value  # Use actual bench value
                            elif player.position in ['K', 'DEF']:
                                # Kickers/DEF on bench have 0 value - skip them
                                continue
                            else:
                                # QB on bench - moderate value
                                need_bonus = 20
                        else:
                            # No roster space available
                            continue
                        
                        # Calculate player value (ADP-based with some variance)
                        # Use custom projections if available
                        player_projected = self.get_player_projected_points(player, self.scoring_format)
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
            
            # Calculate season score for user team using the same method as get_user_roster_value
            user_roster = sim_drafted_players[self.teams[self.user_draft_position - 1]]
            season_score = self._calculate_roster_value_for_simulation(user_roster)
            
            return season_score
            
        except Exception as e:
            print(f"Error in simulation for {candidate_player.name}: {e}")
            return 0.0
        finally:
            # Restore original state
            self.drafted_players = original_drafted_players
            self.available_players = list(original_available_players)
            self.current_pick = original_pick
    
    def _get_roster_needs_for_simulation(self, roster: List[Player]) -> Dict[str, int]:
        """Get roster needs for simulation purposes, considering bench constraints."""
        # Count current players by position
        position_counts = {'QB': 0, 'WR': 0, 'RB': 0, 'TE': 0, 'K': 0, 'DEF': 0}
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
            'DEF': 0
        }
        
        # Sort players by projected points to prioritize starters
        sorted_roster = sorted(roster, key=lambda p: p.projected_points, reverse=True)
        
        for player in sorted_roster:
            pos = player.position
            
            # Check if we can fill a starting position
            if pos in filled_positions and filled_positions[pos] < self.roster_constraints.get(pos, 0):
                # Fill starting position
                filled_positions[pos] += 1
                starters.append(player)
            elif pos in ['RB', 'WR', 'TE'] and filled_positions['FLEX'] < self.roster_constraints.get('FLEX', 0):
                # Fill FLEX position
                filled_positions['FLEX'] += 1
                starters.append(player)
            else:
                # Player goes to bench
                bench_players.append(player)
        
        # Calculate total bench spots used (only actual bench players)
        total_bench_used = len(bench_players)
        
        max_bench = self.roster_constraints.get('BN', 6)
        bench_available = max(0, max_bench - total_bench_used)
        
        # Calculate needs for starting positions
        needs = {
            'QB': max(0, self.roster_constraints.get('QB', 1) - position_counts['QB']),
            'WR': max(0, self.roster_constraints.get('WR', 2) - position_counts['WR']),
            'RB': max(0, self.roster_constraints.get('RB', 2) - position_counts['RB']),
            'TE': max(0, self.roster_constraints.get('TE', 1) - position_counts['TE']),
            'K': max(0, self.roster_constraints.get('K', 1) - position_counts['K']),
            'DEF': max(0, self.roster_constraints.get('DEF', 1) - position_counts['DEF'])
        }
        
        # If bench is full, prioritize filling remaining roster slots
        if bench_available == 0:
            # Only allow drafting players that fill remaining roster slots
            return {pos: count for pos, count in needs.items() if count > 0}
        
        # If bench has space, allow drafting any position
        # Add bench availability to the needs calculation
        needs['BN'] = bench_available
        
        return needs
    
    def _calculate_bench_value(self, roster: List[Player]) -> float:
        """
        Calculate the insurance value of bench players based on position and slot position.
        
        Base percentages by position:
        - RB: 30% (with 7.5% drop-off per RB slot)
        - WR: 27.5% (with 7.5% drop-off per WR slot) 
        - TE: 10% (with 10% drop-off per TE slot)
        - QB: 15% (with 15% drop-off per QB slot)
        - K/DEF: 0% (never recommend backup)
        
        Drop-offs are position-specific - adding a WR doesn't affect RB bench value.
        """
        if not roster:
            return 0.0
        
        # Separate starters from bench players
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
            'DEF': 0
        }
        
        # Sort players by projected points to prioritize starters
        sorted_roster = sorted(roster, key=lambda p: self.get_player_projected_points(p), reverse=True)
        
        for player in sorted_roster:
            pos = player.position
            
            # Check if we can fill a starting position
            if pos in filled_positions and filled_positions[pos] < self.roster_constraints.get(pos, 0):
                # Fill starting position
                filled_positions[pos] += 1
                starters.append(player)
            elif pos in ['RB', 'WR', 'TE'] and filled_positions['FLEX'] < self.roster_constraints.get('FLEX', 0):
                # Fill FLEX position
                filled_positions['FLEX'] += 1
                starters.append(player)
            else:
                # Player goes to bench
                bench_players.append(player)
        
        # Check if bench is full
        max_bench = self.roster_constraints.get('BN', 6)
        if len(bench_players) >= max_bench:
            # Bench is full - only players who start contribute value
            return 0.0
        
        # Calculate bench value only if bench has space
        bench_value = 0.0
        position_counts = {'QB': 0, 'WR': 0, 'RB': 0, 'TE': 0}
        
        for player in bench_players:
            pos = player.position
            if pos in position_counts:
                position_counts[pos] += 1
                slot_position = position_counts[pos]
                
                # Get base percentage and drop-off for position
                base_percentages = {
                    'RB': 30,
                    'WR': 27.5,
                    'TE': 10,
                    'QB': 15
                }
                
                drop_offs = {
                    'RB': 7.5,
                    'WR': 7.5,
                    'TE': 10,
                    'QB': 15
                }
                
                base_percent = base_percentages.get(pos, 0)
                drop_off = drop_offs.get(pos, 0)
                
                # Apply position-specific slot drop-off, minimum 0%
                effective_percent = max(0, base_percent - (slot_position - 1) * drop_off)
                
                # Calculate bench value for this player using correct projected points
                player_projected = self.get_player_projected_points(player)
                player_bench_value = (player_projected * effective_percent) / 100
                
                bench_value += player_bench_value
        
        return bench_value

    def _calculate_bench_value_for_player(self, player: Player, team_roster: list) -> float:
        """Calculate the bench value for a player based on their position and bench depth (new rules)."""
        if player.position in ['K', 'DEF']:
            return 0.0
        
        # Count current bench players by position
        bench_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
        for p in team_roster:
            if p.position in bench_counts:
                bench_counts[p.position] += 1
        bench_depth = bench_counts.get(player.position, 0)
        
        if player.position in ['RB', 'WR']:
            if bench_depth == 0:
                return player.projected_points * 0.30
            elif bench_depth == 1:
                return player.projected_points * 0.22
            elif bench_depth == 2:
                return player.projected_points * 0.14
            else:
                return player.projected_points * 0.05
        elif player.position == 'QB':
            if bench_depth == 0:
                return player.projected_points * 0.13
            else:
                return player.projected_points * 0.03
        elif player.position == 'TE':
            if bench_depth == 0:
                return player.projected_points * 0.10
            else:
                return 0.0
        else:
            return 0.0

    def get_user_roster_value(self) -> float:
        """Calculate the user's current roster value (starters + bench, using bench value rules)."""
        team_name = self.teams[self.user_draft_position - 1]
        roster = self.drafted_players[team_name]
        if not roster:
            return 0.0
        
        # Assign starters and bench as in optimal lineup calculation
        starters = []
        bench = []
        filled = {k: 0 for k in self.roster_constraints}
        sorted_players = sorted(roster, key=lambda p: p.projected_points, reverse=True)
        
        # Fill required positions
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            needed = self.roster_constraints.get(pos, 0)
            for p in sorted_players:
                if p.position == pos and filled[pos] < needed and p not in starters:
                    starters.append(p)
                    filled[pos] += 1
        
        # Fill FLEX
        needed = self.roster_constraints.get('FLEX', 0)
        for p in sorted_players:
            if p.position in ['RB', 'WR', 'TE'] and filled['FLEX'] < needed and p not in starters:
                starters.append(p)
                filled['FLEX'] += 1
        
        # Everything else is bench
        for p in sorted_players:
            if p not in starters:
                bench.append(p)
        
        # Calculate value
        value = sum(p.projected_points for p in starters)
        
        # For bench, use new bench value logic
        bench_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
        for p in bench:
            # For each bench player, pass only the already-bench players of that position to get correct depth
            same_pos_bench = [x for x in bench if x.position == p.position][:bench_counts[p.position]]
            value += self._calculate_bench_value_for_player(p, same_pos_bench)
            bench_counts[p.position] += 1
        
        return value
    
    def _calculate_roster_value_for_simulation(self, roster: List[Player]) -> float:
        """Calculate roster value for simulation using the same method as get_user_roster_value."""
        if not roster:
            return 0.0
        
        # Assign starters and bench as in optimal lineup calculation
        starters = []
        bench = []
        filled = {k: 0 for k in self.roster_constraints}
        sorted_players = sorted(roster, key=lambda p: p.projected_points, reverse=True)
        
        # Fill required positions
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            needed = self.roster_constraints.get(pos, 0)
            for p in sorted_players:
                if p.position == pos and filled[pos] < needed and p not in starters:
                    starters.append(p)
                    filled[pos] += 1
        
        # Fill FLEX
        needed = self.roster_constraints.get('FLEX', 0)
        for p in sorted_players:
            if p.position in ['RB', 'WR', 'TE'] and filled['FLEX'] < needed and p not in starters:
                starters.append(p)
                filled['FLEX'] += 1
        
        # Everything else is bench
        for p in sorted_players:
            if p not in starters:
                bench.append(p)
        
        # Calculate value
        value = sum(p.projected_points for p in starters)
        
        # For bench, use new bench value logic
        bench_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
        for p in bench:
            # For each bench player, pass only the already-bench players of that position to get correct depth
            same_pos_bench = [x for x in bench if x.position == p.position][:bench_counts[p.position]]
            value += self._calculate_bench_value_for_player(p, same_pos_bench)
            bench_counts[p.position] += 1
        
        return value
    
    def _calculate_season_score(self, roster: List[Player]) -> float:
        """Calculate season score by summing optimal weekly lineups plus bench value."""
        if not roster:
            return 0.0
        
        # Calculate weekly lineup scores
        weekly_score_total = 0.0
        
        # Simulate each week (assuming 17 weeks)
        for week in range(1, 18):
            weekly_score = self._calculate_optimal_weekly_lineup(roster, week)
            weekly_score_total += weekly_score
        
        # Add bench value (insurance value for the season)
        bench_value = self._calculate_bench_value(roster)
        
        total_score = weekly_score_total + bench_value
        return total_score
    
    def _calculate_optimal_weekly_lineup(self, roster: List[Player], week: int) -> float:
        """Calculate optimal lineup for a specific week, properly handling roster constraints and bye weeks."""
        # Filter players who are available this week (not on bye)
        available_players = [p for p in roster if p.bye_week != week]
        
        if not available_players:
            return 0.0
        
        # Get weekly projections for available players
        weekly_scores = []
        for player in available_players:
            # Use projected points as a proxy for weekly performance
            # In a real implementation, you'd use actual weekly projections
            # Use custom projections if available
            player_projected = self.get_player_projected_points(player, self.scoring_format)
            weekly_score = player_projected / 17  # Divide season projection by weeks
            weekly_scores.append((player, weekly_score))
        
        # Sort by weekly score
        weekly_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Build optimal lineup based on roster constraints
        lineup = {
            'QB': [],
            'WR': [],
            'RB': [],
            'TE': [],
            'FLEX': [],
            'K': [],
            'DEF': []
        }
        
        # Track which players have been assigned to avoid duplicates
        assigned_players = set()
        
        # Fill required positions first (QB, K, DEF)
        for player, score in weekly_scores:
            if player.name in assigned_players:
                continue
                
            pos = player.position
            if pos in ['QB', 'K', 'DEF']:
                max_slots = self.roster_constraints.get(pos, 1)
                if len(lineup[pos]) < max_slots:
                    lineup[pos].append(score)
                    assigned_players.add(player.name)
        
        # Fill WR, RB, TE positions
        for player, score in weekly_scores:
            if player.name in assigned_players:
                continue
                
            pos = player.position
            if pos in ['WR', 'RB', 'TE']:
                max_slots = self.roster_constraints.get(pos, 1)
                if len(lineup[pos]) < max_slots:
                    lineup[pos].append(score)
                    assigned_players.add(player.name)
        
        # Fill FLEX position with best remaining WR/RB/TE
                    flex_slots = self.roster_constraints.get('FLEX', 0)
        for player, score in weekly_scores:
            if player.name in assigned_players:
                continue
                
            if player.position in ['WR', 'RB', 'TE'] and len(lineup['FLEX']) < flex_slots:
                lineup['FLEX'].append(score)
                assigned_players.add(player.name)
        
        # Sum up the lineup
        total = sum(sum(pos_scores) for pos_scores in lineup.values())
        return total
    
    def get_draft_status(self) -> Dict:
        """Get overall draft status."""
        # If draft is not initialized, return a status indicating it's not started
        if not self.draft_initialized:
            return {
                "total_picks": 0,
                "completed_picks": 0,
                "progress_percentage": 0,
                "is_draft_complete": False,
                "draft_completion_message": None,
                "current_pick_info": {
                    "status": "Draft Not Started",
                    "is_user_turn": False,
                    "round": 0,
                    "pick": 0,
                    "team_id": 0,
                    "team_name": "None"
                },
                "user_team": self.teams[self.user_draft_position - 1] if hasattr(self, 'user_draft_position') else "None",
                "user_roster": []
            }
        
        # Calculate total picks needed based on roster constraints
        total_picks_per_team = sum(self.roster_constraints.values())
        total_picks = total_picks_per_team * self.num_teams
        completed_picks = self.current_pick - 1
        
        # Check if draft is complete (when current pick exceeds total picks)
        is_draft_complete = self.current_pick > total_picks
        
        return {
            "total_picks": total_picks,
            "completed_picks": completed_picks,
            "progress_percentage": (completed_picks / total_picks * 100) if total_picks > 0 else 0,
            "is_draft_complete": is_draft_complete,
            "draft_completion_message": f"🎉 Draft Complete! All {total_picks_per_team} roster spots per team filled!" if is_draft_complete else None,
            "total_roster_spots": total_picks_per_team,
            "current_pick_info": self.get_current_pick_info(),
            "user_team": self.teams[self.user_draft_position - 1],
            "user_roster": self.drafted_players[self.teams[self.user_draft_position - 1]]
        }
    
    def export_draft_results(self) -> Dict:
        """Export complete draft results."""
        results = {
            "league_settings": {
                "num_teams": self.num_teams,
                "user_draft_position": self.user_draft_position,
                "roster_constraints": self.roster_constraints
            },
            "draft_history": [
                {
                    "round": entry["round"],
                    "pick": entry["pick"],
                    "team": entry["team_name"],
                    "player": {
                        "name": entry["player"].name,
                        "position": entry["player"].position,
                        "team": entry["player"].team,
                        "adp": entry["player"].adp,
                        "projected_points": entry["player"].projected_points
                    }
                }
                for entry in self.draft_history
            ],
            "final_rosters": {}
        }
        
        for team_name, roster in self.drafted_players.items():
            results["final_rosters"][team_name] = {
                "players": [
                    {
                        "name": p.name,
                        "position": p.position,
                        "team": p.team,
                        "adp": p.adp,
                        "projected_points": p.projected_points
                    }
                    for p in roster
                ],
                "projected_season_score": self.calculate_season_score(team_name)
            }
        
        return results
    
    def reset_draft(self):
        """Reset the draft to initial state."""
        self.current_round = 1
        self.current_pick = 1
        
        # Recalculate total picks based on roster constraints
        total_picks_per_team = sum(self.roster_constraints.values())
        self.total_picks = total_picks_per_team * self.num_teams
        
        # Regenerate draft order
        self._generate_draft_order()
        
        # Reset draft state
        self.drafted_players = {f'Team {i+1}': [] for i in range(self.num_teams)}
        self.available_players = set(self.players)
        self.draft_history = []
        
        # Clear cached recommendations
        self._cached_recommendations = []
        
        # Mark draft as initialized
        self.draft_initialized = True
        
        print(f"Draft reset: {self.num_teams} teams, {self.total_picks} total picks ({total_picks_per_team} per team)")
    
    def _get_current_team(self) -> str:
        """Get the current team name based on the current pick."""
        pick_info = self.get_current_pick_info()
        return pick_info["team_name"]
    
    def _advance_pick(self):
        """Advance to the next pick in the draft."""
        self.current_pick += 1
        
        # Update current round based on the draft order
        if self.current_pick <= len(self.draft_order):
            self.current_round = self.draft_order[self.current_pick - 1][0]
    
    def calculate_projected_points_from_raw_stats(self, player_name: str, scoring_format: str = 'ppr') -> float:
        """Calculate projected points from raw stats for a specific scoring format."""
        raw_stats = self.raw_stats.get(player_name, {})
        if not raw_stats:
            return 0.0
        
        # Find the player to get position
        player = None
        for p in self.players:
            if p.name == player_name:
                player = p
                break
        
        if not player:
            return 0.0
        
        position = player.position
        
        if position == 'QB':
            # QB scoring: 4 pts per TD pass, 1 pt per 25 yards, -2 per INT, 6 pts per rushing TD, 1 pt per 10 rushing yards
            passing_yards = raw_stats.get('passing_yards', 0)
            passing_tds = raw_stats.get('passing_tds', 0)
            interceptions = raw_stats.get('interceptions', 0)
            rushing_yards = raw_stats.get('rushing_yards', 0)
            rushing_tds = raw_stats.get('rushing_tds', 0)
            fumbles = raw_stats.get('fumbles', 0)
            
            points = (passing_yards / 25) + (passing_tds * 4) + (interceptions * -2) + \
                    (rushing_yards / 10) + (rushing_tds * 6) + (fumbles * -2)
            
        elif position in ['RB', 'WR', 'TE']:
            # RB/WR/TE scoring: 6 pts per TD, 1 pt per 10 yards, reception points based on format
            rushing_yards = raw_stats.get('rushing_yards', 0)
            rushing_tds = raw_stats.get('rushing_tds', 0)
            receiving_yards = raw_stats.get('receiving_yards', 0)
            receiving_tds = raw_stats.get('receiving_tds', 0)
            receptions = raw_stats.get('receptions', 0)
            fumbles = raw_stats.get('fumbles', 0)
            
            # Base points
            rushing_points = (rushing_yards / 10) + (rushing_tds * 6)
            receiving_points = (receiving_yards / 10) + (receiving_tds * 6)
            
            # Add reception points based on format
            if scoring_format == 'ppr':
                receiving_points += receptions * 1.0
            elif scoring_format == 'half-ppr':
                receiving_points += receptions * 0.5
            # standard: no reception points
            
            points = rushing_points + receiving_points + (fumbles * -2)
            
        elif position == 'K':
            # Kicker scoring: 3 pts per FG, 1 pt per XP
            field_goals = raw_stats.get('field_goals', 0)
            extra_points = raw_stats.get('extra_points', 0)
            
            points = (field_goals * 3) + extra_points
            
        elif position == 'DEF':
            # Defense scoring: varies by league, using standard scoring
            sacks = raw_stats.get('sacks', 0)
            interceptions = raw_stats.get('interceptions', 0)
            fumble_recoveries = raw_stats.get('fumble_recoveries', 0)
            touchdowns = raw_stats.get('touchdowns', 0)
            safeties = raw_stats.get('safeties', 0)
            points_allowed = raw_stats.get('points_allowed', 0)
            
            points = (sacks * 1) + (interceptions * 2) + (fumble_recoveries * 2) + \
                    (touchdowns * 6) + (safeties * 2)
            
            # Points allowed bonuses
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
        else:
            points = 0.0
        
        return points
    


# Example usage and testing
if __name__ == "__main__":
    # Initialize the assistant
    assistant = FantasyDraftAssistant("Downloads/WeeklyFantasyFootballCheatingSheet.csv")
    
    # Print some available players
    print("\nTop 10 available players by ADP:")
    available = assistant.get_available_players()
    for i, player in enumerate(available[:10]):
        print(f"{i+1}. {player}")
    
    # Get current pick info
    print(f"\nCurrent pick info: {assistant.get_current_pick_info()}")
    
    # Get roster needs for user team
    user_team = assistant.teams[assistant.user_draft_position - 1]
    print(f"\nRoster needs for {user_team}: {assistant.get_roster_needs(user_team)}")
    
    # Get draft recommendations
    recommendations = assistant.get_draft_recommendations()
    print(f"\nTop 5 draft recommendations:")
    for i, rec in enumerate(recommendations):
        print(f"{i+1}. {rec['name']} ({rec['position']}) - Expected Score: {rec['expected_season_score']:.1f}")
        print(f"   Reason: {rec['roster_need']} need(s) for {rec['position']}") 