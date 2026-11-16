# Fabric Notebook Code: 12_ESPN_Silver
"""Clean ESPN scoreboards and keep the latest snapshot of each game."""

# Cell 1: Setup
from pyspark.sql import Window, functions as F
from pyspark.sql.types import ArrayType, DoubleType, IntegerType, StringType, StructField, StructType

BRONZE_TABLE = "bronze_espn_scoreboards"
SILVER_TABLE = "silver_espn_games"
team = StructType([
    StructField("id", StringType()),
    StructField("displayName", StringType()),
    StructField("abbreviation", StringType()),
    StructField("logo", StringType()),
])
season_type = StructType([
    StructField("id", StringType()),
    StructField("type", IntegerType()),
    StructField("name", StringType()),
])
season = StructType([
    StructField("year", IntegerType()),
    StructField("displayName", StringType()),
    StructField("type", season_type),
])
league = StructType([StructField("season", season)])
event_season = StructType([
    StructField("year", IntegerType()),
    StructField("displayName", StringType()),
    StructField("type", IntegerType()),
])
competitor = StructType([
    StructField("id", StringType()),
    StructField("homeAway", StringType()),
    StructField("score", StringType()),
    StructField("team", team),
    StructField("linescores", ArrayType(StructType([
        StructField("value", DoubleType()),
        StructField("period", IntegerType()),
    ]))),
])
status_type = StructType([
    StructField("state", StringType()),
    StructField("description", StringType()),
])
event = StructType([
    StructField("id", StringType()),
    StructField("season", event_season),
    StructField("status", StructType([StructField("type", status_type)])),
    StructField("competitions", ArrayType(StructType([
        StructField("competitors", ArrayType(competitor)),
    ]))),
])
payload_schema = StructType([
    StructField("events", ArrayType(event)),
    StructField("leagues", ArrayType(league)),
])

# Cell 2: Parse, validate and deduplicate
if not spark.catalog.tableExists(BRONZE_TABLE):
    raise ValueError("Tabela Bronze nao encontrada. Execute 11_ESPN_Bronze primeiro.")
parsed = spark.table(BRONZE_TABLE).withColumn("data", F.from_json("payload", payload_schema))
if parsed.filter(F.col("data.events").isNull()).limit(1).count():
    raise ValueError("Snapshot Bronze nao contem uma lista valida de jogos.")
events = parsed.select(
    "batch_id",
    "collected_at",
    "requested_date",
    F.col("data.leagues")[0]["season"].alias("league_season"),
    F.explode("data.events").alias("event"),
)
season_year = F.coalesce(F.col("event.season.year"), F.col("league_season.year"))
season_name = F.coalesce(F.col("event.season.displayName"), F.col("league_season.displayName"))
season_type_id = F.col("event.season.type")
season_type_name = F.when(
    F.col("league_season.type.type") == season_type_id,
    F.col("league_season.type.name"),
).otherwise(
    F.when(season_type_id == 2, F.lit("Regular Season"))
    .when(season_type_id == 3, F.lit("Postseason"))
)
if events.filter(season_type_id.isNull()).limit(1).count():
    raise ValueError("Jogo ESPN sem tipo de temporada no nivel do evento.")
nba_events = events.filter(season_type_id.isin(2, 3))
if nba_events.filter(
    season_year.isNull()
    | season_name.isNull()
    | season_type_name.isNull()
).limit(1).count():
    raise ValueError("Jogo ESPN sem tipo de temporada.")
games = (
    nba_events
    .withColumn("home", F.expr("filter(event.competitions[0].competitors, x -> x.homeAway = 'home')[0]"))
    .withColumn("away", F.expr("filter(event.competitions[0].competitors, x -> x.homeAway = 'away')[0]"))
    .select(
        F.col("event.id").alias("game_id"),
        F.to_date("requested_date").alias("game_date"),
        season_year.alias("season_year"),
        season_name.alias("season_name"),
        season_type_name.alias("season_type"),
        F.col("home.team.id").alias("home_team_id"),
        F.col("home.team.displayName").alias("home_team"),
        F.col("home.team.abbreviation").alias("home_team_abbreviation"),
        F.col("home.team.logo").alias("home_team_logo"),
        F.col("away.team.id").alias("away_team_id"),
        F.col("away.team.displayName").alias("away_team"),
        F.col("away.team.abbreviation").alias("away_team_abbreviation"),
        F.col("away.team.logo").alias("away_team_logo"),
        F.when(F.col("event.status.type.state") != "pre", F.col("home.score").cast("int")).alias("home_score"),
        F.when(F.col("event.status.type.state") != "pre", F.col("away.score").cast("int")).alias("away_score"),
        F.expr("transform(home.linescores, x -> cast(x.value as int))").alias("home_period_scores"),
        F.expr("transform(away.linescores, x -> cast(x.value as int))").alias("away_period_scores"),
        F.when(F.col("event.status.type.state") == "post", F.lit("FINAL"))
        .when(F.col("event.status.type.state") == "in", F.lit("LIVE"))
        .when(F.col("event.status.type.state") == "pre", F.lit("SCHEDULED"))
        .otherwise(F.lit("UNKNOWN")).alias("status"),
        F.col("collected_at"),
        F.col("batch_id"),
    )
)
invalid = games.filter(
    F.col("game_id").isNull() | F.col("game_date").isNull()
    | F.col("season_year").isNull() | F.col("season_name").isNull() | F.col("season_type").isNull()
    | F.col("home_team_id").isNull() | F.col("home_team").isNull()
    | F.col("away_team_id").isNull() | F.col("away_team").isNull()
    | ((F.col("status") == "FINAL") & (F.col("home_score").isNull() | F.col("away_score").isNull()))
    | (F.col("home_score") < 0) | (F.col("away_score") < 0)
)
if invalid.limit(1).count():
    raise ValueError("Dados de jogo invalidos encontrados na origem ESPN.")
period_shape_mismatch = games.filter(
    (F.col("status") == "FINAL")
    & (
        (
            F.col("home_period_scores").isNull()
            != F.col("away_period_scores").isNull()
        )
        | (
            F.col("home_period_scores").isNotNull()
            & F.col("away_period_scores").isNotNull()
            & (F.size("home_period_scores") != F.size("away_period_scores"))
        )
    )
)
if period_shape_mismatch.limit(1).count():
    raise ValueError("Placares por periodo ESPN incompletos para um dos times.")
period_totals_mismatch = games.filter(
    (F.col("status") == "FINAL")
    & F.col("home_period_scores").isNotNull()
    & F.col("away_period_scores").isNotNull()
    & (F.size("home_period_scores") > 0)
    & (
        (F.expr("aggregate(home_period_scores, 0, (total, points) -> total + points)") != F.col("home_score"))
        | (F.expr("aggregate(away_period_scores, 0, (total, points) -> total + points)") != F.col("away_score"))
    )
)
if period_totals_mismatch.limit(1).count():
    raise ValueError("Soma dos pontos por periodo diverge do placar final ESPN.")
latest = (
    games.withColumn(
        "row_number",
        F.row_number().over(
            Window.partitionBy("game_id").orderBy(F.desc("collected_at"), F.desc("batch_id"))
        ),
    )
    .filter(F.col("row_number") == 1)
    .drop("row_number")
)
if latest.limit(1).count() == 0:
    raise ValueError("Nenhum jogo valido encontrado; a tabela Silver nao foi sobrescrita.")

# Cell 3: Write Silver
latest.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(SILVER_TABLE)
print(f"Silver: {spark.table(SILVER_TABLE).count()} jogos validos.")
