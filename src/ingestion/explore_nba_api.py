"""
NBA API Exploration Script

This script explores the NBA API to:
1. Verify endpoint availability
2. Understand data structures
3. Identify required fields
4. Test connectivity and rate limits

Run this FIRST to validate the API before implementation.
"""

import requests
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional
import sys
import os

# Force UTF-8 encoding on Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# ============================================================================
# CONFIGURATION
# ============================================================================

# API configuration
BASE_URL = "https://stats.nba.com/stats"
TIMEOUT = 30
REQUEST_DELAY = 1.0  # Respectful delay between requests

# Headers (NBA.com requires User-Agent)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def make_request(endpoint: str, params: Dict[str, Any], description: str) -> Optional[Dict]:
    """
    Make an API request with error handling and logging.
    
    Args:
        endpoint: API endpoint (without base URL)
        params: Query parameters
        description: Human-readable description of what we're fetching
        
    Returns:
        Response JSON or None if failed
    """
    url = f"{BASE_URL}/{endpoint}"
    
    print(f"\n{'='*70}")
    print(f"[REQUEST] {description}")
    print(f"{'='*70}")
    print(f"Endpoint: {endpoint}")
    print(f"URL: {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    try:
        print(f"\n[FETCHING] ", end="", flush=True)
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        print("[SUCCESS]")
        
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response size: {len(json.dumps(data)) / 1024:.1f} KB")
        
        return data
        
    except requests.exceptions.Timeout:
        print("[TIMEOUT] API did not respond within 30 seconds")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] CONNECTION ERROR - {str(e)}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP ERROR - {e.response.status_code}")
        if e.response.status_code == 429:
            print("   Rate limited! NBA API is blocking requests.")
        return None
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return None
    finally:
        # Respectful delay
        print(f"[WAIT] Waiting {REQUEST_DELAY}s before next request...")
        time.sleep(REQUEST_DELAY)


def save_response(filename: str, data: Dict):
    """Save API response to file for reference."""
    filepath = f"data/sample/{filename}.json"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"\n[SAVED] {filepath}")
    except Exception as e:
        print(f"\n[WARNING] Could not save response: {str(e)}")


def analyze_response_structure(data: Dict, label: str, max_depth: int = 2):
    """Analyze and display the structure of an API response."""
    def analyze_dict(d: Dict, depth: int = 0, prefix: str = ""):
        if depth > max_depth:
            return
        
        indent = "  " * depth
        for key, value in d.items():
            if isinstance(value, dict):
                print(f"{indent}+- {key}: [dict with {len(value)} keys]")
                if depth < max_depth:
                    analyze_dict(value, depth + 1, prefix + "  ")
            elif isinstance(value, list) and len(value) > 0:
                first_item = value[0]
                if isinstance(first_item, dict):
                    print(f"{indent}+- {key}: [list of {len(value)} dicts]")
                    if depth < max_depth:
                        analyze_dict(first_item, depth + 1, prefix + "  ")
                else:
                    print(f"{indent}+- {key}: [list of {len(value)} items]")
            else:
                value_str = str(value)[:50] if value else "None"
                print(f"{indent}+- {key}: {type(value).__name__} = {value_str}")
    
    print(f"\n{'='*70}")
    print(f"[STRUCTURE] {label}")
    print(f"{'='*70}")
    analyze_dict(data)


def count_records(data: Dict) -> Dict[str, int]:
    """Count top-level records in response."""
    counts = {}
    for key, value in data.items():
        if isinstance(value, list):
            counts[key] = len(value)
    return counts


# ============================================================================
# PHASE 2A: NBA API EXPLORATION
# ============================================================================

def explore_scoreboard():
    """
    ENDPOINT 1: ScoreboardV3 (Games Schedule)
    Fetches games scheduled for a specific date.
    """
    print(f"\n\n{'#'*70}")
    print(f"# PHASE 2A.1: SCOREBOARD - Games for a Specific Date")
    print(f"{'#'*70}")
    
    # Use today's date
    today = datetime.now()
    game_date = today.strftime("%Y-%m-%d")
    
    print(f"\n[INFO] Exploring games scheduled for: {game_date}")
    print("\nThis endpoint returns:")
    print("  - List of games for the date")
    print("  - Game status (scheduled, in progress, final)")
    print("  - Teams, scores, quarter, time")
    
    params = {
        "GameDate": game_date,
        "LeagueID": "00",  # 00 = NBA, 10 = G League, 20 = WNBA
    }
    
    response = make_request("ScoreboardV3", params, "Games scheduled for today")
    
    if response:
        save_response("01_scoreboard", response)
        
        # Display structure
        analyze_response_structure(response, "ScoreboardV3 Response", max_depth=3)
        
        # Display record counts
        counts = count_records(response)
        print(f"\n{'='*70}")
        print("[COUNTS] Record Counts")
        print(f"{'='*70}")
        for key, count in counts.items():
            print(f"  {key}: {count} records")
        
        # Display sample game if available
        if "games" in response and len(response["games"]) > 0:
            game = response["games"][0]
            print(f"\n{'='*70}")
            print("[SAMPLE] Sample Game")
            print(f"{'='*70}")
            print(json.dumps(game, indent=2)[:1000])  # First 1000 chars
            
            # Extract key fields
            print(f"\n{'='*70}")
            print("[FIELDS] Key Fields Identified")
            print(f"{'='*70}")
            if "gameId" in game:
                print(f"  Game ID: {game['gameId']}")
            if "gameStatus" in game:
                print(f"  Status: {game['gameStatus']}")
            if "homeTeam" in game and "teamName" in game["homeTeam"]:
                print(f"  Home Team: {game['homeTeam']['teamName']}")
            if "awayTeam" in game and "teamName" in game["awayTeam"]:
                print(f"  Away Team: {game['awayTeam']['teamName']}")
            if "homeTeam" in game and "score" in game["homeTeam"]:
                print(f"  Home Score: {game['homeTeam']['score']}")
            if "awayTeam" in game and "score" in game["awayTeam"]:
                print(f"  Away Score: {game['awayTeam']['score']}")
    
    return response


