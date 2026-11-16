# Fabric Notebook Code: 01_Ingestion_Setup_Bronze

"""
NBA Live Data Platform - Phase 3
Notebook 1: Setup & Bronze Layer Ingestion

Purpose:
- Initialize lakehouse and schemas
- Create Bronze layer tables
- Implement NBA API ingestion logic with error handling
- Store raw data for audit trail and reprocessing

Production Grade Features:
- Explicit schema definition (no inferSchema)
- Data quality validation
- Metadata tracking (ingestion_timestamp, source)
- Idempotent operations (safe for re-execution)
- Comprehensive error handling and logging
- Delta Lake format with partitioning
"""

# Cell 1: Configure Spark Session and Imports
# ============================================



# Import required libraries
from pyspark.sql import functions as F, types as T
from pyspark.sql.types import *
from datetime import date, datetime
import logging
import json
import math
import time
import uuid
import requests
from typing import Optional, Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('nba_ingestion')

# Get notebook context and workspace info
context = notebookutils.runtime.context
workspace_id = context["currentWorkspaceId"]
workspace_name = context.get("workspaceName", "UNKNOWN")
is_pipeline = context["isForPipeline"]

logger.info(f"Notebook started in workspace: {workspace_name} (ID: {workspace_id})")
logger.info(f"Running from pipeline: {is_pipeline}")

def lakehouse_is_schema_enabled() -> bool:
    probe_schema = f"_schema_probe_{uuid.uuid4().hex}"
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {probe_schema}")
        spark.sql(f"DROP SCHEMA IF EXISTS {probe_schema}")
        return True
    except Exception as exc:
        if "Feature not supported on Apache Spark in Microsoft Fabric" in str(exc):
            return False
        raise


SCHEMA_ENABLED = lakehouse_is_schema_enabled()
if SCHEMA_ENABLED:
    for schema_name in ("bronze", "silver", "gold"):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")


def lakehouse_table_name(layer: str, table: str) -> str:
    if layer not in {"bronze", "silver", "gold"} or not table.isidentifier():
        raise ValueError(f"Invalid lakehouse table name: {layer}.{table}")
    return f"{layer}.{table}" if SCHEMA_ENABLED else f"{layer}_{table}"


BRONZE_GAMES_TABLE = lakehouse_table_name("bronze", "games_raw")
BRONZE_PLAYER_STATS_TABLE = lakehouse_table_name("bronze", "player_stats_raw")
BRONZE_SHOTS_TABLE = lakehouse_table_name("bronze", "shots_raw")
EXECUTION_LOG_TABLE = lakehouse_table_name("bronze", "execution_log")

execution_log_schema = StructType([
    StructField("run_id", StringType(), False),
    StructField("notebook_name", StringType(), False),
    StructField("start_time", TimestampType(), False),
    StructField("end_time", TimestampType(), False),
    StructField("status", StringType(), False),
    StructField("games_processed", IntegerType(), False),
    StructField("player_records_ingested", IntegerType(), False),
    StructField("shots_ingested", IntegerType(), False),
    StructField("error_message", StringType(), True),
    StructField("processed_dates", StringType(), True),
])


def write_execution_log(
    run_id: str,
    notebook_name: str,
    start_time: datetime,
    status: str,
    games_processed: int = 0,
    player_records_ingested: int = 0,
    shots_ingested: int = 0,
    error_message: Optional[str] = None,
    processed_dates: Optional[str] = None,
) -> None:
    row = (
        run_id,
        notebook_name,
        start_time,
        datetime.utcnow(),
        status,
        games_processed,
        player_records_ingested,
        shots_ingested,
        error_message,
        processed_dates,
    )
    spark.createDataFrame([row], execution_log_schema).write \
        .format("delta").mode("append").saveAsTable(EXECUTION_LOG_TABLE)


# Cell 2: Define Bronze Layer Schemas
# ====================================

