# Phase 3 Implementation Guide
## NBA Live Data Platform - Lakehouse Setup & PySpark Notebooks

**Last Updated:** 2024  
**Status:** Ready for Production Deployment  
**Target Workspace:** YOUR_WORKSPACE (Trial)

---

## 📋 Overview

Phase 3 builds the complete medallion architecture (Bronze → Silver → Gold) using production-grade PySpark notebooks in Microsoft Fabric. This phase transforms the raw NBA API data into an analytics-ready dimensional model optimized for Power BI Direct Lake connectivity.

### What We're Building

```
Phase 3 Architecture:
├── Bronze Layer (Raw Data)
│   ├── games_raw          (Raw game data from ScoreboardV3)
│   ├── player_stats_raw   (Raw stats from BoxScoreTraditionalV2)
│   ├── shots_raw          (Raw shots from ShotChartDetail)
│   └── execution_log      (Audit trail)
│
├── Silver Layer (Cleaned & Validated)
│   ├── games_clean        (Deduplicated, enriched games)
│   ├── player_stats_clean (Calculated percentages, normalized positions)
│   ├── shots_clean        (Validated coordinates, shot zones)
│   └── [Data Quality Flags]
│
└── Gold Layer (Analytics-Ready Dimensional Model)
    ├── Dimensions:
    │   ├── dim_date           (Calendar dimension)
    │   ├── dim_team           (Team with division/conference)
    │   ├── dim_player         (Player metadata)
    │   └── [SCD Type 2 support]
    │
    ├── Facts:
    │   ├── fact_games         (Game-level facts)
    │   ├── fact_player_games  (Player-game performance)
    │   └── fact_shots         (Shot-level details)
    │
    └── Aggregates:
        ├── agg_player_season_stats      (Pre-calculated player season stats)
        └── agg_team_game_performance    (Team game performance)
```

---

## 🚀 Quick Start: 3-Step Deployment

### Step 1: Create Lakehouse in Fabric
```bash
# Via Fabric CLI (optional - can also use Web UI)
fab item create --type Lakehouse --name nba_lakehouse --workspace "YOUR_WORKSPACE"
```

**Or use Fabric Web UI:**
1. Go to workspace "YOUR_WORKSPACE"
2. New → Lakehouse
3. Name: `nba_lakehouse`
4. Create

### Step 2: Deploy Notebooks to Fabric
1. In Fabric workspace, create 3 notebooks:
   - `01_Ingestion_Setup_Bronze`
   - `02_Transformation_Silver_Layer`
   - `03_Dimensional_Model_Gold_Layer`

2. For each notebook:
   - Copy code from corresponding `.py` file (see `/notebooks/`)
   - Paste into Fabric notebook cells
   - Configure default lakehouse attachment

### Step 3: Run Notebooks in Order
```
Notebook 1: 01_Ingestion_Setup_Bronze
  ↓ (5-10 minutes)
Notebook 2: 02_Transformation_Silver_Layer
  ↓ (5-10 minutes)
Notebook 3: 03_Dimensional_Model_Gold_Layer
  ↓ (3-5 minutes)
✅ Ready for Power BI
```

---

## 📚 Notebook Details

### Notebook 1: Ingestion Setup (Bronze Layer)
**File:** `01_Ingestion_Setup_Bronze.py` (20.7 KB)

**Purpose:**
- Initialize lakehouse and create schemas (bronze/silver/gold)
- Define Bronze layer tables with explicit schemas
- Implement NBA API ingestion with error handling
- Store raw data in Delta format with partitioning

**Key Functions:**
| Function | Purpose |
|----------|---------|
| `create_bronze_tables()` | Idempotent table creation |
| `get_nba_api_games()` | Fetch games from NBA API |
| `transform_game_record()` | Map API response to schema |
| `load_games_to_bronze()` | MERGE INTO upsert pattern |

**Production Features:**
✅ Explicit schema validation (no `inferSchema`)  
✅ Error handling with contextual logging  
✅ Idempotent operations (safe for re-execution)  
✅ MERGE INTO for duplicate handling  
✅ JSON audit trail in `api_response_json` field  
✅ Execution audit log with timestamps  

**Expected Output:**
- 3 Bronze tables (games_raw, player_stats_raw, shots_raw)
- 1 Execution log table
- Ready for incremental updates