def explore_boxscore(game_id: Optional[str] = None):
    """
    ENDPOINT 2: BoxScoreTraditionalV3 (Player Statistics)
    Fetches player statistics for a specific game.
    """
    print(f"\n\n{'#'*70}")
    print(f"# PHASE 2A.2: BOX SCORE - Player Statistics")
    print(f"{'#'*70}")
    
    if not game_id:
        print("\n[INFO] No game ID provided. Using a sample game ID for demonstration.")
        print("   (In production, we'll get game IDs from ScoreboardV3)")
        game_id = "0021501001"  # Sample game ID
    
    print(f"\nExploring box score for game: {game_id}")
    print("\nThis endpoint returns:")
    print("  - Player-level statistics (points, rebounds, assists, etc.)")
    print("  - Team totals")
    print("  - Shooting percentages and advanced stats")
    
    params = {
        "GameID": game_id,
        "LeagueID": "00",
    }
    
    response = make_request("BoxScoreTraditionalV3", params, f"Player stats for game {game_id}")
    
    if response:
        save_response("02_boxscore", response)
        
        # Display structure
        analyze_response_structure(response, "BoxScoreTraditionalV3 Response", max_depth=2)
        
        # Display record counts
        counts = count_records(response)
        print(f"\n{'='*70}")
        print("[COUNTS] Record Counts")
        print(f"{'='*70}")
        for key, count in counts.items():
            print(f"  {key}: {count} records")
        
        # Display sample player stat if available
        if "playerStatistics" in response and len(response["playerStatistics"]) > 0:
            stat = response["playerStatistics"][0]
            print(f"\n{'='*70}")
            print("[SAMPLE] Sample Player Statistic")
            print(f"{'='*70}")
            print(json.dumps(stat, indent=2)[:1500])
    
    return response


def explore_shotchart(game_id: Optional[str] = None):
    """
    ENDPOINT 3: ShotChartDetail (Shot-level Data)
    Fetches shot-by-shot data for a game.
    """
    print(f"\n\n{'#'*70}")
    print(f"# PHASE 2A.3: SHOT CHART - Shot-Level Data")
    print(f"{'#'*70}")
    
    if not game_id:
        print("\n[INFO] No game ID provided. Using a sample game ID for demonstration.")
        game_id = "0021501001"
    
    print(f"\nExploring shot chart for game: {game_id}")
    print("\nThis endpoint returns:")
    print("  - Individual shot attempts")
    print("  - Court coordinates (x, y)")
    print("  - Shot type and distance")
    print("  - Made/missed indicator")
    
    params = {
        "GameID": game_id,
        "LeagueID": "00",
    }
    
    response = make_request("ShotChartDetail", params, f"Shot chart for game {game_id}")
    
    if response:
        save_response("03_shotchart", response)
        
        # Display structure
        analyze_response_structure(response, "ShotChartDetail Response", max_depth=2)
        
        # Display record counts
        counts = count_records(response)
        print(f"\n{'='*70}")
        print("[COUNTS] Record Counts")
        print(f"{'='*70}")
        for key, count in counts.items():
            print(f"  {key}: {count} records")
        
        # Display sample shot if available
        if "shotChartData" in response and len(response["shotChartData"]) > 0:
            shot = response["shotChartData"][0]
            print(f"\n{'='*70}")
            print("[SAMPLE] Sample Shot")
            print(f"{'='*70}")
            print(json.dumps(shot, indent=2)[:1000])
    
    return response


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main exploration workflow."""
    
    print(f"\n{'='*70}")
    print(f" NBA API EXPLORATION - PHASE 2")
    print(f" Validating API Endpoints and Data Structures")
    print(f"{'='*70}")
    print(f"\nStart Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Request Delay: {REQUEST_DELAY}s (respectful rate limiting)")
    print(f"Timeout: {TIMEOUT}s")
    
    try:
        # Phase 2A.1: Explore Scoreboard
        scoreboard_data = explore_scoreboard()
        
        # Extract game ID from scoreboard if available
        game_id_for_stats = None
        if scoreboard_data and "games" in scoreboard_data and len(scoreboard_data["games"]) > 0:
            game = scoreboard_data["games"][0]
            if "gameId" in game:
                game_id_for_stats = game["gameId"]
                print(f"\n[OK] Found game ID from today's schedule: {game_id_for_stats}")
        
        # Phase 2A.2: Explore Box Score
        explore_boxscore(game_id_for_stats)
        
        # Phase 2A.3: Explore Shot Chart
        explore_shotchart(game_id_for_stats)
        
        # Summary
        print(f"\n\n{'='*70}")
        print(f"[SUCCESS] EXPLORATION COMPLETE")
        print(f"{'='*70}")
        print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nNext Steps:")
        print("  1. Review saved API responses in data/sample/")
        print("  2. Create data dictionary based on fields discovered")
        print("  3. Implement ingestion notebook in Fabric")
        print("  4. Build Bronze layer schema")
        print("\n[OK] Ready for Phase 3: Lakehouse Setup")
        
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Exploration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
