# Fabric Notebook Code: 15_ESPN_Players_Silver
"""Clean ESPN player and team box scores at game-level granularity."""

# Cell 1: Setup
from pyspark.sql import Window, functions as F
from pyspark.sql.types import ArrayType, BooleanType, StringType, StructField, StructType

BRONZE_TABLE = "bronze_espn_boxscores"
GAMES_TABLE = "silver_espn_games"
PLAYER_TABLE = "silver_espn_player_games"
TEAM_TABLE = "silver_espn_team_games"
team_identity_schema = StructType([
    StructField("id", StringType()),
    StructField("displayName", StringType()),
    StructField("abbreviation", StringType()),
    StructField("logo", StringType()),
])
athlete_schema = StructType([
    StructField("id", StringType()),
    StructField("displayName", StringType()),
    StructField("jersey", StringType()),
    StructField("position", StructType([StructField("abbreviation", StringType())])),
    StructField("headshot", StructType([StructField("href", StringType())])),
])
player_entry_schema = StructType([
    StructField("athlete", athlete_schema),
    StructField("active", BooleanType()),
    StructField("starter", BooleanType()),
    StructField("didNotPlay", BooleanType()),
    StructField("reason", StringType()),
    StructField("stats", ArrayType(StringType())),
])
player_statistics_schema = StructType([
    StructField("names", ArrayType(StringType())),
    StructField("athletes", ArrayType(player_entry_schema)),
])
player_team_schema = StructType([
    StructField("team", team_identity_schema),
    StructField("statistics", ArrayType(player_statistics_schema)),
])
team_stat_schema = StructType([
    StructField("name", StringType()),
    StructField("displayValue", StringType()),
])
team_boxscore_schema = StructType([
    StructField("team", team_identity_schema),
    StructField("homeAway", StringType()),
    StructField("statistics", ArrayType(team_stat_schema)),
])
payload_schema = StructType([
    StructField("boxscore", StructType([
        StructField("players", ArrayType(player_team_schema)),
        StructField("teams", ArrayType(team_boxscore_schema)),
    ])),
])

# Cell 2: Select the latest complete snapshot for each game
if not spark.catalog.tableExists(BRONZE_TABLE):
    raise ValueError("Tabela Bronze de jogadores nao encontrada. Execute 14_ESPN_Players_Bronze.")
if not spark.catalog.tableExists(GAMES_TABLE):
    raise ValueError("Tabela Silver de jogos nao encontrada. Execute 12_ESPN_Silver primeiro.")
latest = (
    spark.table(BRONZE_TABLE)
    .withColumn("snapshot_rank", F.row_number().over(
        Window.partitionBy("game_id").orderBy(F.desc("collected_at"), F.desc("batch_id"))
    ))
    .filter(F.col("snapshot_rank") == 1)
    .withColumn("data", F.from_json("payload", payload_schema))
)
if latest.filter(
    F.col("data.boxscore.players").isNull()
    | (F.size("data.boxscore.players") != 2)
    | F.col("data.boxscore.teams").isNull()
    | (F.size("data.boxscore.teams") != 2)
).limit(1).count():
    raise ValueError("Box score ESPN invalido: sao esperados dois times e dois grupos de jogadores.")
game_seasons = spark.table(GAMES_TABLE).select(
    "game_id", "season_year", "season_name", "season_type",
)
latest = latest.join(game_seasons, on="game_id", how="left")
if latest.filter(
    F.col("season_year").isNull() | F.col("season_name").isNull() | F.col("season_type").isNull()
).limit(1).count():
    raise ValueError("Box score ESPN sem temporada correspondente na Silver de jogos.")

teams = latest.select(
    "batch_id", "collected_at", "game_id", "game_date",
    "season_year", "season_name", "season_type",
    F.explode("data.boxscore.players").alias("side"),
)
if teams.filter(
    F.col("side.team.id").isNull() | F.col("side.team.displayName").isNull()
    | F.col("side.statistics").isNull() | (F.size("side.statistics") != 1)
).limit(1).count():
    raise ValueError("Box score ESPN invalido: estatisticas ou identificacao do time ausentes.")
groups = teams.select(
    "batch_id", "collected_at", "game_id", "game_date",
    "season_year", "season_name", "season_type",
    F.col("side.team.id").alias("team_id"),
    F.col("side.team.displayName").alias("team_name"),
    F.col("side.team.abbreviation").alias("team_abbreviation"),
    F.col("side.team.logo").alias("team_logo"),
    F.explode("side.statistics").alias("group"),
)
required_player_stats = (
    "MIN", "PTS", "FG", "3PT", "FT", "REB", "AST", "TO",
    "STL", "BLK", "OREB", "DREB", "PF", "+/-",
)
invalid_group = F.col("group.athletes").isNull() | (F.size("group.athletes") == 0)
for label in required_player_stats:
    invalid_group = invalid_group | ~F.coalesce(F.array_contains("group.names", label), F.lit(False))
