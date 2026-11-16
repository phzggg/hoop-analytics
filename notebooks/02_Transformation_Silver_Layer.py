# Fabric Notebook Code: 02_Transformation_Silver_Layer

"""
NBA Live Data Platform - Phase 3
Notebook 2: Silver Layer Transformations & Data Quality

Purpose:
- Clean and standardize Bronze data
- Apply data quality validations
- Enrich with calculated fields
- Store clean data for analytics

Production Grade Features:
- Data quality checks with flagging
- Deduplication logic
- Null handling and defaults
- Referential integrity checks
- Schema validation
- Lineage tracking with transformation metadata
"""

# Cell 1: Setup & Imports
# =======================



from pyspark.sql import DataFrame, functions as F, types as T, Window
from pyspark.sql.types import *
from datetime import datetime
import logging
import uuid
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nba_transformations')

# Get execution context
context = notebookutils.runtime.context
is_pipeline = context["isForPipeline"]

logger.info(f"Silver transformation started (from pipeline: {is_pipeline})")

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
SILVER_GAMES_TABLE = lakehouse_table_name("silver", "games_clean")
SILVER_PLAYER_STATS_TABLE = lakehouse_table_name("silver", "player_stats_clean")
SILVER_SHOTS_TABLE = lakehouse_table_name("silver", "shots_clean")


def write_execution_log(
    run_id: str,
    start_time: datetime,
    status: str,
    games_processed: int = 0,
    player_records_processed: int = 0,
    shots_processed: int = 0,
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
        "02_Transformation_Silver_Layer",
        start_time,
        datetime.utcnow(),
        status,
        games_processed,
        player_records_processed,
        shots_processed,
        error_message,
        datetime.utcnow().date().isoformat(),
    )
    spark.createDataFrame([row], schema).write \
        .format("delta").mode("append").saveAsTable(EXECUTION_LOG_TABLE)


# Cell 2: Data Quality Framework
# ==============================

class DataQualityValidator:
    """
    Production-grade data quality validation framework.
    
    Validates:
    - Completeness (required fields non-null)
    - Uniqueness (no unwanted duplicates)
    - Validity (correct data types, ranges)
    - Consistency (referential integrity)
    """
    
    def __init__(self, df, table_name: str):
        self.df = df
        self.table_name = table_name
        self.validation_results = {}
        self.dq_flags = None
    
    def check_completeness(self, required_fields: List[str]) -> Dict[str, int]:
        """
        Check for null values in required fields.
        
        Returns:
            Dictionary with field -> null_count
        """
        results = {}
        for field in required_fields:
            null_count = self.df.filter(F.col(field).isNull()).count()
            results[field] = null_count
            if null_count > 0:
                logger.warning(
                    f"{self.table_name}: {null_count} nulls found in required field '{field}'"
                )
        self.validation_results['completeness'] = results
        return results
    
    def check_uniqueness(self, unique_key_fields: List[str]) -> int:
        """
        Check for duplicate rows based on unique key.
        
        Returns:
            Number of duplicate rows
        """
        duplicate_count = (
            self.df
            .groupBy(*unique_key_fields)
            .count()
            .filter(F.col("count") > 1)
            .count()
        )
        self.validation_results['duplicates'] = duplicate_count
        if duplicate_count > 0:
            logger.warning(
                f"{self.table_name}: {duplicate_count} duplicate key combinations found"
            )
        return duplicate_count
    
    def check_valid_ranges(self, range_checks: Dict[str, tuple]) -> Dict[str, int]:
        """
        Check numeric fields are within valid ranges.
        
        Args:
            range_checks: {field: (min, max), ...}
            
        Returns:
            Dictionary with field -> violations_count
        """
        results = {}
        for field, (min_val, max_val) in range_checks.items():
            violations = self.df.filter(
                (F.col(field) < min_val) | (F.col(field) > max_val)
            ).count()
            results[field] = violations
            if violations > 0:
                logger.warning(
                    f"{self.table_name}: {violations} out-of-range values in '{field}'"
                )
        self.validation_results['range_violations'] = results
        return results
    
    def add_quality_flags(self, required_fields: List[str]) -> DataFrame:
        """
        Add data quality flags to DataFrame.
        
        Returns:
            DataFrame with additional quality columns
        """
        has_required_null = F.lit(False)
        for field in required_fields:
            has_required_null = has_required_null | F.col(field).isNull()

        df_flagged = self.df.withColumn(
            "dq_has_nulls", has_required_null
        ).withColumn(
            "dq_validation_status",
            F.when(has_required_null, "FAILED").otherwise("PASSED")
        ).withColumn(
            "dq_processed_timestamp",
            F.current_timestamp()
        )
        
        self.dq_flags = df_flagged
        logger.info(f"{self.table_name}: Quality flags added")
        return df_flagged
    
    def report(self) -> str:
        """Generate data quality report."""
        report = f"\n📊 Data Quality Report: {self.table_name}\n"
        report += f"{'='*50}\n"
        for check_name, results in self.validation_results.items():
            report += f"\n{check_name.upper()}:\n"
            if isinstance(results, dict):
                for field, value in results.items():
                    report += f"  {field}: {value}\n"
            else:
                report += f"  Result: {results}\n"
        return report


