# Fabric Notebook Code: 13_ESPN_Gold
"""Create simple game and team analytics for the Fabric app."""

# Cell 1: Setup
from pyspark.sql import functions as F

SILVER_TABLE = "silver_espn_games"
GAMES_TABLE = "gold_espn_games"
TEAMS_TABLE = "gold_espn_team_summary"
TEAM_GAMES_TABLE = "gold_espn_team_games"
GAME_PERIODS_TABLE = "gold_espn_game_periods"
if not spark.catalog.tableExists(SILVER_TABLE):
    raise ValueError("Tabela Silver nao encontrada. Execute 12_ESPN_Silver primeiro.")
games = spark.table(SILVER_TABLE)

# Cell 2: Game table
gold_games = games.select(
    "game_id", "game_date", "season_year", "season_name", "season_type",
    "home_team_id", "home_team", "home_team_abbreviation", "home_team_logo",
    "away_team_id", "away_team", "away_team_abbreviation", "away_team_logo",
    "home_score", "away_score", "status",
    F.current_timestamp().alias("updated_at"),
)
gold_games.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(GAMES_TABLE)

# Cell 3: Team-game detail and season summary
final_games = games.filter(
    (F.col("status") == "FINAL") & F.col("home_score").isNotNull() & F.col("away_score").isNotNull()
)
home = final_games.select(
    "game_id", "game_date", "season_year", "season_name", "season_type",
    F.col("home_team_id").alias("team_id"),
    F.col("home_team").alias("team_name"),
    F.col("home_team_abbreviation").alias("team_abbreviation"),
    F.col("home_team_logo").alias("team_logo"),
    F.col("away_team_id").alias("opponent_id"),
    F.col("away_team").alias("opponent_name"),
    F.col("away_team_abbreviation").alias("opponent_abbreviation"),
    F.col("away_team_logo").alias("opponent_logo"),
    F.lit("HOME").alias("home_away"),
    F.col("home_score").alias("points_for"),
    F.col("away_score").alias("points_against"),
)
away = final_games.select(
    "game_id", "game_date", "season_year", "season_name", "season_type",
    F.col("away_team_id").alias("team_id"),
    F.col("away_team").alias("team_name"),
    F.col("away_team_abbreviation").alias("team_abbreviation"),
    F.col("away_team_logo").alias("team_logo"),
    F.col("home_team_id").alias("opponent_id"),
    F.col("home_team").alias("opponent_name"),
    F.col("home_team_abbreviation").alias("opponent_abbreviation"),
    F.col("home_team_logo").alias("opponent_logo"),
    F.lit("AWAY").alias("home_away"),
    F.col("away_score").alias("points_for"),
    F.col("home_score").alias("points_against"),
)
team_games = (
    home.unionByName(away)
    .withColumn("result", F.when(F.col("points_for") > F.col("points_against"), "W").otherwise("L"))
    .withColumn("point_differential", F.col("points_for") - F.col("points_against"))
    .withColumn("updated_at", F.current_timestamp())
)
if team_games.groupBy("game_id", "team_id").count().filter(F.col("count") != 1).limit(1).count():
    raise ValueError("Granularidade invalida: esperado um registro por time e jogo.")
team_games.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(TEAM_GAMES_TABLE)

summary = team_games.groupBy(
    "season_year", "season_name", "season_type", "team_id", "team_name",
    "team_abbreviation", "team_logo",
).agg(
    F.count("*").alias("games_played"),
    F.sum(F.when(F.col("result") == "W", 1).otherwise(0)).alias("wins"),
    F.sum(F.when(F.col("result") == "L", 1).otherwise(0)).alias("losses"),
    F.sum(F.when((F.col("home_away") == "HOME") & (F.col("result") == "W"), 1).otherwise(0)).alias("home_wins"),
    F.sum(F.when((F.col("home_away") == "HOME") & (F.col("result") == "L"), 1).otherwise(0)).alias("home_losses"),
    F.sum(F.when((F.col("home_away") == "AWAY") & (F.col("result") == "W"), 1).otherwise(0)).alias("away_wins"),
    F.sum(F.when((F.col("home_away") == "AWAY") & (F.col("result") == "L"), 1).otherwise(0)).alias("away_losses"),
    F.sum("points_for").alias("points_for"),
    F.sum("points_against").alias("points_against"),
    F.round(F.avg("points_for"), 2).alias("avg_points_for"),
    F.round(F.avg("points_against"), 2).alias("avg_points_against"),
    F.round(F.avg("point_differential"), 2).alias("avg_point_differential"),
)
summary = summary.withColumn("win_percentage", F.round(F.col("wins") / F.col("games_played"), 4))
summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(TEAMS_TABLE)

# Cell 4: Team-by-period detail for game box-score screens
home_periods = (
    final_games.filter(F.size("home_period_scores") > 0)
    .select(
        "game_id", "game_date", "season_year", "season_name", "season_type",
        F.col("home_team_id").alias("team_id"),
        F.col("home_team").alias("team_name"),
        F.col("away_team_id").alias("opponent_id"),
        F.col("away_team").alias("opponent_name"),
        F.lit("HOME").alias("home_away"),
        F.col("home_score").alias("team_score"),
        F.col("away_score").alias("opponent_score"),
        F.posexplode("home_period_scores").alias("period_index", "points"),
    )
)
away_periods = (
    final_games.filter(F.size("away_period_scores") > 0)
    .select(
        "game_id", "game_date", "season_year", "season_name", "season_type",
        F.col("away_team_id").alias("team_id"),
        F.col("away_team").alias("team_name"),
        F.col("home_team_id").alias("opponent_id"),
        F.col("home_team").alias("opponent_name"),
        F.lit("AWAY").alias("home_away"),
        F.col("away_score").alias("team_score"),
        F.col("home_score").alias("opponent_score"),
        F.posexplode("away_period_scores").alias("period_index", "points"),
    )
)
periods = home_periods.unionByName(away_periods)
periods = (
    periods.withColumn("period_number", F.col("period_index") + 1)
    .withColumn(
        "period_label",
        F.when(
            F.col("period_number") <= 4,
            F.concat(F.lit("Q"), F.col("period_number").cast("string")),
        ).otherwise(
            F.concat(F.lit("OT"), (F.col("period_number") - 4).cast("string")),
        ),
    )
    .withColumn("updated_at", F.current_timestamp())
    .drop("period_index")
)
if periods.groupBy("game_id", "team_id", "period_number").count().filter(F.col("count") != 1).limit(1).count():
    raise ValueError("Granularidade invalida: esperado um registro por time, jogo e periodo.")
periods.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(GAME_PERIODS_TABLE)
print(
    f"Gold: {spark.table(GAMES_TABLE).count()} jogos, "
    f"{spark.table(TEAM_GAMES_TABLE).count()} registros time-jogo, "
    f"{spark.table(TEAMS_TABLE).count()} campanhas e "
    f"{spark.table(GAME_PERIODS_TABLE).count()} registros de periodo."
)