if groups.filter(invalid_group).limit(1).count():
    raise ValueError("Box score ESPN sem jogadores ou indicadores individuais obrigatorios.")

# Cell 3: Extract and validate player-game statistics
entries = groups.select(
    "batch_id", "collected_at", "game_id", "game_date",
    "season_year", "season_name", "season_type",
    "team_id", "team_name", "team_abbreviation", "team_logo",
    F.col("group.names").alias("names"),
    F.explode("group.athletes").alias("entry"),
)
if entries.filter(F.col("entry.didNotPlay").isNull()).limit(1).count():
    raise ValueError("Box score ESPN sem indicador de participacao do jogador.")
played = entries.filter(~F.col("entry.didNotPlay"))
integer_stats = (
    ("PTS", "points_raw"), ("REB", "rebounds_raw"), ("AST", "assists_raw"),
    ("TO", "turnovers_raw"), ("STL", "steals_raw"), ("BLK", "blocks_raw"),
    ("OREB", "offensive_rebounds_raw"), ("DREB", "defensive_rebounds_raw"),
    ("PF", "personal_fouls_raw"), ("+/-", "plus_minus_raw"),
)
for label, column in (("MIN", "minutes_raw"),) + integer_stats + (
    ("FG", "field_goals_raw"), ("3PT", "three_point_field_goals_raw"),
    ("FT", "free_throws_raw"),
):
    played = played.withColumn(
        column,
        F.expr(f"try_element_at(entry.stats, cast(array_position(names, '{label}') as int))"),
    )

inactive_without_minutes = (
    (F.col("minutes_raw") == "--") & (F.col("entry.active") == F.lit(False))
    & (F.length(F.trim(F.col("entry.reason"))) > 0)
    & (F.col("points_raw") == "0") & (F.col("rebounds_raw") == "0")
    & (F.col("assists_raw") == "0")
)
inactive_without_minutes = F.coalesce(inactive_without_minutes, F.lit(False))
excluded_count = played.filter(inactive_without_minutes).count()
if excluded_count:
    print(f"Jogadores inativos sem minutos excluidos: {excluded_count}.")
played = played.filter(~inactive_without_minutes)
invalid_player = (
    F.col("entry.athlete.id").isNull() | F.col("entry.athlete.displayName").isNull()
    | ~F.coalesce(F.col("minutes_raw").rlike(r"^\d+(?::[0-5]\d)?$"), F.lit(False))
)
for _, column in integer_stats:
    pattern = r"^[+-]?\d+$" if column == "plus_minus_raw" else r"^\d+$"
    invalid_player = invalid_player | ~F.coalesce(F.col(column).rlike(pattern), F.lit(False))
for column in ("field_goals_raw", "three_point_field_goals_raw", "free_throws_raw"):
    invalid_player = invalid_player | ~F.coalesce(F.col(column).rlike(r"^\d+-\d+$"), F.lit(False))
raw_player_columns = ["minutes_raw"] + [column for _, column in integer_stats] + [
    "field_goals_raw", "three_point_field_goals_raw", "free_throws_raw",
]
invalid_player_examples = (
    played.filter(invalid_player)
    .select(
        "game_id", "team_id",
        F.col("entry.athlete.id").alias("player_id"),
        F.col("entry.athlete.displayName").alias("player_name"),
        *raw_player_columns,
    )
    .limit(5)
    .collect()
)
if invalid_player_examples:
    examples = [row.asDict(recursive=True) for row in invalid_player_examples]
    raise ValueError(
        "Box score ESPN contem estatisticas individuais invalidas. "
        f"Exemplos de valores brutos: {examples}"
    )

def stat_part(column, group):
    expression = F.regexp_extract(F.col(column), r"^(\d+)-(\d+)$", group).cast("int")
    return expression

