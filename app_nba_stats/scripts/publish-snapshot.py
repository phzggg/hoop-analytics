import base64
import gzip
import hashlib
import json
import math
import uuid
from datetime import datetime, timezone

import com.microsoft.sqlserver.jdbc.spark
import requests
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

EXPORT_FIELDS = None
DESTINATION_DATABASE = None
MODEL_ID = None

workspace_id = notebookutils.runtime.context["currentWorkspaceId"]
token = notebookutils.credentials.getToken("pbi")
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {token}"})
model_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{MODEL_ID}/executeQueries"


def query(dax):
    response = session.post(
        model_url,
        json={"queries": [{"query": dax}], "serializerSettings": {"includeNulls": True}},
        timeout=(10, 120),
    )
    response.raise_for_status()
    result = response.json()
    if result.get("error"):
        raise RuntimeError(f"Model query failed: {result['error']}")
    query_result = result["results"][0]
    if query_result.get("error"):
        raise RuntimeError(f"Model query failed: {query_result['error']}")
    table = query_result["tables"][0]
    if table.get("error"):
        raise RuntimeError(f"Model query failed: {table['error']}")
    return table["rows"]


tables = {}
for kind, specification in EXPORT_FIELDS.items():
    table = specification["table"]
    columns = specification["columns"]
    count = query(f"""EVALUATE ROW("n", COUNTROWS('{table}'))""")[0]["[n]"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError(f"Invalid row count for {kind}")
    if count > 100000 or count * len(columns) > 1000000:
        raise ValueError(f"{kind} exceeds query limits; partitioned export is required")
    source = query(specification["query"])
    if len(source) != count:
        raise ValueError(f"{kind}: received {len(source)} of {count} rows")
    rows = []
    for record in source:
        row = {}
        for index, column in enumerate(columns):
            key = f"[c{index}]"
            if key not in record:
                raise ValueError(f"Missing {column} in {kind}")
            value = record[key]
            if value is not None and not isinstance(value, (str, bool, int, float)):
                raise ValueError(f"Invalid {column} in {kind}")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"Invalid number in {kind}")
            row[column] = value
        rows.append(row)
    tables[kind] = rows
    print(f"{kind}: {count} rows")
if not tables["games"] or not tables["players"]:
    raise ValueError("Required game or player data is empty")

generated_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
snapshot = {"version": 1, "generatedAt": generated_at, "tables": tables}
data = json.dumps(snapshot, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
checksum = hashlib.sha256(data).hexdigest()
encoded = base64.b64encode(gzip.compress(data)).decode("ascii")
parts = [encoded[index:index + 3900] for index in range(0, len(encoded), 3900)]
version_id = str(uuid.uuid4())

headers = {"x-ms-fabric-skill": "spark-cli"}
url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases"
databases = []
while url:
    if not url.startswith(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases"):
        raise ValueError("Unexpected database listing URL")
    response = session.get(url, headers=headers, timeout=(10, 30))
    response.raise_for_status()
    page = response.json()
    databases.extend(item for item in page["value"] if item["displayName"] == DESTINATION_DATABASE)
    url = page.get("continuationUri")
if len(databases) != 1:
    raise RuntimeError(f"Expected one public database, found {len(databases)}")
database = databases[0]["properties"]
server = database["serverFqdn"].replace(",", ":")
database_name = database["databaseName"]
jdbc_url = f"jdbc:sqlserver://{server};database={database_name};encrypt=true;"

part_schema = StructType([
    StructField("id", StringType(), False),
    StructField("content", StringType(), False),
    StructField("part", IntegerType(), False),
    StructField("versionId", StringType(), False),
])
part_rows = [(str(uuid.uuid4()), content, index, version_id) for index, content in enumerate(parts)]
part_frame = spark.createDataFrame(part_rows, part_schema).coalesce(1)
part_frame.write.mode("append").option("url", jdbc_url).option("reliabilityLevel", "NO_DUPLICATES").mssql("dbo.SnapshotParts")
stored = (
    spark.read.option("url", jdbc_url).mssql("dbo.SnapshotParts")
    .filter(F.col("versionId") == version_id)
    .select("part", "content")
    .orderBy("part")
    .collect()
)
if len(stored) != len(parts) or any(row["part"] != index or row["content"] != parts[index] for index, row in enumerate(stored)):
    raise RuntimeError("Stored snapshot parts did not pass verification")
stored_data = gzip.decompress(base64.b64decode("".join(row["content"] for row in stored), validate=True))
if hashlib.sha256(stored_data).hexdigest() != checksum:
    raise RuntimeError("Stored snapshot checksum did not match")

version_schema = StructType([
    StructField("id", StringType(), False),
    StructField("createdAt", StringType(), False),
    StructField("parts", IntegerType(), False),
    StructField("sha256", StringType(), False),
])
version = spark.createDataFrame([(version_id, generated_at, len(parts), checksum)], version_schema)
version.write.mode("append").option("url", jdbc_url).option("reliabilityLevel", "NO_DUPLICATES").mssql("dbo.SnapshotVersions")
published = (
    spark.read.option("url", jdbc_url).mssql("dbo.SnapshotVersions")
    .filter(F.lower(F.col("id")) == version_id)
    .count()
)
if published != 1:
    raise RuntimeError(f"Expected one published version, found {published}")
print(f"Published {version_id}: {len(parts)} verified parts, generated {generated_at}")
