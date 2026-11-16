# Fabric Notebook Code: 16_ESPN_Players_Gold
"""Create player-game details and per-player averages for the Fabric app."""

# Cell 1: Setup
from pyspark.sql import functions as F

SILVER_TABLE = "silver_espn_player_games"
SILVER_TEAM_TABLE = "silver_espn_team_games"
TEAM_GAMES_TABLE = "gold_espn_team_games"
GAMES_TABLE = "gold_espn_player_games"
SUMMARY_TABLE = "gold_espn_player_summary"
PLAYERS_TABLE = "gold_espn_players"
TEAM_BOXSCORES_TABLE = "gold_espn_team_boxscores"
if not spark.catalog.tableExists(SILVER_TABLE):
    raise ValueError("Tabela Silver de jogadores nao encontrada. Execute 15_ESPN_Players_Silver.")
if not spark.catalog.tableExists(SILVER_TEAM_TABLE):
    raise ValueError("Tabela Silver de times nao encontrada. Execute 15_ESPN_Players_Silver.")
if not spark.catalog.tableExists(TEAM_GAMES_TABLE):
    raise ValueError("Tabela Gold de jogos por time nao encontrada. Execute 13_ESPN_Gold primeiro.")
players = spark.table(SILVER_TABLE)

# Cell 2: Player-game details
player_games = players.select(
    "game_id", "game_date", "season_year", "season_name", "season_type",
    "team_id", "team_name", "team_abbreviation", "team_logo",
    "player_id", "player_name", "position", "jersey", "headshot_url", "is_starter",
    "minutes", "points", "field_goals_made", "field_goals_attempted",
    "three_point_field_goals_made", "three_point_field_goals_attempted",
    "free_throws_made", "free_throws_attempted",
    "rebounds", "offensive_rebounds", "defensive_rebounds",
    "assists", "turnovers", "steals", "blocks", "personal_fouls", "plus_minus",
    F.current_timestamp().alias("updated_at"),
)
player_games.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(GAMES_TABLE)

# Cell 3: Player-season summary
summary = players.groupBy(
    "player_id", "season_year", "season_name", "season_type",
).agg(
    F.max_by("player_name", F.struct("game_date", "game_id")).alias("player_name"),
    F.max_by("position", F.struct("game_date", "game_id")).alias("position"),
    F.max_by("jersey", F.struct("game_date", "game_id")).alias("jersey"),
    F.max_by("headshot_url", F.struct("game_date", "game_id")).alias("headshot_url"),
    F.count("*").alias("games_played"),
    F.sum("minutes").alias("total_minutes"),
    F.round(F.avg("minutes"), 2).alias("avg_minutes"),
    F.sum("points").alias("total_points"),
    F.round(F.avg("points"), 2).alias("avg_points"),
    F.sum("field_goals_made").alias("field_goals_made"),
    F.sum("field_goals_attempted").alias("field_goals_attempted"),
    F.sum("three_point_field_goals_made").alias("three_point_field_goals_made"),
    F.sum("three_point_field_goals_attempted").alias("three_point_field_goals_attempted"),
    F.sum("free_throws_made").alias("free_throws_made"),
    F.sum("free_throws_attempted").alias("free_throws_attempted"),
    F.round(F.avg("offensive_rebounds"), 2).alias("avg_offensive_rebounds"),
    F.round(F.avg("defensive_rebounds"), 2).alias("avg_defensive_rebounds"),
    F.round(F.avg("rebounds"), 2).alias("avg_rebounds"),
    F.round(F.avg("assists"), 2).alias("avg_assists"),
    F.round(F.avg("turnovers"), 2).alias("avg_turnovers"),
    F.round(F.avg("steals"), 2).alias("avg_steals"),
    F.round(F.avg("blocks"), 2).alias("avg_blocks"),
    F.round(F.avg("plus_minus"), 2).alias("avg_plus_minus"),
    F.sum("field_goals_made").alias("_fgm"),
    F.sum("field_goals_attempted").alias("_fga"),
    F.sum("three_point_field_goals_made").alias("_3pm"),
    F.sum("free_throws_attempted").alias("_fta"),
)
summary = (
    summary
    .withColumn(
        "field_goal_pct",
        F.when(F.col("_fga") > 0, F.round(F.col("_fgm") / F.col("_fga"), 4)),
    )
    .withColumn(
        "three_point_pct",
        F.when(
            F.col("three_point_field_goals_attempted") > 0,
            F.round(
                F.col("three_point_field_goals_made")
                / F.col("three_point_field_goals_attempted"),
                4,
            ),
        ),
    )
    .withColumn(
        "free_throw_pct",
        F.when(
            F.col("free_throws_attempted") > 0,
            F.round(F.col("free_throws_made") / F.col("free_throws_attempted"), 4),
        ),
    )
    .withColumn(
        "effective_field_goal_pct",
        F.when(F.col("_fga") > 0, F.round((F.col("_fgm") + 0.5 * F.col("_3pm")) / F.col("_fga"), 4)),
    )
    .withColumn(
        "true_shooting_pct",
        F.when(
            (F.col("_fga") + 0.44 * F.col("_fta")) > 0,
            F.round(
                F.col("total_points") / (2 * (F.col("_fga") + 0.44 * F.col("_fta"))),
                4,
            ),
        ),
    )
    .drop("_fgm", "_fga", "_3pm", "_fta")
    .withColumn("updated_at", F.current_timestamp())
)
summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(SUMMARY_TABLE)