players = played.select(
    "game_id", F.to_date("game_date").alias("game_date"),
    "season_year", "season_name", "season_type",
    "team_id", "team_name", "team_abbreviation", "team_logo",
    F.col("entry.athlete.id").alias("player_id"),
    F.col("entry.athlete.displayName").alias("player_name"),
    F.col("entry.athlete.position.abbreviation").alias("position"),
    F.col("entry.athlete.jersey").alias("jersey"),
    F.col("entry.athlete.headshot.href").alias("headshot_url"),
    F.col("entry.starter").alias("is_starter"),
    (
        F.regexp_extract("minutes_raw", r"^(\d+)", 1).cast("double")
        + F.when(F.col("minutes_raw").contains(":"),
                 F.regexp_extract("minutes_raw", r":(\d+)$", 1).cast("double") / 60)
        .otherwise(F.lit(0.0))
    ).alias("minutes"),
    F.col("points_raw").cast("int").alias("points"),
    stat_part("field_goals_raw", 1).alias("field_goals_made"),
    stat_part("field_goals_raw", 2).alias("field_goals_attempted"),
    stat_part("three_point_field_goals_raw", 1).alias("three_point_field_goals_made"),
    stat_part("three_point_field_goals_raw", 2).alias("three_point_field_goals_attempted"),
    stat_part("free_throws_raw", 1).alias("free_throws_made"),
    stat_part("free_throws_raw", 2).alias("free_throws_attempted"),
    F.col("rebounds_raw").cast("int").alias("rebounds"),
    F.col("assists_raw").cast("int").alias("assists"),
    F.col("turnovers_raw").cast("int").alias("turnovers"),
    F.col("steals_raw").cast("int").alias("steals"),
    F.col("blocks_raw").cast("int").alias("blocks"),
    F.col("offensive_rebounds_raw").cast("int").alias("offensive_rebounds"),
    F.col("defensive_rebounds_raw").cast("int").alias("defensive_rebounds"),
    F.col("personal_fouls_raw").cast("int").alias("personal_fouls"),
    F.col("plus_minus_raw").cast("int").alias("plus_minus"),
    "collected_at", "batch_id",
)
if players.filter(F.col("game_date").isNull()).limit(1).count():
    raise ValueError("Data de jogo invalida no box score ESPN.")
if players.groupBy("game_id", "player_id").count().filter(F.col("count") > 1).limit(1).count():
    raise ValueError("Jogador duplicado no mesmo jogo ESPN.")
player_count = players.count()
if not player_count:
    raise ValueError("Nenhum jogador participante encontrado nos box scores ESPN.")

# Cell 4: Extract and validate team-game box scores
team_entries = latest.select(
    "batch_id", "collected_at", "game_id", "game_date",
    "season_year", "season_name", "season_type",
    F.explode("data.boxscore.teams").alias("side"),
).select(
    "batch_id", "collected_at", "game_id", "game_date",
    "season_year", "season_name", "season_type",
    F.col("side.team.id").alias("team_id"),
    F.col("side.team.displayName").alias("team_name"),
    F.col("side.team.abbreviation").alias("team_abbreviation"),
    F.col("side.team.logo").alias("team_logo"),
    F.col("side.homeAway").alias("home_away"),
    F.col("side.statistics").alias("statistics"),
)
if team_entries.filter(
    F.col("team_id").isNull() | F.col("team_name").isNull()
    | ~F.col("home_away").isin("home", "away")
    | F.col("statistics").isNull()
).limit(1).count():
    raise ValueError("Box score ESPN invalido: identificacao do time ou estatisticas ausentes.")

team_stat_names = {
    "field_goals_raw": "fieldGoalsMade-fieldGoalsAttempted",
    "field_goal_pct_raw": "fieldGoalPct",
    "three_point_field_goals_raw": "threePointFieldGoalsMade-threePointFieldGoalsAttempted",
    "three_point_pct_raw": "threePointFieldGoalPct",
    "free_throws_raw": "freeThrowsMade-freeThrowsAttempted",
    "free_throw_pct_raw": "freeThrowPct",
    "total_rebounds_raw": "totalRebounds",
    "offensive_rebounds_raw": "offensiveRebounds",
    "defensive_rebounds_raw": "defensiveRebounds",
    "assists_raw": "assists",
    "steals_raw": "steals",
    "blocks_raw": "blocks",
    "turnovers_raw": "turnovers",
    "team_turnovers_raw": "teamTurnovers",
    "total_turnovers_raw": "totalTurnovers",
    "technical_fouls_raw": "technicalFouls",
    "total_technical_fouls_raw": "totalTechnicalFouls",
    "flagrant_fouls_raw": "flagrantFouls",
    "turnover_points_raw": "turnoverPoints",
    "fast_break_points_raw": "fastBreakPoints",
    "points_in_paint_raw": "pointsInPaint",
    "personal_fouls_raw": "fouls",
    "largest_lead_raw": "largestLead",
    "lead_changes_raw": "leadChanges",
    "lead_percentage_raw": "leadPercentage",
}
for column, source_name in team_stat_names.items():
    team_entries = team_entries.withColumn(
        column,
        F.expr(f"try_element_at(filter(statistics, x -> x.name = '{source_name}'), 1).displayValue"),
    )

required_team_stats = (
    "field_goals_raw", "field_goal_pct_raw", "three_point_field_goals_raw",
    "three_point_pct_raw", "free_throws_raw", "free_throw_pct_raw",
    "total_rebounds_raw", "offensive_rebounds_raw", "defensive_rebounds_raw",
    "assists_raw", "steals_raw", "blocks_raw", "turnovers_raw",
    "team_turnovers_raw", "total_turnovers_raw", "turnover_points_raw",
    "fast_break_points_raw", "points_in_paint_raw", "personal_fouls_raw",
    "largest_lead_raw", "lead_changes_raw", "lead_percentage_raw",
)
invalid_team_stats = F.lit(False)
for column in required_team_stats:
    invalid_team_stats = invalid_team_stats | F.col(column).isNull()