# Schema for games_raw - preserves original API response
games_raw_schema = StructType([
    StructField("game_id", StringType(), False),
    StructField("game_date", DateType(), False),
    StructField("game_status", IntegerType(), True),
    StructField("game_status_text", StringType(), True),
    StructField("season", IntegerType(), True),
    StructField("game_type", StringType(), True),
    StructField("home_team_id", IntegerType(), True),
    StructField("home_team_name", StringType(), True),
    StructField("away_team_id", IntegerType(), True),
    StructField("away_team_name", StringType(), True),
    StructField("home_score", IntegerType(), True),
    StructField("away_score", IntegerType(), True),
    StructField("quarter", IntegerType(), True),
    StructField("game_clock", StringType(), True),
    StructField("arena_name", StringType(), True),
    StructField("arena_city", StringType(), True),
    StructField("api_response_json", StringType(), True),  # Full JSON for audit
    StructField("ingestion_timestamp", TimestampType(), False),
    StructField("source_system", StringType(), False),
    StructField("is_processed", BooleanType(), False)
])

# Schema for player_stats_raw
player_stats_raw_schema = StructType([
    StructField("game_id", StringType(), False),
    StructField("game_date", DateType(), False),
    StructField("player_id", IntegerType(), True),
    StructField("player_name", StringType(), True),
    StructField("team_id", IntegerType(), True),
    StructField("team_name", StringType(), True),
    StructField("position", StringType(), True),
    StructField("minutes_played", DoubleType(), True),
    StructField("field_goals_made", IntegerType(), True),
    StructField("field_goals_attempted", IntegerType(), True),
    StructField("three_pointers_made", IntegerType(), True),
    StructField("three_pointers_attempted", IntegerType(), True),
    StructField("free_throws_made", IntegerType(), True),
    StructField("free_throws_attempted", IntegerType(), True),
    StructField("rebounds", IntegerType(), True),
    StructField("assists", IntegerType(), True),
    StructField("steals", IntegerType(), True),
    StructField("blocks", IntegerType(), True),
    StructField("turnovers", IntegerType(), True),
    StructField("fouls", IntegerType(), True),
    StructField("points", IntegerType(), True),
    StructField("plus_minus", IntegerType(), True),
    StructField("api_response_json", StringType(), True),
    StructField("ingestion_timestamp", TimestampType(), False),
    StructField("source_system", StringType(), False)
])

# Schema for shots_raw
shots_raw_schema = StructType([
    StructField("game_id", StringType(), False),
    StructField("game_date", DateType(), False),
    StructField("player_id", IntegerType(), True),
    StructField("player_name", StringType(), True),
    StructField("team_id", IntegerType(), True),
    StructField("team_name", StringType(), True),
    StructField("shot_number", IntegerType(), True),
    StructField("shot_type", StringType(), True),
    StructField("x_coordinate", DoubleType(), True),
    StructField("y_coordinate", DoubleType(), True),
    StructField("shot_distance", DoubleType(), True),
    StructField("is_made", BooleanType(), True),
    StructField("quarter", IntegerType(), True),
    StructField("minutes_remaining", IntegerType(), True),
    StructField("seconds_remaining", IntegerType(), True),
    StructField("api_response_json", StringType(), True),
    StructField("ingestion_timestamp", TimestampType(), False),
    StructField("source_system", StringType(), False)
])

logger.info("Bronze schemas defined successfully")
print("✅ Bronze schemas defined")


# Cell 3: Verify Lakehouse Connection
# ===================================

spark.sql("SELECT 1 AS test_connection").collect()
logger.info("Connected to default lakehouse")
print("Lakehouse connected (schema-enabled: {})".format(SCHEMA_ENABLED))


# Cell 4: Create Bronze Tables
# ===========================

