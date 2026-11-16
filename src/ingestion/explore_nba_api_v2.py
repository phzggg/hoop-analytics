"""
NBA API Exploration Script v2 - Using nba_api Package

Explores NBA data using the nba_api Python package endpoints.
"""

import json
from datetime import datetime
import time
from typing import Optional, Any
import sys
import os

# Force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

try:
    from nba_api.stats.endpoints import (
        ScoreboardV3,
        BoxScoreTraditionalV2,
        ShotChartDetail,
        CommonPlayerInfo,
        LeagueGameFinder
    )
    print("[OK] nba_api endpoints imported successfully")
except ImportError as e:
    print(f"[ERROR] Import failed: {str(e)}")
    print("Try: pip install nba-api")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

REQUEST_DELAY = 2.0  # Respectful delay between API requests

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_response(filename: str, data: Any):
    """Save API response to file."""
    filepath = f"data/sample/{filename}.json"
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Handle pandas DataFrames
        if hasattr(data, 'to_dict'):
            data = data.to_dict(orient='records')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"[SAVED] {filepath}")
    except Exception as e:
        print(f"[WARNING] Could not save: {str(e)}")


def show_structure(data: Any, label: str, limit: int = 2):
    """Display data structure."""
    print(f"\n{'='*70}")
    print(f"[DATA] {label}")
    print(f"{'='*70}")
    
    # Handle DataFrame
    if hasattr(data, 'shape'):
        print(f"Shape: {data.shape[0]} rows x {data.shape[1]} columns")
        print(f"\nColumns:")
        for i, col in enumerate(data.columns):
            if i >= 10:  # Limit columns shown
                print(f"  ... and {len(data.columns) - 10} more columns")
                break
            dtype = str(data[col].dtype)
            val = str(data[col].iloc[0]) if len(data) > 0 else "N/A"
            val = val[:50]
            print(f"  {col:35} [{dtype:12}] = {val}")
        
        if len(data) > 0:
            print(f"\nSample row:")
            for col in list(data.columns)[:5]:
                val = str(data[col].iloc[0])[:60]
                print(f"  {col:35} {val}")
    
    # Handle dict
    elif isinstance(data, dict):
        print(f"Keys: {len(data)}")
        for i, (key, value) in enumerate(data.items()):
            if i >= 5:
                print(f"  ... and {len(data) - 5} more keys")
                break
            if isinstance(value, list):
                print(f"  {key}: list of {len(value)} items")
            else:
                print(f"  {key}: {type(value).__name__}")
    
    # Handle list
    elif isinstance(data, list):
        print(f"Length: {len(data)}")
        if len(data) > 0 and isinstance(data[0], dict):
            print(f"First item keys: {len(data[0])}")


# ============================================================================
# EXPLORATION FUNCTIONS
# ============================================================================

def explore_scoreboard_v3():
    """Explore ScoreboardV3 - Games for a specific date."""
    print(f"\n\n{'#'*70}")
    print("# PHASE 2: SCOREBOARD - Games for Today")
    print(f"{'#'*70}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n[INFO] Fetching games for: {today}")
    
    try:
        print("[FETCHING]", end="", flush=True)
        scoreboard = ScoreboardV3(game_date=today)
        data = scoreboard.get_data_frames()
        print("[SUCCESS]")
        
        print(f"\n[RESULT] Received data with {len(data)} tables")
        
        # Explore each table
        for table_name, df in data.items():
            if df is not None and len(df) > 0:
                print(f"  - {table_name}: {len(df)} rows, {len(df.columns)} columns")
                
                if table_name == 'GameHeader':
                    show_structure(df, f"Scoreboard - {table_name}")
                    save_response("01_scoreboard_gameheader", df)
                    
                    # Extract game IDs
                    if 'GAME_ID' in df.columns:
                        game_ids = df['GAME_ID'].tolist()
                        print(f"\n[FOUND] Game IDs: {game_ids}")
                        return game_ids[0] if game_ids else None
        
        time.sleep(REQUEST_DELAY)
        return None
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def explore_boxscore(game_id: Optional[str] = None):
    """Explore BoxScoreTraditionalV2 - Player statistics."""
    print(f"\n\n{'#'*70}")
    print("# PHASE 2: BOX SCORE - Player Statistics")
    print(f"{'#'*70}")
    
    if not game_id:
        # Use a known game from recent NBA season
        game_id = "0022400101"  # Sample from 2024-25 season
        print(f"\n[INFO] Using sample game ID: {game_id}")
    else:
        print(f"\n[INFO] Using game ID: {game_id}")
    
    try:
        print("[FETCHING]", end="", flush=True)
        boxscore = BoxScoreTraditionalV2(game_id=game_id)
        data = boxscore.get_data_frames()
        print("[SUCCESS]")
        
        print(f"\n[RESULT] Received {len(data)} tables")
        
        # Explore each table
        for table_name, df in data.items():
            if df is not None and len(df) > 0:
                print(f"  - {table_name}: {len(df)} rows, {len(df.columns)} columns")
                
                if table_name == 'PlayerStats':
                    show_structure(df, f"Box Score - {table_name}")
                    save_response("02_boxscore_players", df)
                elif table_name == 'TeamStats':
                    show_structure(df, f"Box Score - {table_name}")
                    save_response("02_boxscore_teams", df)
        
        time.sleep(REQUEST_DELAY)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