---

### Notebook 2: Transformations (Silver Layer)
**File:** `02_Transformation_Silver_Layer.py` (20.5 KB)

**Purpose:**
- Clean and standardize Bronze data
- Apply data quality validations
- Calculate derived metrics (shooting %, efficiency)
- Deduplicate records and validate schema

**Key Features:**

**DataQualityValidator Class:**
```python
validator = DataQualityValidator(df, "table_name")
validator.check_completeness(["required_field_1", "required_field_2"])
validator.check_uniqueness(["unique_key"])
validator.check_valid_ranges({"field": (min, max)})
validator.add_quality_flags()
print(validator.report())
```

**Transformations Applied:**

| Layer | Transformation | Output |
|-------|---|---|
| **Games** | Dedup, status standardization, score validation, date key | games_clean |
| **Player Stats** | FG/3P/FT percentages, position normalization, usage calculation | player_stats_clean |
| **Shots** | Court validation (-250 to 250 x, -50 to 420 y), zone categorization | shots_clean |

**Data Quality Checks:**
- Completeness: Required fields are non-null
- Uniqueness: No unintended duplicates
- Validity: Score ranges (0-150), coordinates within court bounds
- Consistency: Referential integrity with games

**Expected Output:**
- 3 Silver tables with quality flags
- Data lineage with Bronze source tracking
- Ready for dimensional modeling

---

### Notebook 3: Dimensional Model (Gold Layer)
**File:** `03_Dimensional_Model_Gold_Layer.py` (21.2 KB)

**Purpose:**
- Build analytics-ready dimensional model
- Create conformed dimensions and fact tables
- Enable Power BI Direct Lake connectivity
- Pre-aggregate common metrics for performance

**Dimension Tables:**

| Table | Grain | Key Attributes | Rows |
|-------|-------|---|---|
| **dim_date** | One per calendar day | Year, month, quarter, day of week, holidays | ~1,460 (4 years) |
| **dim_team** | One per team per season | Team name, division, conference | ~30/season |
| **dim_player** | One per player | Player ID, name, position, team | ~500+ |

**Fact Tables:**

| Table | Grain | Measures | Partitioned By |
|-------|-------|----------|---|
| **fact_games** | One per game | Points, differential, status | game_date |
| **fact_player_games** | One player per game | Points, rebounds, assists, FG%, role | game_date |
| **fact_shots** | One per shot | Made/missed, distance, zone, coordinates | game_date |

**Aggregate Tables:**

| Table | Purpose | Used For |
|-------|---------|----------|
| **agg_player_season_stats** | Player season summaries | Dashboard filters, season stats |
| **agg_team_game_performance** | Team game performance | Team comparison, efficiency analysis |

**Expected Output:**
- 3 dimension tables with surrogate keys
- 3 fact tables with granular data
- 2 aggregate tables for performance
- **Total:** ~100K+ rows ready for Power BI Direct Lake
- **Format:** Delta Lake with partitioning
- **Ready:** Immediate Power BI connectivity (no import/DirectQuery needed)

---

## 🔧 Production-Grade Implementation Details

### Error Handling Pattern
```python
try:
    # Your transformation logic
    result = transform_data(df)
    logger.info(f"Successfully processed {result.count()} records")
except SpecificException as e:
    logger.error(f"Error during transformation: {str(e)}")
    # Decide: retry, dead-letter, or raise
    raise
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise
```

### Logging Best Practices
```python
logger.info(f"Processing {record_count} records from {source}")
logger.warning(f"{null_count} nulls in required field: {field_name}")
logger.error(f"Transformation failed: {error_details}")
```

### Idempotency Pattern
```python
# MERGE INTO handles both insert and update
spark.sql("""
    MERGE INTO target t
    USING source s
    ON t.key = s.key
    WHEN MATCHED THEN UPDATE SET ...
    WHEN NOT MATCHED THEN INSERT ...
""")
```

### Data Quality Framework
```python
# Validate at ingestion boundary
validator = DataQualityValidator(df, "table_name")
validator.check_completeness(required_fields)
validator.check_uniqueness(unique_key)
validator.check_valid_ranges(range_map)

# Add flags for analytics
df_flagged = validator.add_quality_flags()

# Report findings
print(validator.report())
```