def create_empty_table(table_name: str, schema: StructType, partition_columns=None):
    if spark.catalog.tableExists(table_name):
        return
    writer = spark.createDataFrame([], schema).write.format("delta").mode("errorifexists")
    if partition_columns:
        writer = writer.partitionBy(*partition_columns)
    writer.saveAsTable(table_name)


def create_bronze_tables():
    create_empty_table(BRONZE_GAMES_TABLE, games_raw_schema, ["game_date"])
    create_empty_table(BRONZE_PLAYER_STATS_TABLE, player_stats_raw_schema, ["game_date"])
    create_empty_table(BRONZE_SHOTS_TABLE, shots_raw_schema, ["game_date"])
    create_empty_table(EXECUTION_LOG_TABLE, execution_log_schema)
    logger.info("Bronze tables created or verified")
    print(f"Bronze tables ready (schema-enabled: {SCHEMA_ENABLED})")


create_bronze_tables()


# Cell 5: NBA API Ingestion Functions
# ===================================

def get_nba_api_games(game_date: str) -> List[Dict[str, Any]]:
    logger.info(f"Fetching games for date: {game_date}")
    payload = request_nba_api(
        "scoreboardv3",
        {"GameDate": game_date, "LeagueID": "00"},
    )
    scoreboard = payload.get("scoreboard")
    if not isinstance(scoreboard, dict) or not isinstance(scoreboard.get("games"), list):
        raise ValueError("NBA scoreboardv3 response is missing scoreboard.games")

    games = []
    for game in scoreboard["games"]:
        if not isinstance(game, dict):
            raise ValueError("NBA scoreboardv3 contains an invalid game")
        home_team = game.get("homeTeam")
        away_team = game.get("awayTeam")
        if not isinstance(home_team, dict) or not isinstance(away_team, dict):
            raise ValueError("NBA scoreboardv3 game is missing team data")
        game_id = str(game.get("gameId") or "").strip()
        home_name = " ".join(
            part for part in (home_team.get("teamCity"), home_team.get("teamName")) if part
        ) or None
        away_name = " ".join(
            part for part in (away_team.get("teamCity"), away_team.get("teamName")) if part
        ) or None
        games.append({
            "GAME_ID": game_id,
            "GAME_DATE_EST": scoreboard.get("gameDate") or game_date,
            "GAME_STATUS_ID": game.get("gameStatus"),
            "GAME_STATUS_TEXT": game.get("gameStatusText"),
            "SEASON": game.get("season"),
            "GAME_TYPE": game_type_from_id(game_id),
            "HOME_TEAM_ID": safe_int(home_team.get("teamId")),
            "HOME_TEAM_NAME": home_name,
            "HOME_TEAM_SCORE": home_team.get("score"),
            "VISITOR_TEAM_ID": safe_int(away_team.get("teamId")),
            "VISITOR_TEAM_NAME": away_name,
            "VISITOR_TEAM_SCORE": away_team.get("score"),
            "QUARTER": game.get("period"),
            "GAME_CLOCK": game.get("gameClock"),
            "ARENA_NAME": game.get("arenaName"),
            "ARENA_CITY": home_team.get("teamCity"),
            "API_RESPONSE": game,
        })

    logger.info(f"Fetched {len(games)} games for {game_date}")
    return games