# One row per player across seasons, using their latest observed details.
player_dimension = players.groupBy("player_id").agg(
    F.max_by("player_name", F.struct("game_date", "game_id")).alias("player_name"),
    F.max_by("position", F.struct("game_date", "game_id")).alias("position"),
    F.max_by("headshot_url", F.struct("game_date", "game_id")).alias("headshot_url"),
).withColumn("updated_at", F.current_timestamp())
player_dimension.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(PLAYERS_TABLE)

# Cell 4: Team-game box scores
team_stats = spark.table(SILVER_TEAM_TABLE)
scoreboard = spark.table(TEAM_GAMES_TABLE).select(
    "game_id", "team_id", "points_for", "points_against", "result", "point_differential",
)
team_boxscores = team_stats.join(scoreboard, on=["game_id", "team_id"], how="inner").withColumn(
    "updated_at", F.current_timestamp(),
)
team_boxscore_count = team_boxscores.count()
silver_team_count = team_stats.count()
if team_boxscore_count != silver_team_count:
    raise ValueError("Nem todos os box scores de time encontraram a partida correspondente na Gold.")
team_boxscores.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    TEAM_BOXSCORES_TABLE
)
print(
    f"Gold jogadores: {player_games.count()} participacoes e "
    f"{summary.count()} jogador-temporada; {team_boxscore_count} box scores de time."
)

# Cell 5: Refresh the semantic model after the pipeline has written Gold
def refresh_semantic_model():
    import time
    import uuid
    import requests

    workspace_id = notebookutils.runtime.context["currentWorkspaceId"]
    token = notebookutils.credentials.getToken("pbi")
    headers = {"Authorization": f"Bearer {token}"}
    base = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    session = requests.Session()
    url = f"{base}/datasets"
    models = []
    while url:
        if not url.startswith(f"{base}/datasets"):
            raise ValueError("Endereco inesperado na listagem de modelos semanticos.")
        response = session.get(url, headers=headers, timeout=(10, 30))
        response.raise_for_status()
        payload = response.json()
        models.extend(model for model in payload["value"] if model["name"] == "NBA Analise Jogadores")
        url = payload.get("@odata.nextLink")
    if len(models) != 1:
        raise ValueError(f"Esperado um modelo NBA Analise Jogadores; encontrados {len(models)}.")

    refresh_url = f"{base}/datasets/{models[0]['id']}/refreshes"
    response = session.post(
        refresh_url, headers=headers,
        json={"type": "full", "commitMode": "transactional", "timeout": "00:10:00"},
        timeout=(10, 30),
    )
    response.raise_for_status()
    request_id = response.headers.get("x-ms-request-id")
    if not request_id:
        raise RuntimeError("Atualizacao aceita sem identificador para acompanhar o resultado.")
    try:
        request_id = str(uuid.UUID(request_id))
    except ValueError as exc:
        raise RuntimeError("Identificador de atualizacao invalido.") from exc
    location = f"{refresh_url}/{request_id}"
    print(f"Atualizacao do modelo iniciada: {request_id}")
    deadline = time.monotonic() + 660
    while time.monotonic() < deadline:
        response = session.get(location, headers=headers, timeout=(10, 30))
        response.raise_for_status()
        details = response.json()
        status = details["status"]
        if status == "Completed":
            print("Modelo semantico NBA atualizado com sucesso.")
            return
        if status not in ("Unknown", "InProgress"):
            raise RuntimeError(
                f"Falha na atualizacao do modelo semantico: {status}; "
                f"detalhes: {details.get('messages', [])}"
            )
        time.sleep(10)
    raise TimeoutError("Tempo esgotado aguardando a atualizacao do modelo semantico.")


if notebookutils.runtime.context["isForPipeline"]:
    refresh_semantic_model()