### Partitioning Strategy
```python
# All tables partitioned by game_date for:
# ✅ Partition pruning (faster queries)
# ✅ Incremental updates
# ✅ Cost optimization
# ✅ Manageability

.partitionBy("game_date") \
.saveAsTable("schema.table_name")
```

---

## 🧪 Testing & Validation

### Validate Schema Consistency
```sql
-- Check all tables exist
SHOW TABLES IN bronze;
SHOW TABLES IN silver;
SHOW TABLES IN gold;

-- Verify record counts
SELECT COUNT(*) as row_count FROM bronze.games_raw;
SELECT COUNT(*) as row_count FROM silver.games_clean;
SELECT COUNT(*) as row_count FROM gold.fact_games;
```

### Data Quality Checks
```sql
-- Check for nulls in required fields
SELECT COUNT(*) FROM silver.games_clean WHERE game_id IS NULL;

-- Verify no unintended duplicates
SELECT game_id, COUNT(*) as cnt FROM gold.fact_games 
GROUP BY game_id 
HAVING COUNT(*) > 1;

-- Validate date ranges
SELECT 
    MIN(game_date) as earliest_game,
    MAX(game_date) as latest_game
FROM gold.fact_games;
```

### Referential Integrity
```sql
-- Check foreign key relationships
SELECT COUNT(*) as unmatched_teams
FROM gold.fact_games fg
LEFT JOIN gold.dim_team dt 
    ON fg.home_team_key = dt.team_key
WHERE dt.team_key IS NULL;
```

### Performance Validation
```sql
-- Check partition effectiveness
EXPLAIN 
SELECT * FROM gold.fact_games 
WHERE game_date = '2024-12-15';

-- Verify table statistics
SELECT 
    table_name, 
    rows, 
    size_in_bytes
FROM sys.tables
WHERE table_schema IN ('gold');
```

---

## 🔌 Power BI Direct Lake Setup

### Step 1: Enable Direct Lake
1. In Power BI Desktop or Service
2. Semantic Model → New → Direct Lake
3. Select workspace: **YOUR_WORKSPACE**
4. Select lakehouse: **nba_lakehouse**

### Step 2: Add Tables
Available tables for Direct Lake:
- `fact_games` (Game-level facts)
- `fact_player_games` (Player performance)
- `fact_shots` (Shot-level detail)
- `dim_date` (Calendar)
- `dim_team` (Team metadata)
- `dim_player` (Player metadata)
- `agg_player_season_stats` (Pre-aggregated stats)
- `agg_team_game_performance` (Team aggregates)

### Step 3: Create Relationships
```
Relationships to establish:
├── fact_games → dim_date (on date_key)
├── fact_games → dim_team (home_team_key, away_team_key)
├── fact_player_games → dim_date (on date_key)
├── fact_player_games → dim_player (on player_key)
├── fact_player_games → dim_team (on team_key)
└── fact_shots → dim_player (on player_key)
    fact_shots → dim_team (on team_key)
    fact_shots → dim_date (on date_key)
```

### Step 4: Build Reports
Example visualizations:
- **Game Summary:** Home vs Away scores, point differential
- **Player Performance:** PPG, RPG, APG, shooting percentages
- **Team Efficiency:** Points per game by division
- **Shot Chart:** Court heatmaps, make % by zone
- **Season Stats:** Player rankings, MVP candidates

---

## ⚙️ Configuration & Customization

### Change Data Refresh Window
Edit Notebook 1, Cell 6:
```python
# Current: Today's games only
today = datetime.now().strftime("%Y-%m-%d")

# Option A: Last 7 days
dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") 
         for i in range(7)]

# Option B: Full season (slow, use once)
start_date = "2024-10-22"
end_date = "2024-12-31"
```

### Adjust Data Quality Thresholds
Edit Notebook 2, define ranges:
```python
validator.check_valid_ranges({
    "home_score": (0, 200),      # Increase for extreme games
    "minutes_played": (0, 50),    # Adjust based on game length
})
```

### Add Custom Transformations
Insert in Notebook 2, Silver layer:
```python
# Example: Add player efficiency rating (PER)
df_player_stats_clean = df_player_stats_clean.withColumn(
    "player_efficiency_rating",
    F.round(
        ((ps.points + ps.rebounds + ps.assists - ps.turnovers - 
          (ps.field_goals_attempted - ps.field_goals_made)) / 
         ps.minutes_played) * 100,
        2
    )
)
```