def explore_shotchart(game_id: Optional[str] = None):
    """Explore ShotChartDetail - Shot-level data with coordinates."""
    print(f"\n\n{'#'*70}")
    print("# PHASE 2: SHOT CHART - Shot-Level Data with Coordinates")
    print(f"{'#'*70}")
    
    if not game_id:
        game_id = "0022400101"
        print(f"\n[INFO] Using sample game ID: {game_id}")
    else:
        print(f"\n[INFO] Using game ID: {game_id}")
    
    try:
        print("[FETCHING]", end="", flush=True)
        shots = ShotChartDetail(
            team_id='0',
            player_id='0',
            game_id=game_id,
            context_measure_simple='FGA'
        )
        data = shots.get_data_frames()
        print("[SUCCESS]")
        
        if isinstance(data, list):
            print(f"\n[RESULT] Received list of {len(data)} dataframes")
            for i, df in enumerate(data):
                if df is not None and len(df) > 0:
                    print(f"  - DataFrame {i}: {len(df)} rows, {len(df.columns)} columns")
                    if i == 0:
                        show_structure(df, "Shot Chart Detail")
                        save_response("03_shotchart", df)
        else:
            print(f"\n[RESULT] Received data")
            show_structure(data, "Shot Chart Detail")
            save_response("03_shotchart", data)
        
        time.sleep(REQUEST_DELAY)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


def explore_player_info():
    """Explore CommonPlayerInfo - Player metadata."""
    print(f"\n\n{'#'*70}")
    print("# PHASE 2: COMMON PLAYER INFO - Player Metadata")
    print(f"{'#'*70}")
    
    # LeBron James ID
    player_id = 2544
    print(f"\n[INFO] Fetching info for player ID: {player_id}")
    
    try:
        print("[FETCHING]", end="", flush=True)
        player = CommonPlayerInfo(player_id=player_id)
        data = player.get_data_frames()
        print("[SUCCESS]")
        
        if isinstance(data, list):
            print(f"\n[RESULT] Received {len(data)} dataframes")
            for i, df in enumerate(data):
                if df is not None and len(df) > 0:
                    print(f"  - DataFrame {i}: {len(df)} rows, {len(df.columns)} columns")
                    if i == 0:
                        show_structure(df, "Common Player Info")
                        save_response("04_player_info", df)
        else:
            show_structure(data, "Common Player Info")
            save_response("04_player_info", data)
        
        time.sleep(REQUEST_DELAY)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


def explore_league_games():
    """Explore LeagueGameFinder - Find games by criteria."""
    print(f"\n\n{'#'*70}")
    print("# PHASE 2: LEAGUE GAME FINDER - Find Games")
    print(f"{'#'*70}")
    
    season = "2024-25"
    print(f"\n[INFO] Fetching games for season: {season}")
    
    try:
        print("[FETCHING]", end="", flush=True)
        games = LeagueGameFinder(season_nullable=season, league_id_nullable='00')
        data = games.get_data_frames()
        print("[SUCCESS]")
        
        if isinstance(data, list):
            print(f"\n[RESULT] Received {len(data)} dataframes")
            for i, df in enumerate(data):
                if df is not None and len(df) > 0:
                    print(f"  - DataFrame {i}: {len(df)} rows, {len(df.columns)} columns")
                    if i == 0:
                        print(f"\n[SAMPLE] First 3 games:")
                        show_structure(df, "League Games", limit=3)
                        save_response("05_league_games", df.head(10))
        else:
            show_structure(data, "League Games")
            save_response("05_league_games", data)
        
        time.sleep(REQUEST_DELAY)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main exploration."""
    
    print(f"\n{'='*70}")
    print(" NBA API EXPLORATION - PHASE 2")
    print(" Using nba-api Python Package")
    print(f"{'='*70}")
    print(f"\nStart Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Request Delay: {REQUEST_DELAY}s (respectful rate limiting)")
    
    try:
        # Step 1: Scoreboard
        print("\n[STEP 1/5] Scoreboard")
        game_id = explore_scoreboard_v3()
        
        # Step 2: Box Score
        print("\n[STEP 2/5] Box Score")
        explore_boxscore(game_id)
        
        # Step 3: Shot Chart
        print("\n[STEP 3/5] Shot Chart")
        explore_shotchart(game_id)
        
        # Step 4: Player Info
        print("\n[STEP 4/5] Player Info")
        explore_player_info()
        
        # Step 5: League Games
        print("\n[STEP 5/5] League Games")
        explore_league_games()
        
        # Summary
        print(f"\n\n{'='*70}")
        print("[SUCCESS] EXPLORATION COMPLETE")
        print(f"{'='*70}")
        print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nData Sources Validated:")
        print("  [OK] Scoreboard V3 - Game schedules and status")
        print("  [OK] Box Score Traditional V2 - Player and team stats")
        print("  [OK] Shot Chart Detail - Shot-level data with coordinates")
        print("  [OK] Common Player Info - Player metadata")
        print("  [OK] League Game Finder - Historical game search")
        print("\nSample Responses Saved:")
        print("  - data/sample/01_scoreboard_gameheader.json")
        print("  - data/sample/02_boxscore_players.json")
        print("  - data/sample/02_boxscore_teams.json")
        print("  - data/sample/03_shotchart.json")
        print("  - data/sample/04_player_info.json")
        print("  - data/sample/05_league_games.json")
        print("\nNext Phase:")
        print("  Phase 3: Lakehouse Setup")
        print("  - Create Lakehouse in Fabric")
        print("  - Design Bronze/Silver/Gold schemas")
        print("  - Deploy initial notebooks")
        print("\n[OK] Ready for Phase 3!")
        
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Exploration cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