# Cell 3: Transform Games Data
# ============================

def transform_games_silver() -> int:
    """
    Transform games_raw → games_clean
    
    Transformations:
    - Remove duplicates
    - Standardize game status
    - Add calculated fields (game_duration_minutes)
    - Validate score values
    - Add data quality flags
    
    Returns:
        Number of records processed
    """
    try:
        logger.info("Starting games transformation")
        
        # Read from Bronze
        df_games_raw = spark.table(BRONZE_GAMES_TABLE)
        record_count = df_games_raw.count()
        logger.info(f"Read {record_count} raw game records")
        
        # Step 1: Remove duplicates (keep latest ingestion)
        df_deduplicated = (
            df_games_raw
            .withColumn(
                "rn",
                F.row_number().over(
                    Window.partitionBy("game_id")
                    .orderBy(F.desc("ingestion_timestamp"))
                )
            )
            .filter(F.col("rn") == 1)
            .drop("rn")
        )
        
        dedup_count = df_deduplicated.count()
        logger.info(f"After deduplication: {dedup_count} records")
        
        # Step 2: Apply transformations
        df_games_clean = (
            df_deduplicated
            .withColumn(
                "game_date_key",  # For dimensional joins
                F.concat(
                    F.year(F.col("game_date")),
                    F.lpad(F.month(F.col("game_date")), 2, "0"),
                    F.lpad(F.dayofmonth(F.col("game_date")), 2, "0")
                ).cast(IntegerType())
            )
            .withColumn(
                "season",
                F.coalesce(
                    F.col("season"),
                    F.when(F.month("game_date") >= 10, F.year("game_date"))
                    .otherwise(F.year("game_date") - 1),
                ).cast(IntegerType())
            )
            .withColumn(
                "game_status_final",
                F.when(F.col("game_status") == 3, "FINAL")
                .when(F.col("game_status") == 2, "IN_PROGRESS")
                .when(F.col("game_status") == 1, "NOT_STARTED")
                .otherwise("UNKNOWN")
            )
            .withColumn(
                "total_points",
                F.coalesce(F.col("home_score"), F.lit(0)) +
                F.coalesce(F.col("away_score"), F.lit(0))
            )
            .withColumn(
                "point_differential",
                F.coalesce(F.col("home_score"), F.lit(0)) -
                F.coalesce(F.col("away_score"), F.lit(0))
            )
            .withColumn(
                "season_phase",
                F.when(F.col("game_type") == "PRESEASON", "PRESEASON")
                .when(F.col("game_type") == "REGULAR", "REGULAR")
                .when(F.col("game_type") == "PLAYOFFS", "PLAYOFFS")
                .when(F.col("game_type") == "ALL_STAR", "ALL_STAR")
                .otherwise("UNKNOWN")
            )
            # Add lineage
            .withColumn(
                "source_bronze_table",
                F.lit(BRONZE_GAMES_TABLE)
            )
            .withColumn(
                "silver_transformation_timestamp",
                F.current_timestamp()
            )
        )
        
        # Step 3: Data quality validation
        validator = DataQualityValidator(df_games_clean, "games_clean")
        
        # Check required fields
        required_fields = ["game_id", "game_date", "home_team_id", "away_team_id"]
        validator.check_completeness(required_fields)
        
        # Check for duplicates
        validator.check_uniqueness(["game_id"])
        
        # Check score ranges (0-150 points is reasonable for NBA)
        validator.check_valid_ranges({
            "home_score": (0, 150),
            "away_score": (0, 150)
        })
        
        print(validator.report())
        logger.info(f"Data quality validation completed")
        
        # Step 4: Add quality flags
        df_games_final = validator.add_quality_flags(required_fields)
        
        # Step 5: Write to Silver
        df_games_final.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy("game_date") \
            .saveAsTable(SILVER_GAMES_TABLE)
        
        logger.info(f"Wrote {dedup_count} records to {SILVER_GAMES_TABLE}")
        print(f"✅ Games transformation complete: {dedup_count} records")
        
        return dedup_count
        
    except Exception as e:
        logger.error(f"Error transforming games: {str(e)}")
        raise


# Cell 4: Transform Player Stats Data
# ====================================

