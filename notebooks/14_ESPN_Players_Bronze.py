# Fabric Notebook Code: 14_ESPN_Players_Bronze
"""Land ESPN game summaries with player box scores in a Bronze Delta table."""

# Cell 1: Setup
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

LANDING_PATH = "Files/espn_nba/boxscores/*.jsonl"
BRONZE_TABLE = "bronze_espn_boxscores"
schema = StructType([
    StructField("batch_id", StringType(), False),
    StructField("collected_at", StringType(), False),
    StructField("game_id", StringType(), False),
    StructField("game_date", StringType(), False),
    StructField("source", StringType(), False),
    StructField("payload", StringType(), False),
])

# Cell 2: Read and validate staged data
staged = spark.read.schema(schema).json(LANDING_PATH)
invalid = staged.filter(
    F.col("batch_id").isNull() | F.col("collected_at").isNull()
    | F.col("game_id").isNull() | F.col("game_date").isNull()
    | F.col("source").isNull() | F.col("payload").isNull()
)
if invalid.limit(1).count():
    raise ValueError("Arquivo ESPN de jogadores invalido; verifique o lote no OneLake.")
staged = staged.dropDuplicates(["batch_id", "game_id"])
input_count = staged.count()
if not input_count:
    raise ValueError("Nenhum box score encontrado. Execute stage_espn_players primeiro.")

# Cell 3: Upsert Bronze
if not spark.catalog.tableExists(BRONZE_TABLE):
    spark.createDataFrame([], schema).write.format("delta").saveAsTable(BRONZE_TABLE)
staged.createOrReplaceTempView("espn_boxscores_staging")
spark.sql(f"""
    MERGE INTO {BRONZE_TABLE} AS target
    USING espn_boxscores_staging AS source
    ON target.batch_id = source.batch_id AND target.game_id = source.game_id
    WHEN NOT MATCHED THEN INSERT *
""")
print(f"Bronze jogadores: {input_count} box scores verificados; total {spark.table(BRONZE_TABLE).count()}.")
