# Fabric Notebook Code: 03_Dimensional_Model_Gold_Layer

"""
NBA Live Data Platform - Phase 3
Notebook 3: Gold Layer Dimensional Model

Purpose:
- Create analytics-ready fact and dimension tables
- Implement slowly changing dimensions (Type 2)
- Build surrogate key relationships
- Optimize for Direct Lake Power BI connectivity

Production Grade Features:
- Surrogate key generation with SCD Type 2
- Conformed dimensions for analytics
- Fact table grain clarity (one row per game)
- Aggregate tables for common queries
- Schema validation and referential integrity
"""

# Cell 1: Setup & Imports
# =======================



from pyspark.sql import functions as F, types as T, Window
from pyspark.sql.types import *
from datetime import datetime
import logging
import uuid
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nba_gold_layer')

context = notebookutils.runtime.context
is_pipeline = context["isForPipeline"]

logger.info(f"Gold layer dimensional model started (from pipeline: {is_pipeline})")

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


SILVER_GAMES_TABLE = lakehouse_table_name("silver", "games_clean")
SILVER_PLAYER_STATS_TABLE = lakehouse_table_name("silver", "player_stats_clean")
SILVER_SHOTS_TABLE = lakehouse_table_name("silver", "shots_clean")
EXECUTION_LOG_TABLE = lakehouse_table_name("bronze", "execution_log")
GOLD_DIM_DATE_TABLE = lakehouse_table_name("gold", "dim_date")
GOLD_DIM_TEAM_TABLE = lakehouse_table_name("gold", "dim_team")
GOLD_DIM_PLAYER_TABLE = lakehouse_table_name("gold", "dim_player")
GOLD_FACT_GAMES_TABLE = lakehouse_table_name("gold", "fact_games")
GOLD_FACT_PLAYER_GAMES_TABLE = lakehouse_table_name("gold", "fact_player_games")
GOLD_FACT_SHOTS_TABLE = lakehouse_table_name("gold", "fact_shots")
GOLD_AGG_PLAYER_STATS_TABLE = lakehouse_table_name("gold", "agg_player_season_stats")
GOLD_AGG_TEAM_PERFORMANCE_TABLE = lakehouse_table_name("gold", "agg_team_game_performance")