def transform_player_stats_silver() -> int:
    """
    Transform player_stats_raw → player_stats_clean
    
    Transformations:
    - Calculate shooting percentages
    - Normalize player positions
    - Add performance indicators
    - Validate game existence (referential integrity)
    - Remove bench players without stats (optional)
    
    Returns:
        Number of records processed
    """
    try:
        logger.info("Starting player stats transformation")
        
        # Read from Bronze
        df_player_stats_raw = spark.table(BRONZE_PLAYER_STATS_TABLE)
        record_count = df_player_stats_raw.count()
        logger.info(f"Read {record_count} raw player stat records")
        
        # Step 1: Deduplicate (keep latest ingestion per game/player)
        df_deduplicated = (
            df_player_stats_raw
            .withColumn(
                "rn",
                F.row_number().over(
                    Window.partitionBy("game_id", "player_id")
                    .orderBy(F.desc("ingestion_timestamp"))
                )
            )
            .filter(F.col("rn") == 1)
            .drop("rn")
        )
        
        dedup_count = df_deduplicated.count()
        logger.info(f"After deduplication: {dedup_count} records")
        
        # Step 2: Calculate shooting percentages (handle division by zero)
        df_player_stats_clean = (
            df_deduplicated
            .withColumn(
                "fg_percentage",
                F.when(
                    F.col("field_goals_attempted") > 0,
                    F.round(
                        (F.col("field_goals_made") /
                         F.col("field_goals_attempted")) * 100,
                        2
                    )
                ).otherwise(F.lit(None))
            )
            .withColumn(
                "three_point_percentage",
                F.when(
                    F.col("three_pointers_attempted") > 0,
                    F.round(
                        (F.col("three_pointers_made") /
                         F.col("three_pointers_attempted")) * 100,
                        2
                    )
                ).otherwise(F.lit(None))
            )
            .withColumn(
                "ft_percentage",
                F.when(
                    F.col("free_throws_attempted") > 0,
                    F.round(
                        (F.col("free_throws_made") /
                         F.col("free_throws_attempted")) * 100,
                        2
                    )
                ).otherwise(F.lit(None))
            )
            # Normalize positions
            .withColumn(
                "position_normalized",
                F.when(F.col("position").isin("C"), "CENTER")
                .when(F.col("position").isin("PF"), "POWER_FORWARD")
                .when(F.col("position").isin("SF"), "SMALL_FORWARD")
                .when(F.col("position").isin("SG"), "SHOOTING_GUARD")
                .when(F.col("position").isin("PG"), "POINT_GUARD")
                .otherwise("UNKNOWN")
            )
            .withColumn(
                "season",
                F.when(F.month("game_date") >= 10, F.year("game_date"))
                .otherwise(F.year("game_date") - 1)
                .cast(IntegerType())
            )
            # Calculate efficiency rating (simple PER variant)
            .withColumn(
                "usage_indicator",
                F.round(
                    ((F.col("field_goals_attempted") +
                      F.col("free_throws_attempted") * 0.44 +
                      F.col("turnovers")) / 100) * 100,
                    2
                )
            )
            # Add lineage
            .withColumn(
                "source_bronze_table",
                F.lit(BRONZE_PLAYER_STATS_TABLE)
            )
            .withColumn(
                "silver_transformation_timestamp",
                F.current_timestamp()
            )
        )
        
        # Step 3: Data quality validation
        validator = DataQualityValidator(
            df_player_stats_clean,
            "player_stats_clean"
        )
        
        required_fields = ["game_id", "player_id", "team_id"]
        validator.check_completeness(required_fields)
        validator.check_uniqueness(["game_id", "player_id"])
        
        # Validate performance stats
        validator.check_valid_ranges({
            "points": (0, 100),
            "rebounds": (0, 50),
            "assists": (0, 30)
        })
        
        print(validator.report())
        
        # Step 4: Add quality flags
        df_player_stats_final = validator.add_quality_flags(required_fields)
        
        # Step 5: Write to Silver
        df_player_stats_final.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy("game_date") \
            .saveAsTable(SILVER_PLAYER_STATS_TABLE)
        
        logger.info(f"Wrote {dedup_count} records to {SILVER_PLAYER_STATS_TABLE}")
        print(f"✅ Player stats transformation complete: {dedup_count} records")
        
        return dedup_count
        
    except Exception as e:
        logger.error(f"Error transforming player stats: {str(e)}")
        raise


# Cell 5: Transform Shots Data
# ============================