for column in ("field_goals_raw", "three_point_field_goals_raw", "free_throws_raw"):
    invalid_team_stats = invalid_team_stats | ~F.coalesce(F.col(column).rlike(r"^\d+-\d+$"), F.lit(False))
for column in (
    "field_goal_pct_raw", "three_point_pct_raw", "free_throw_pct_raw", "lead_percentage_raw",
):
    invalid_team_stats = invalid_team_stats | ~F.coalesce(F.col(column).rlike(r"^\d+(\.\d+)?$"), F.lit(False))
for column in required_team_stats:
    if column not in (
        "field_goals_raw", "three_point_field_goals_raw", "free_throws_raw",
        "field_goal_pct_raw", "three_point_pct_raw", "free_throw_pct_raw", "lead_percentage_raw",
    ):
        invalid_team_stats = invalid_team_stats | ~F.coalesce(F.col(column).rlike(r"^\d+$"), F.lit(False))
if team_entries.filter(invalid_team_stats).limit(1).count():
    raise ValueError("Box score ESPN contem estatisticas de time ausentes ou invalidas.")

def team_stat_part(column, group):
    return F.regexp_extract(F.col(column), r"^(\d+)-(\d+)$", group).cast("int")

team_games = team_entries.select(
    "game_id", F.to_date("game_date").alias("game_date"),
    "season_year", "season_name", "season_type",
    "team_id", "team_name", "team_abbreviation", "team_logo", "home_away",
    team_stat_part("field_goals_raw", 1).alias("field_goals_made"),
    team_stat_part("field_goals_raw", 2).alias("field_goals_attempted"),
    F.col("field_goal_pct_raw").cast("double").alias("field_goal_pct"),
    team_stat_part("three_point_field_goals_raw", 1).alias("three_point_field_goals_made"),
    team_stat_part("three_point_field_goals_raw", 2).alias("three_point_field_goals_attempted"),
    F.col("three_point_pct_raw").cast("double").alias("three_point_pct"),
    team_stat_part("free_throws_raw", 1).alias("free_throws_made"),
    team_stat_part("free_throws_raw", 2).alias("free_throws_attempted"),
    F.col("free_throw_pct_raw").cast("double").alias("free_throw_pct"),
    F.col("total_rebounds_raw").cast("int").alias("rebounds"),
    F.col("offensive_rebounds_raw").cast("int").alias("offensive_rebounds"),
    F.col("defensive_rebounds_raw").cast("int").alias("defensive_rebounds"),
    F.col("assists_raw").cast("int").alias("assists"),
    F.col("steals_raw").cast("int").alias("steals"),
    F.col("blocks_raw").cast("int").alias("blocks"),
    F.col("turnovers_raw").cast("int").alias("turnovers"),
    F.col("team_turnovers_raw").cast("int").alias("team_turnovers"),
    F.col("total_turnovers_raw").cast("int").alias("total_turnovers"),
    F.col("technical_fouls_raw").cast("int").alias("technical_fouls"),
    F.col("total_technical_fouls_raw").cast("int").alias("total_technical_fouls"),
    F.col("flagrant_fouls_raw").cast("int").alias("flagrant_fouls"),
    F.col("turnover_points_raw").cast("int").alias("turnover_points"),
    F.col("fast_break_points_raw").cast("int").alias("fast_break_points"),
    F.col("points_in_paint_raw").cast("int").alias("points_in_paint"),
    F.col("personal_fouls_raw").cast("int").alias("personal_fouls"),
    F.col("largest_lead_raw").cast("int").alias("largest_lead"),
    F.col("lead_changes_raw").cast("int").alias("lead_changes"),
    F.col("lead_percentage_raw").cast("double").alias("lead_percentage"),
    "collected_at", "batch_id",
)
if team_games.filter(F.col("game_date").isNull()).limit(1).count():
    raise ValueError("Data de jogo invalida no box score ESPN de times.")
if team_games.groupBy("game_id", "team_id").count().filter(F.col("count") != 1).limit(1).count():
    raise ValueError("Time duplicado no mesmo jogo ESPN.")
team_count = team_games.count()
if not team_count:
    raise ValueError("Nenhuma estatistica de time encontrada nos box scores ESPN.")

# Cell 5: Write Silver tables
players.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(PLAYER_TABLE)
team_games.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(TEAM_TABLE)
print(f"Silver: {player_count} participacoes de jogadores e {team_count} registros time-jogo.")