---

## 📊 Monitoring & Maintenance

### Monitor Execution Log
```sql
-- View recent notebook executions
SELECT 
    run_id,
    notebook_name,
    status,
    games_processed,
    error_message,
    start_time,
    end_time
FROM bronze.execution_log
ORDER BY start_time DESC
LIMIT 10;
```

### Optimize Tables
Run periodically (weekly/monthly):
```sql
-- Optimize Delta tables for performance
OPTIMIZE gold.fact_games;
OPTIMIZE gold.dim_team;
OPTIMIZE silver.games_clean;

-- Vacuum old versions (30 days)
VACUUM gold.fact_games RETAIN 30 DAYS;
```

### Monitor Capacity Usage
```sql
-- Estimate storage usage
SELECT 
    table_name,
    COUNT(*) as row_count,
    (SELECT ((size_in_bytes / 1024) / 1024) FROM sys.tables 
     WHERE table_name = <current>) as size_mb
FROM information_schema.tables
WHERE table_schema = 'gold';
```

---

## 🎯 Success Criteria

✅ **Phase 3 Complete When:**

- [ ] All 3 notebooks deployed and tested
- [ ] Bronze layer has 3+ tables with raw data
- [ ] Silver layer shows 0 null values in required fields
- [ ] Gold layer has 8+ tables (3 dimensions, 3 facts, 2 aggregates)
- [ ] Record counts cascade correctly:
  - Bronze: Raw count from API
  - Silver: Deduplicated (≤ Bronze count)
  - Gold: Joined with dimensions
- [ ] Data quality validator reports pass
- [ ] Execution log shows all runs as SUCCESS
- [ ] Power BI can connect via Direct Lake
- [ ] Sample reports execute <5 seconds

---

## 🚨 Troubleshooting

### Issue: "Table already exists" error
**Solution:** Drop table before recreating (only in dev):
```sql
DROP TABLE IF EXISTS bronze.games_raw;
```

### Issue: Null values in Silver layer
**Solution:** Check for nulls and add default values:
```python
.fillna({"field_name": "default_value"})
```

### Issue: Slow Gold layer queries
**Solution:** Run OPTIMIZE:
```sql
OPTIMIZE gold.fact_games;
OPTIMIZE gold.dim_team;
```

### Issue: Power BI can't find tables
**Solution:** Verify Direct Lake attachment and table permissions

---

## 📈 Next Steps (Phase 4+)

**Phase 4 - Real-Time Dashboard (Future):**
- Create Power BI reports with Direct Lake
- Build executive scorecard
- Implement player comparison dashboard
- Create shot chart visualization

**Phase 5 - Orchestration (Future):**
- Deploy Fabric Pipelines for daily refresh
- Implement incremental updates
- Add alert thresholds for anomalies
- Schedule notifications for key events

**Phase 6 - ML/Analytics (Future):**
- Add predictive models (win prediction, MVP race)
- Implement clustering (player archetypes)
- Build recommendation engine
- Create advanced time-series forecasting

---

## 📞 Support & Resources

| Resource | Purpose |
|----------|---------|
| [PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md) | Phase 2 completion details |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Commands and troubleshooting |
| [README.md](../README.md) | Full project overview |
| `/notebooks/` | Notebook source files |
| `/docs/` | Documentation files |

---

## 🎓 Learning Objectives

By completing Phase 3, you'll understand:

✅ **Medallion Architecture**
- Bronze (raw), Silver (clean), Gold (analytics) patterns
- When to use each layer
- Data quality gates

✅ **PySpark Best Practices**
- Explicit schema definition
- Window functions and aggregations
- MERGE INTO for idempotent updates
- Partition strategy

✅ **Fabric Data Engineering**
- Lakehouse organization
- Delta Lake format and optimization
- Direct Lake Power BI connectivity
- Execution logging and monitoring

✅ **Data Quality Engineering**
- Validation frameworks
- Null handling and deduplication
- Referential integrity checks
- Quality flags and reporting

---

**Status:** ✅ Phase 3 Ready for Production Deployment

Generated: 2024 | Version: 1.0