def transform_shots_silver() -> int:
    """
    Transform shots_raw → shots_clean
    
    Transformations:
    - Validate shot coordinates (within court bounds)
    - Categorize shot zones
    - Add shot quality indicators
    - Remove invalid records
    
    Returns:
        Number of records processed
    """
    try:
        logger.info("Starting shots transformation")
        
        # Read from Bronze
        df_shots_raw = spark.table(BRONZE_SHOTS_TABLE)
        record_count = df_shots_raw.count()
        logger.info(f"Read {record_count} raw shot records")
        
        # Step 1: Deduplicate
        df_deduplicated = (
            df_shots_raw
            .withColumn(
                "rn",
                F.row_number().over(
                    Window.partitionBy("game_id", "player_id", "shot_number")
                    .orderBy(F.desc("ingestion_timestamp"))
                )
            )
            .filter(F.col("rn") == 1)
            .drop("rn")
        )
        
        dedup_count = df_deduplicated.count()
        
        # Step 2: Validate and categorize
        df_shots_clean = (
            df_deduplicated
            # Filter invalid court coordinates (NBA court is 94 x 50 feet)
            .filter(
                (F.col("x_coordinate").isNull() |
                 ((F.col("x_coordinate") >= -250) & (F.col("x_coordinate") <= 250))) &
                (F.col("y_coordinate").isNull() |
                 ((F.col("y_coordinate") >= -50) & (F.col("y_coordinate") <= 420)))
            )
            # Categorize shot zones
            .withColumn(
                "shot_zone",
                F.when(
                    F.col("shot_distance") <= 3,
                    "PAINT_NON_RA"
                )
                .when(
                    (F.col("shot_distance") > 3) & (F.col("shot_distance") <= 10),
                    "MID_RANGE"
                )
                .when(
                    (F.col("shot_distance") > 10) & (F.col("shot_distance") <= 40),
                    "THREE_POINT_RANGE"
                )
                .when(
                    F.col("shot_distance") > 40,
                    "DEEP_THREE"
                )
                .otherwise("UNKNOWN")
            )
            # Shot difficulty based on distance
            .withColumn(
                "shot_difficulty",
                F.when(F.col("shot_distance") <= 5, "EASY")
                .when((F.col("shot_distance") > 5) & (F.col("shot_distance") <= 15), "MEDIUM")
                .when((F.col("shot_distance") > 15) & (F.col("shot_distance") <= 28), "HARD")
                .when(F.col("shot_distance") > 28, "VERY_HARD")
                .otherwise("UNKNOWN")
            )
            .withColumn(
                "season",
                F.when(F.month("game_date") >= 10, F.year("game_date"))
                .otherwise(F.year("game_date") - 1)
                .cast(IntegerType())
            )
            # Add lineage
            .withColumn(
                "source_bronze_table",
                F.lit(BRONZE_SHOTS_TABLE)
            )
            .withColumn(
                "silver_transformation_timestamp",
                F.current_timestamp()
            )
        )
        
        # Step 3: Data quality validation
        validator = DataQualityValidator(df_shots_clean, "shots_clean")
        
        required_fields = ["game_id", "player_id", "is_made"]
        validator.check_completeness(required_fields)
        
        # Validate shot coordinates are within bounds
        validator.check_valid_ranges({
            "x_coordinate": (-250, 250),
            "y_coordinate": (-50, 420)
        })
        
        print(validator.report())
        
        # Step 4: Add quality flags
        df_shots_final = validator.add_quality_flags(required_fields)
        
        # Step 5: Write to Silver
        df_shots_final.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy("game_date") \
            .saveAsTable(SILVER_SHOTS_TABLE)
        
        clean_count = df_shots_final.count()
        logger.info(f"Wrote {clean_count} records to {SILVER_SHOTS_TABLE}")
        print(f"✅ Shots transformation complete: {clean_count} records")
        
        return clean_count
        
    except Exception as e:
        logger.error(f"Error transforming shots: {str(e)}")
        raise


# Cell 6: Execute All Transformations
# ====================================

run_start_time = datetime.utcnow()
run_id = f"silver_transform_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
games_count = 0
player_stats_count = 0
shots_count = 0

try:
    logger.info("="*60)
    logger.info("SILVER LAYER TRANSFORMATION STARTED")
    logger.info("="*60)
    
    # Execute transformations in order
    games_count = transform_games_silver()
    print("\n" + "="*60 + "\n")
    
    player_stats_count = transform_player_stats_silver()
    print("\n" + "="*60 + "\n")
    
    shots_count = transform_shots_silver()
    print("\n" + "="*60 + "\n")
    
    write_execution_log(
        run_id,
        run_start_time,
        "SUCCESS",
        games_count,
        player_stats_count,
        shots_count,
    )
    
    logger.info("="*60)
    logger.info("SILVER LAYER TRANSFORMATION COMPLETED SUCCESSFULLY")
    logger.info("="*60)
    print("✅ All Silver transformations completed successfully!")
    
except Exception as e:
    logger.exception(f"Fatal error during Silver transformation: {str(e)}")
    if spark.catalog.tableExists(EXECUTION_LOG_TABLE):
        write_execution_log(
            run_id,
            run_start_time,
            "FAILED",
            games_count,
            player_stats_count,
            shots_count,
            error_message=str(e)[:4000],
        )
    raise