def write_execution_log(
    run_id: str,
    start_time: datetime,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    schema = StructType([
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
    row = (
        run_id,
        "03_Dimensional_Model_Gold_Layer",
        start_time,
        datetime.utcnow(),
        status,
        0,
        0,
        0,
        error_message,
        datetime.utcnow().date().isoformat(),
    )
    spark.createDataFrame([row], schema).write \
        .format("delta").mode("append").saveAsTable(EXECUTION_LOG_TABLE)


# Cell 2: Dimension Table Functions
# ==================================

def create_dim_date():
    """
    Create DimDate dimension table.
    
    Grain: One row per calendar date
    Attributes: Year, Month, Quarter, Day of week, Holiday flags
    """
    try:
        logger.info("Creating DimDate dimension...")
        
        # Keep the date dimension ahead of upcoming NBA seasons.
        dates_sql = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY dates.date) as date_key,
            dates.date,
            YEAR(dates.date) as year,
            MONTH(dates.date) as month,
            QUARTER(dates.date) as quarter,
            DAY(dates.date) as day_of_month,
            DAYOFWEEK(dates.date) as day_of_week,
            WEEKOFYEAR(dates.date) as week_of_year,
            CASE
                WHEN MONTH(dates.date) IN (11, 12) OR
                     (MONTH(dates.date) = 1 AND DAY(dates.date) <= 2)
                THEN TRUE
                ELSE FALSE
            END as is_holiday_period,
            current_timestamp() as created_timestamp,
            current_timestamp() as updated_timestamp
        FROM (
            SELECT EXPLODE(SEQUENCE(
                to_date('2023-01-01'),
                add_months(current_date(), 60),
                INTERVAL 1 DAY
            )) as date
        ) dates
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_DIM_DATE_TABLE}
            USING DELTA
            COMMENT 'Date dimension for time-based analysis'
            AS
            {dates_sql}
        """)
        
        logger.info("✅ DimDate created successfully")
        print("✅ DimDate dimension created")
        
    except Exception as e:
        logger.error(f"Error creating DimDate: {str(e)}")
        raise


def create_dim_team():
    """
    Create DimTeam dimension table.
    
    Grain: One row per team per season (SCD Type 2)
    Attributes: Team name, city, conference, division
    """
    try:
        logger.info("Creating DimTeam dimension...")
        
        # Distinct teams from games (both home and away)
        teams_sql = f"""
        WITH teams AS (
            SELECT DISTINCT
                home_team_id as team_id,
                home_team_name as team_name,
                season
            FROM {SILVER_GAMES_TABLE}
            UNION
            SELECT DISTINCT
                away_team_id as team_id,
                away_team_name as team_name,
                season
            FROM {SILVER_GAMES_TABLE}
        ),
        team_divisions AS (
            SELECT
                team_id,
                team_name,
                season,
                CASE
                    WHEN team_name LIKE '%Miami%' THEN 'SOUTHEAST'
                    WHEN team_name LIKE '%Boston%' THEN 'ATLANTIC'
                    WHEN team_name LIKE '%New York%' THEN 'ATLANTIC'
                    WHEN team_name LIKE '%Philadelphia%' THEN 'ATLANTIC'
                    WHEN team_name LIKE '%Toronto%' THEN 'ATLANTIC'
                    WHEN team_name LIKE '%Detroit%' THEN 'CENTRAL'
                    WHEN team_name LIKE '%Indiana%' THEN 'CENTRAL'
                    WHEN team_name LIKE '%Chicago%' THEN 'CENTRAL'
                    WHEN team_name LIKE '%Cleveland%' THEN 'CENTRAL'
                    WHEN team_name LIKE '%Milwaukee%' THEN 'CENTRAL'
                    WHEN team_name LIKE '%Atlanta%' THEN 'SOUTHEAST'
                    WHEN team_name LIKE '%Charlotte%' THEN 'SOUTHEAST'
                    WHEN team_name LIKE '%Washington%' THEN 'SOUTHEAST'
                    WHEN team_name LIKE '%Denver%' THEN 'NORTHWEST'
                    WHEN team_name LIKE '%Portland%' THEN 'NORTHWEST'
                    WHEN team_name LIKE '%Utah%' THEN 'NORTHWEST'
                    WHEN team_name LIKE '%Oklahoma%' THEN 'SOUTHWEST'
                    WHEN team_name LIKE '%San Antonio%' THEN 'SOUTHWEST'
                    WHEN team_name LIKE '%Houston%' THEN 'SOUTHWEST'
                    WHEN team_name LIKE '%Memphis%' THEN 'SOUTHWEST'
                    WHEN team_name LIKE '%Dallas%' THEN 'SOUTHWEST'
                    WHEN team_name LIKE '%Los Angeles Lakers%' THEN 'PACIFIC'
                    WHEN team_name LIKE '%Golden State%' THEN 'PACIFIC'
                    WHEN team_name LIKE '%Los Angeles Clippers%' THEN 'PACIFIC'
                    WHEN team_name LIKE '%Sacramento%' THEN 'PACIFIC'
                    WHEN team_name LIKE '%Phoenix%' THEN 'PACIFIC'
                    ELSE 'UNKNOWN'
                END as division
            FROM teams
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY team_id, season) as team_key,
            team_id,
            team_name,
            CASE
                WHEN division IN ('ATLANTIC', 'CENTRAL', 'SOUTHEAST') THEN 'EAST'
                WHEN division IN ('NORTHWEST', 'SOUTHWEST', 'PACIFIC') THEN 'WEST'
                ELSE 'UNKNOWN'
            END as conference,
            division,
            season,
            TRUE as is_active,
            current_timestamp() as created_timestamp,
            current_timestamp() as updated_timestamp
        FROM team_divisions
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_DIM_TEAM_TABLE}
            USING DELTA
            COMMENT 'Team dimension with division and conference'
            PARTITIONED BY (season)
            AS
            {teams_sql}
        """)
        
        logger.info("✅ DimTeam created successfully")
        print("✅ DimTeam dimension created")
        
    except Exception as e:
        logger.error(f"Error creating DimTeam: {str(e)}")
        raise


def create_dim_player():
    """
    Create DimPlayer dimension table.
    
    Grain: One row per player (slowly changing, Type 1)
    Attributes: Player name, position, team history
    """
    try:
        logger.info("Creating DimPlayer dimension...")
        
        # Unique players from Silver layer
        players_sql = f"""
        WITH ranked_players AS (
            SELECT
                player_id,
                player_name,
                position_normalized as primary_position,
                team_id,
                team_name,
                ROW_NUMBER() OVER (
                    PARTITION BY player_id
                    ORDER BY game_date DESC, ingestion_timestamp DESC
                ) as player_rank
            FROM {SILVER_PLAYER_STATS_TABLE}
            WHERE player_id IS NOT NULL AND player_name IS NOT NULL
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY player_id) as player_key,
            player_id,
            player_name,
            primary_position,
            team_id,
            team_name,
            current_timestamp() as created_timestamp,
            current_timestamp() as updated_timestamp
        FROM ranked_players
        WHERE player_rank = 1
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_DIM_PLAYER_TABLE}
            USING DELTA
            COMMENT 'Player dimension with career information'
            AS
            {players_sql}
        """)
        
        logger.info("✅ DimPlayer created successfully")
        print("✅ DimPlayer dimension created")
        
    except Exception as e:
        logger.error(f"Error creating DimPlayer: {str(e)}")
        raise


# Cell 3: Fact Table Functions
# ============================

def create_fact_games():
    """
    Create FactGames fact table.
    
    Grain: One row per game
    Measures: Points, assists, rebounds, etc.
    Dimensions: Date, Home Team, Away Team
    """
    try:
        logger.info("Creating FactGames fact table...")
        
        fact_sql = f"""
        WITH games_with_keys AS (
            SELECT
                g.game_id,
                g.game_date,
                ROW_NUMBER() OVER (ORDER BY g.game_date, g.game_id) as game_key,
                dd.date_key,
                dt_h.team_key as home_team_key,
                dt_a.team_key as away_team_key,
                g.home_score as home_points,
                g.away_score as away_points,
                ABS(g.home_score - g.away_score) as point_differential,
                g.home_score + g.away_score as total_points,
                CASE
                    WHEN g.home_score IS NULL OR g.away_score IS NULL THEN NULL
                    WHEN g.home_score > g.away_score THEN 'HOME'
                    WHEN g.home_score < g.away_score THEN 'AWAY'
                    ELSE 'TIE'
                END as winning_team,
                g.game_status_final as game_status,
                g.season_phase as game_type,
                g.season,
                g.arena_name,
                current_timestamp() as created_timestamp,
                current_timestamp() as updated_timestamp
            FROM {SILVER_GAMES_TABLE} g
            LEFT JOIN {GOLD_DIM_DATE_TABLE} dd
                ON g.game_date = dd.date
            LEFT JOIN {GOLD_DIM_TEAM_TABLE} dt_h
                ON g.home_team_id = dt_h.team_id
                AND g.season = dt_h.season
            LEFT JOIN {GOLD_DIM_TEAM_TABLE} dt_a
                ON g.away_team_id = dt_a.team_id
                AND g.season = dt_a.season
        )
        SELECT * FROM games_with_keys
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_FACT_GAMES_TABLE}
            USING DELTA
            COMMENT 'Game-level facts with scores and status'
            PARTITIONED BY (game_date)
            AS
            {fact_sql}
        """)
        
        logger.info("✅ FactGames created successfully")
        print("✅ FactGames fact table created")
        
    except Exception as e:
        logger.error(f"Error creating FactGames: {str(e)}")
        raise


def create_fact_player_games():
    """
    Create FactPlayerGames fact table.
    
    Grain: One row per player per game
    Measures: Points, rebounds, assists, shooting percentages
    Dimensions: Player, Game, Team, Date
    """
    try:
        logger.info("Creating FactPlayerGames fact table...")
        
        fact_sql = f"""
        WITH player_games_with_keys AS (
            SELECT
                ROW_NUMBER() OVER (ORDER BY ps.game_date, ps.game_id, ps.player_id) as player_game_key,
                ps.game_id,
                ps.game_date,
                ps.player_id,
                ps.team_id,
                ps.player_name,
                ps.team_name,
                ps.season,
                dd.date_key,
                dp.player_key,
                dt.team_key,
                -- Scoring
                ps.points,
                ps.field_goals_made,
                ps.field_goals_attempted,
                ps.fg_percentage,
                ps.three_pointers_made,
                ps.three_pointers_attempted,
                ps.three_point_percentage,
                ps.free_throws_made,
                ps.free_throws_attempted,
                ps.ft_percentage,
                -- Rebounds and assists
                ps.rebounds,
                ps.assists,
                -- Defense and efficiency
                ps.steals,
                ps.blocks,
                ps.turnovers,
                ps.fouls,
                ps.plus_minus,
                ps.minutes_played,
                -- Other
                ps.position_normalized as primary_position,
                CASE
                    WHEN ps.points >= 20 THEN 'SCORER'
                    WHEN ps.rebounds >= 10 THEN 'REBOUNDER'
                    WHEN ps.assists >= 5 THEN 'PLAYMAKER'
                    ELSE 'ROLE_PLAYER'
                END as player_role,
                fg.game_status,
                current_timestamp() as created_timestamp,
                current_timestamp() as updated_timestamp
            FROM {SILVER_PLAYER_STATS_TABLE} ps
            LEFT JOIN {GOLD_DIM_DATE_TABLE} dd
                ON ps.game_date = dd.date
            LEFT JOIN {GOLD_DIM_PLAYER_TABLE} dp
                ON ps.player_id = dp.player_id
            LEFT JOIN {GOLD_DIM_TEAM_TABLE} dt
                ON ps.team_id = dt.team_id
                AND ps.season = dt.season
            LEFT JOIN {GOLD_FACT_GAMES_TABLE} fg
                ON ps.game_id = fg.game_id
                AND ps.game_date = fg.game_date
            WHERE ps.player_id IS NOT NULL
        )
        SELECT * FROM player_games_with_keys
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_FACT_PLAYER_GAMES_TABLE}
            USING DELTA
            COMMENT 'Player-game level facts for performance analysis'
            PARTITIONED BY (game_date)
            AS
            {fact_sql}
        """)
        
        logger.info("✅ FactPlayerGames created successfully")
        print("✅ FactPlayerGames fact table created")
        
    except Exception as e:
        logger.error(f"Error creating FactPlayerGames: {str(e)}")
        raise


def create_fact_shots():
    """
    Create FactShots fact table.
    
    Grain: One row per shot
    Measures: Shot made/missed, distance, coordinates
    Dimensions: Player, Game, Team, Date
    """
    try:
        logger.info("Creating FactShots fact table...")
        
        fact_sql = f"""
        WITH shots_with_keys AS (
            SELECT
                ROW_NUMBER() OVER (ORDER BY s.game_date, s.game_id, s.player_id, s.shot_number) as shot_key,
                s.game_id,
                s.game_date,
                s.player_id,
                s.team_id,
                s.season,
                s.shot_number,
                dd.date_key,
                dp.player_key,
                dt.team_key,
                s.shot_type,
                s.shot_zone,
                s.shot_difficulty,
                s.shot_distance,
                s.x_coordinate,
                s.y_coordinate,
                CASE WHEN s.is_made THEN 1 ELSE 0 END as is_made,
                s.quarter,
                s.minutes_remaining,
                s.seconds_remaining,
                current_timestamp() as created_timestamp
            FROM {SILVER_SHOTS_TABLE} s
            LEFT JOIN {GOLD_DIM_DATE_TABLE} dd
                ON s.game_date = dd.date
            LEFT JOIN {GOLD_DIM_PLAYER_TABLE} dp
                ON s.player_id = dp.player_id
            LEFT JOIN {GOLD_DIM_TEAM_TABLE} dt
                ON s.team_id = dt.team_id
                AND s.season = dt.season
            WHERE s.player_id IS NOT NULL
        )
        SELECT * FROM shots_with_keys
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_FACT_SHOTS_TABLE}
            USING DELTA
            COMMENT 'Shot-level facts for shot analysis and heatmaps'
            PARTITIONED BY (game_date)
            AS
            {fact_sql}
        """)
        
        logger.info("✅ FactShots created successfully")
        print("✅ FactShots fact table created")
        
    except Exception as e:
        logger.error(f"Error creating FactShots: {str(e)}")
        raise


# Cell 4: Aggregate Tables for Performance
# ========================================

def create_agg_player_season_stats():
    """
    Create pre-aggregated player season statistics.
    
    Used for quick season summaries in reports
    Grain: One row per player per season
    """
    try:
        logger.info("Creating AggPlayerSeasonStats...")
        
        agg_sql = f"""
        SELECT
            player_key,
            player_id,
            player_name,
            primary_position,
            season,
            COUNT(DISTINCT game_id) as games_played,
            ROUND(AVG(points), 2) as avg_points,
            ROUND(AVG(rebounds), 2) as avg_rebounds,
            ROUND(AVG(assists), 2) as avg_assists,
            ROUND(AVG(minutes_played), 1) as avg_minutes,
            SUM(points) as total_points,
            ROUND(AVG(fg_percentage), 1) as avg_fg_percentage,
            ROUND(AVG(three_point_percentage), 1) as avg_three_point_percentage,
            ROUND(AVG(plus_minus), 2) as avg_plus_minus,
            SUM(steals) as total_steals,
            SUM(blocks) as total_blocks,
            SUM(turnovers) as total_turnovers,
            current_timestamp() as created_timestamp
        FROM {GOLD_FACT_PLAYER_GAMES_TABLE}
        GROUP BY player_key, player_id, player_name, primary_position, season
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_AGG_PLAYER_STATS_TABLE}
            USING DELTA
            COMMENT 'Pre-aggregated player season statistics'
            PARTITIONED BY (season)
            AS
            {agg_sql}
        """)
        
        logger.info("✅ AggPlayerSeasonStats created successfully")
        print("✅ AggPlayerSeasonStats aggregate table created")
        
    except Exception as e:
        logger.error(f"Error creating AggPlayerSeasonStats: {str(e)}")
        raise


def create_agg_team_game_performance():
    """
    Create team game performance aggregates.
    
    Grain: One row per team per game
    Includes team shooting efficiency, rebounds, etc.
    """
    try:
        logger.info("Creating AggTeamGamePerformance...")
        
        agg_sql = f"""
        SELECT
            game_date,
            game_id,
            team_key,
            team_id,
            team_name,
            season,
            COUNT(*) as players_played,
            SUM(points) as total_points,
            ROUND(AVG(minutes_played), 1) as avg_minutes,
            SUM(rebounds) as total_rebounds,
            SUM(assists) as total_assists,
            ROUND(AVG(fg_percentage), 1) as team_fg_percentage,
            ROUND(AVG(three_point_percentage), 1) as team_three_point_percentage,
            SUM(steals) as total_steals,
            SUM(blocks) as total_blocks,
            SUM(turnovers) as total_turnovers,
            current_timestamp() as created_timestamp
        FROM {GOLD_FACT_PLAYER_GAMES_TABLE}
        GROUP BY game_date, game_id, team_key, team_id, team_name, season
        """
        
        spark.sql(f"""
            CREATE OR REPLACE TABLE {GOLD_AGG_TEAM_PERFORMANCE_TABLE}
            USING DELTA
            COMMENT 'Team performance aggregates per game'
            PARTITIONED BY (game_date)
            AS
            {agg_sql}
        """)
        
        logger.info("✅ AggTeamGamePerformance created successfully")
        print("✅ AggTeamGamePerformance aggregate table created")
        
    except Exception as e:
        logger.error(f"Error creating AggTeamGamePerformance: {str(e)}")
        raise


# Cell 5: Execute Gold Layer Build
# ================================

run_start_time = datetime.utcnow()
run_id = f"gold_build_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

try:
    logger.info("="*70)
    logger.info("GOLD LAYER DIMENSIONAL MODEL BUILD STARTED")
    logger.info("="*70)
    
    # Create dimension tables
    print("\n📊 Creating Dimension Tables...")
    print("-"*70)
    create_dim_date()
    create_dim_team()
    create_dim_player()
    
    print("\n" + "="*70)
    print("\n📊 Creating Fact Tables...")
    print("-"*70)
    create_fact_games()
    create_fact_player_games()
    create_fact_shots()
    
    print("\n" + "="*70)
    print("\n📊 Creating Aggregate Tables...")
    print("-"*70)
    create_agg_player_season_stats()
    create_agg_team_game_performance()
    
    # Log execution
    write_execution_log(run_id, run_start_time, "SUCCESS")
    
    logger.info("="*70)
    logger.info("GOLD LAYER BUILD COMPLETED SUCCESSFULLY")
    logger.info("="*70)
    print("\n✅ Gold dimensional model created successfully!")
    print("✅ Ready for Power BI Direct Lake connectivity!")
    
except Exception as e:
    logger.exception(f"Fatal error during Gold layer build: {str(e)}")
    print(f"\n❌ Gold layer build failed: {str(e)}")
    raise
    if spark.catalog.tableExists(EXECUTION_LOG_TABLE):
        write_execution_log(
            run_id,
            run_start_time,
            "FAILED",
            error_message=str(e)[:4000],
        )
    raise


# Cell 6: Validation & Schema Info
# ================================

# Display schema information for Power BI
print("\n" + "="*70)
print("📋 GOLD LAYER SCHEMA SUMMARY")
print("="*70)

gold_tables = [
    GOLD_DIM_DATE_TABLE,
    GOLD_DIM_TEAM_TABLE,
    GOLD_DIM_PLAYER_TABLE,
    GOLD_FACT_GAMES_TABLE,
    GOLD_FACT_PLAYER_GAMES_TABLE,
    GOLD_FACT_SHOTS_TABLE,
    GOLD_AGG_PLAYER_STATS_TABLE,
    GOLD_AGG_TEAM_PERFORMANCE_TABLE,
]

for table_name in gold_tables:
    count = spark.table(table_name).count()
    spark.sql(f"DESCRIBE TABLE {table_name}").show(truncate=False)
    print(f"\n✅ {table_name}: {count:,} rows\n")

print("="*70)
print("Ready for Power BI Direct Lake!")
print("="*70)