NBA_API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json, text/plain, */*",
}


def request_nba_api(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    for attempt in range(2):
        try:
            response = requests.get(
                f"https://stats.nba.com/stats/{endpoint}",
                params=params,
                headers=NBA_API_HEADERS,
                timeout=(10, 60),
            )
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt == 1:
                logger.exception(f"NBA API {endpoint} unavailable after two attempts")
                raise
            logger.warning(f"NBA API {endpoint} connection failed; retrying once in 5 seconds")
            time.sleep(5)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected NBA API response for {endpoint}")
    return payload


def get_result_set(payload: Dict[str, Any], result_name: str) -> List[Dict[str, Any]]:
    result_sets = payload.get("resultSets", payload.get("resultSet", []))
    if isinstance(result_sets, dict):
        result_sets = [result_sets]
    for result_set in result_sets:
        if result_set.get("name") == result_name:
            headers = result_set.get("headers", [])
            return [dict(zip(headers, row)) for row in result_set.get("rowSet", [])]
    raise ValueError(f"NBA API response is missing result set '{result_name}'")


def safe_int(value: Any) -> Optional[int]:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
        return None if math.isnan(number) else int(number)
    except (TypeError, ValueError, OverflowError):
        return None


def safe_float(value: Any) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
        return None if math.isnan(number) else number
    except (TypeError, ValueError, OverflowError):
        return None


def parse_nba_date(value: Any, fallback: Optional[date] = None) -> Optional[date]:
    if value is None or str(value).strip() == "":
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    normalized = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return datetime.strptime(normalized[:10], "%Y-%m-%d").date()


def nba_season_year(value: Any, game_date: date) -> int:
    season = str(value or "").strip()
    if len(season) >= 4 and season[:4].isdigit():
        return int(season[:4]) if "-" in season else int(season[-4:])
    return game_date.year if game_date.month >= 10 else game_date.year - 1


def game_type_from_id(game_id: str) -> str:
    return {
        "001": "PRESEASON",
        "002": "REGULAR",
        "003": "ALL_STAR",
        "004": "PLAYOFFS",
    }.get(game_id[:3], "UNKNOWN")


def parse_minutes(value: Any) -> Optional[float]:
    if value is None or str(value).strip() in {"", "0"}:
        return 0.0 if value == "0" else None
    text = str(value).strip()
    if ":" in text:
        minutes, seconds = text.split(":", 1)
        return float(minutes) + float(seconds) / 60
    return safe_float(text)


def get_nba_api_player_stats(
    game_id: str,
    game_date: date,
    team_names: Dict[int, str],
) -> List[Dict[str, Any]]:
    payload = request_nba_api("boxscoretraditionalv2", {
        "GameID": game_id,
        "StartPeriod": 0,
        "EndPeriod": 10,
        "StartRange": 0,
        "EndRange": 0,
        "RangeType": 0,
    })
    records = get_result_set(payload, "PlayerStats")
    now = datetime.utcnow()
    result = []
    for record in records:
        team_id = safe_int(record.get("TEAM_ID"))
        result.append({
            "game_id": game_id,
            "game_date": parse_nba_date(record.get("GAME_DATE"), game_date),
            "player_id": safe_int(record.get("PLAYER_ID")),
            "player_name": record.get("PLAYER_NAME"),
            "team_id": team_id,
            "team_name": record.get("TEAM_NAME") or team_names.get(team_id),
            "position": record.get("START_POSITION"),
            "minutes_played": parse_minutes(record.get("MIN")),
            "field_goals_made": safe_int(record.get("FGM")),
            "field_goals_attempted": safe_int(record.get("FGA")),
            "three_pointers_made": safe_int(record.get("FG3M")),
            "three_pointers_attempted": safe_int(record.get("FG3A")),
            "free_throws_made": safe_int(record.get("FTM")),
            "free_throws_attempted": safe_int(record.get("FTA")),
            "rebounds": safe_int(record.get("REB")),
            "assists": safe_int(record.get("AST")),
            "steals": safe_int(record.get("STL")),
            "blocks": safe_int(record.get("BLK")),
            "turnovers": safe_int(record.get("TO")),
            "fouls": safe_int(record.get("PF")),
            "points": safe_int(record.get("PTS")),
            "plus_minus": safe_int(record.get("PLUS_MINUS")),
            "api_response_json": json.dumps(record),
            "ingestion_timestamp": now,
            "source_system": "NBA_API_BoxScoreTraditionalV2",
        })
    return result


def get_nba_api_shots(
    game_id: str,
    game_date: date,
    game_type: str,
    team_names: Dict[int, str],
) -> List[Dict[str, Any]]:
    season_type = {
        "PRESEASON": "Pre Season",
        "ALL_STAR": "All Star",
        "PLAYOFFS": "Playoffs",
    }.get(game_type, "Regular Season")
    payload = request_nba_api("shotchartdetail", {
        "ContextMeasure": "FGA",
        "GameID": game_id,
        "LeagueID": "00",
        "PlayerID": "0",
        "Season": f"{game_date.year if game_date.month >= 10 else game_date.year - 1}-{str(game_date.year + (1 if game_date.month >= 10 else 0))[-2:]}",
        "SeasonType": season_type,
        "TeamID": "0",
    })
    records = get_result_set(payload, "Shot_Chart_Detail")
    now = datetime.utcnow()
    result = []
    for record in records:
        made = safe_int(record.get("SHOT_MADE_FLAG"))
        result.append({
            "game_id": game_id,
            "game_date": parse_nba_date(record.get("GAME_DATE"), game_date),
            "player_id": safe_int(record.get("PLAYER_ID")),
            "player_name": record.get("PLAYER_NAME"),
            "team_id": safe_int(record.get("TEAM_ID")),
            "team_name": record.get("TEAM_NAME") or team_names.get(
                safe_int(record.get("TEAM_ID"))
            ),
            "shot_number": safe_int(record.get("GAME_EVENT_ID")),
            "shot_type": record.get("SHOT_TYPE") or record.get("ACTION_TYPE"),
            "x_coordinate": safe_float(record.get("LOC_X")),
            "y_coordinate": safe_float(record.get("LOC_Y")),
            "shot_distance": safe_float(record.get("SHOT_DISTANCE")),
            "is_made": None if made is None else made != 0,
            "quarter": safe_int(record.get("PERIOD")),
            "minutes_remaining": safe_int(record.get("MINUTES_REMAINING")),
            "seconds_remaining": safe_int(record.get("SECONDS_REMAINING")),
            "api_response_json": json.dumps(record),
            "ingestion_timestamp": now,
            "source_system": "NBA_API_ShotChartDetail",
        })
    return result


def transform_game_record(api_record: Dict[str, Any]) -> Dict[str, Any]:
    game_id = str(api_record.get("GAME_ID", "")).strip()
    game_date = parse_nba_date(api_record.get("GAME_DATE_EST"))
    if not game_id or game_date is None:
        raise ValueError("NBA scoreboard record is missing a game ID or valid game date")

    status = safe_int(api_record.get("GAME_STATUS_ID"))
    status_text = api_record.get("GAME_STATUS_TEXT") or {
        1: "NOT_STARTED",
        2: "IN_PROGRESS",
        3: "FINAL",
    }.get(status, "UNKNOWN")
    return {
        "game_id": game_id,
        "game_date": game_date,
        "game_status": status,
        "game_status_text": status_text,
        "season": nba_season_year(api_record.get("SEASON"), game_date),
        "game_type": api_record.get("GAME_TYPE", "UNKNOWN"),
        "home_team_id": safe_int(api_record.get("HOME_TEAM_ID")),
        "home_team_name": api_record.get("HOME_TEAM_NAME"),
        "away_team_id": safe_int(api_record.get("VISITOR_TEAM_ID")),
        "away_team_name": api_record.get("VISITOR_TEAM_NAME"),
        "home_score": safe_int(api_record.get("HOME_TEAM_SCORE")),
        "away_score": safe_int(api_record.get("VISITOR_TEAM_SCORE")),
        "quarter": safe_int(api_record.get("QUARTER")),
        "game_clock": api_record.get("GAME_CLOCK"),
        "arena_name": api_record.get("ARENA_NAME"),
        "arena_city": api_record.get("ARENA_CITY"),
        "api_response_json": json.dumps(api_record),
        "ingestion_timestamp": datetime.utcnow(),
        "source_system": "NBA_API_ScoreboardV3",
        "is_processed": False,
    }


def load_games_to_bronze(games: List[Dict[str, Any]]) -> int:
    if not games:
        return 0

    transformed_games = [transform_game_record(game) for game in games]
    return load_records_to_bronze(
        transformed_games,
        games_raw_schema,
        BRONZE_GAMES_TABLE,
        ["game_id", "game_date"],
        "new_games_staging",
    )


def load_records_to_bronze(
    records: List[Dict[str, Any]],
    schema: StructType,
    table_name: str,
    merge_keys: List[str],
    staging_view: str,
) -> int:
    if not records:
        return 0

    dataframe = spark.createDataFrame(records, schema=schema).dropDuplicates(merge_keys)
    invalid_key_condition = None
    for key in merge_keys:
        condition = F.col(key).isNull()
        invalid_key_condition = condition if invalid_key_condition is None else invalid_key_condition | condition
    if dataframe.filter(invalid_key_condition).limit(1).count():
        raise ValueError(f"Cannot merge {table_name}: one or more merge keys are null")

    record_count = dataframe.count()
    dataframe.createOrReplaceTempView(staging_view)
    join_condition = " AND ".join(
        f"target.{key} = source.{key}" for key in merge_keys
    )
    spark.sql(f"""
        MERGE INTO {table_name} AS target
        USING {staging_view} AS source
        ON {join_condition}
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)
    logger.info(f"Upserted {record_count} records into {table_name}")
    return record_count


# Cell 6: Execute Ingestion
# =========================

run_start_time = datetime.utcnow()
today = datetime.now().strftime("%Y-%m-%d")
run_id = f"ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
games_loaded = 0
player_stats_loaded = 0
shots_loaded = 0

try:
    games_data = get_nba_api_games(today)
    games_loaded = load_games_to_bronze(games_data)

    player_records = []
    shot_records = []
    for game in games_data:
        game_status = safe_int(game.get("GAME_STATUS_ID"))
        if game_status not in (2, 3):
            continue

        game_id = game["GAME_ID"]
        game_date = parse_nba_date(game.get("GAME_DATE_EST"))
        if game_date is None:
            raise ValueError(f"Game {game_id} has no valid date")

        time.sleep(2)
        team_names = {
            game.get("HOME_TEAM_ID"): game.get("HOME_TEAM_NAME"),
            game.get("VISITOR_TEAM_ID"): game.get("VISITOR_TEAM_NAME"),
        }
        player_records.extend(
            get_nba_api_player_stats(game_id, game_date, team_names)
        )
        time.sleep(2)
        shot_records.extend(
            get_nba_api_shots(
                game_id,
                game_date,
                game.get("GAME_TYPE", "UNKNOWN"),
                team_names,
            )
        )

    player_stats_loaded = load_records_to_bronze(
        player_records,
        player_stats_raw_schema,
        BRONZE_PLAYER_STATS_TABLE,
        ["game_id", "player_id"],
        "new_player_stats_staging",
    )
    shots_loaded = load_records_to_bronze(
        shot_records,
        shots_raw_schema,
        BRONZE_SHOTS_TABLE,
        ["game_id", "shot_number"],
        "new_shots_staging",
    )

    write_execution_log(
        run_id,
        "01_Ingestion_Setup_Bronze",
        run_start_time,
        "SUCCESS",
        games_loaded,
        player_stats_loaded,
        shots_loaded,
        processed_dates=today,
    )
    print(
        f"Ingestion complete: {games_loaded} games, "
        f"{player_stats_loaded} player rows, {shots_loaded} shots"
    )
except Exception as e:
    logger.exception(f"Fatal error during ingestion: {str(e)}")
    write_execution_log(
        run_id,
        "01_Ingestion_Setup_Bronze",
        run_start_time,
        "FAILED",
        games_loaded,
        player_stats_loaded,
        shots_loaded,
        error_message=str(e)[:4000],
        processed_dates=today,
    )
    raise




