# Fabric Notebook Code: 11_ESPN_Bronze
"""Land staged ESPN scoreboard snapshots in a Bronze Delta table."""

# Cell 1: Setup
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

LANDING_PATH = "Files/espn_nba/landing/*.jsonl"
BRONZE_TABLE = "bronze_espn_scoreboards"
schema = StructType([
    StructField("batch_id", StringType(), False),
    StructField("collected_at", StringType(), False),
    StructField("requested_date", StringType(), False),
    StructField("source", StringType(), False),
    StructField("payload", StringType(), False),
])

# Cell 2: Read and validate staged data
staged = spark.read.schema(schema).json(LANDING_PATH)
invalid = staged.filter(
    F.col("batch_id").isNull() | F.col("collected_at").isNull()
    | F.col("requested_date").isNull() | F.col("payload").isNull()
)
if invalid.limit(1).count():
    raise ValueError("Arquivo de entrada ESPN invalido; verifique o lote no OneLake.")
staged = staged.dropDuplicates(["batch_id", "requested_date"])
input_count = staged.count()
if not input_count:
    raise ValueError("Nenhum lote encontrado. Execute stage_espn_scoreboard.py primeiro.")

# Cell 3: Upsert Bronze
if not spark.catalog.tableExists(BRONZE_TABLE):
    spark.createDataFrame([], schema).write.format("delta").saveAsTable(BRONZE_TABLE)
staged.createOrReplaceTempView("espn_scoreboards_staging")
spark.sql(f"""
    MERGE INTO {BRONZE_TABLE} AS target
    USING espn_scoreboards_staging AS source
    ON target.batch_id = source.batch_id AND target.requested_date = source.requested_date
    WHEN NOT MATCHED THEN INSERT *
""")
print(f"Bronze: {input_count} snapshots verificados; total {spark.table(BRONZE_TABLE).count()}.")
