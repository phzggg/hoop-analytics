# Notebooks Reorganization - Visual Guide

## Overview

✅ All 4 notebooks reorganized from **1 cell → 7 cells each**

---

## 📊 Cell Structure Map

### Utilities_init_session
```
┌─────────────────────────────────────────────────────────────┐
│ Cell 1: Configure Spark Session                             │
│  • Adaptive execution settings                              │
│  • Delta Lake optimization                                  │
│  • Native execution engine                                  │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 2: Verify Lakehouse Connection                         │
│  • Test connection                                          │
│  • Get workspace info                                       │
│  • Validate access                                          │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 3: Create Schema Structure                             │
│  • Create bronze schema                                     │
│  • Create silver schema                                     │
│  • Create gold schema                                       │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 4: Common Utility Functions                            │
│  • Logger functions                                         │
│  • DataFrame utilities                                      │
│  • File operations                                          │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 5: ExecutionLogger Class                               │
│  • Track notebook execution                                 │
│  • Log metrics and timing                                   │
│  • Store in audit table                                     │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 6: DataFrameUtils & FileSystemUtils                    │
│  • DataFrame operations                                     │
│  • Schema validation                                        │
│  • File system utilities                                    │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 7: TableUtils & PerformanceMonitor                     │
│  • Table creation and management                            │
│  • Performance tracking                                     │
│  • Query optimization helpers                               │
└─────────────────────────────────────────────────────────────┘
```

---

### 01_Ingestion_Setup_Bronze
```
┌─────────────────────────────────────────────────────────────┐
│ Cell 1: Configure Spark & Imports                           │
│  • Load Utilities (via %run)                                │
│  • Import libraries                                         │
│  • Setup logging                                            │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 2: Define Bronze Layer Schemas                         │
│  • games_raw_schema                                         │
│  • player_stats_raw_schema                                  │
│  • shot_logs_raw_schema                                     │
│  • execution_audit_schema                                   │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 3: Create Bronze Tables                                │
│  • CREATE TABLE IF NOT EXISTS brnz_games                    │
│  • CREATE TABLE IF NOT EXISTS brnz_player_stats             │
│  • CREATE TABLE IF NOT EXISTS brnz_shot_logs                │
│  • CREATE TABLE IF NOT EXISTS brnz_execution_audit          │
│  • Partitioned by game_date                                 │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 4: NBA API Integration - Scoreboard                    │
│  • Fetch current games via nba-api                          │
│  • Parse response                                           │
│  • Handle errors and retries                                │
│  • 2-second rate limiting                                   │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 5: MERGE INTO Games - Idempotent Insert                │
│  • MERGE INTO brnz_games                                    │
│  • Match on game_id                                         │
│  • Insert new games                                         │
│  • Update existing games with new scores                    │
│  • Count rows inserted/updated                              │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 6: Fetch & Load Player Statistics                      │
│  • For each game, fetch player box scores                   │
│  • Parse player statistics                                  │
│  • MERGE INTO brnz_player_stats                             │
│  • Handle rate limiting                                     │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 7: Log Execution to Audit Table                        │
│  • INSERT INTO brnz_execution_audit                         │
│  • Record: timestamp, rows_loaded, status                   │
│  • Print execution summary                                  │
│  • SUCCESS/FAILURE status                                   │
└─────────────────────────────────────────────────────────────┘
```

---

### 02_Transformation_Silver_Layer
```
┌─────────────────────────────────────────────────────────────┐
│ Cell 1: Setup & Imports                                     │
│  • Load Utilities                                           │
│  • Import PySpark functions                                 │
│  • Configure logging                                        │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 2: Data Quality Validator Framework                    │
│  • Class: DataQualityValidator                              │
│  • Methods:                                                 │
│    - check_completeness()                                   │
│    - check_uniqueness()                                     │
│    - check_validity()                                       │
│    - check_consistency()                                    │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 3: Create Silver Tables                                │
│  • Define schemas with calculated fields                    │
│  • CREATE TABLE slv_games_clean                             │
│  • CREATE TABLE slv_player_stats_clean                      │
│  • CREATE TABLE slv_shot_logs_clean                         │
│  • Add quality tracking columns                             │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 4: Transform Games Data                                │
│  • Read from brnz_games                                     │
│  • Deduplicate records                                      │
│  • Add calculated fields                                    │
│  • Run data quality checks                                  │
│  • INSERT INTO slv_games_clean                              │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 5: Transform Player Stats                              │
│  • Read from brnz_player_stats                              │
│  • Calculate shooting percentages                           │
│  • Add quality indicators                                   │
│  • Run validation checks                                    │
│  • INSERT INTO slv_player_stats_clean                       │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 6: Transform Shot Data                                 │
│  • Read from brnz_shot_logs                                 │
│  • Standardize coordinates                                  │
│  • Add calculated fields                                    │
│  • Quality validation                                       │
│  • INSERT INTO slv_shot_logs_clean                          │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 7: Quality Validation & Logging                        │
│  • Run post-transformation checks                           │
│  • Validate row counts                                      │
│  • Check for NULLs in key fields                            │
│  • Log execution to audit table                             │
│  • Print transformation summary                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 03_Dimensional_Model_Gold_Layer
```
┌─────────────────────────────────────────────────────────────┐
│ Cell 1: Setup & Imports                                     │
│  • Load Utilities                                           │
│  • Import Window & aggregation functions                    │
│  • Setup logging                                            │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 2: Create Dimension Schemas                            │
│  • dim_date schema (calendar dimension)                     │
│  • dim_team schema (team dimension)                         │
│  • dim_player schema (player dimension)                     │
│  • With surrogate keys and attributes                       │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 3: Build & Load Date Dimension                         │
│  • Generate dates for full season                           │
│  • Add year, month, day, quarter, week                      │
│  • CREATE TABLE dim_date                                    │
│  • INSERT pre-calculated date records                       │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 4: Build & Load Team & Player Dimensions               │
│  • Extract unique teams from silver tables                  │
│  • Generate surrogate keys (ROW_NUMBER)                     │
│  • Extract unique players                                   │
│  • CREATE and INSERT to dim_team and dim_player             │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 5: Create Fact Tables                                  │
│  • fact_games: One row per game                             │
│  • fact_player_games: One row per player-game               │
│  • fact_shots: One row per shot taken                       │
│  • Join with dimensions for surrogate keys                  │
│  • CREATE and INSERT records                                │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 6: Create Materialized Aggregates                      │
│  • agg_player_season_stats (stats by player-season)         │
│  • agg_team_game_performance (stats by team-game)           │
│  • Pre-computed for fast queries                            │
│  • CREATE and INSERT aggregate records                      │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Cell 7: Validation & Direct Lake Readiness                  │
│  • Count rows in all Gold tables                            │
│  • Validate data relationships                              │
│  • Verify partitioning                                      │
│  • Log execution summary                                    │
│  • Ready for Power BI Direct Lake                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Data Flow Through Cells

```
┌──────────────────┐
│  Utilities Init  │  ← Start here (1st notebook)
│   (7 cells)      │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Bronze Ingest   │  ← Run 2nd
│   (7 cells)      │     ├─ Config & Schema
│   Raw NBA API    │     ├─ API calls
│   Data           │     └─ Idempotent merge
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Silver Transfm  │  ← Run 3rd
│   (7 cells)      │     ├─ Quality checks
│   Clean Data     │     ├─ Deduplication
│   Validated      │     └─ Calculated fields
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Gold Dimensions │  ← Run 4th
│   (7 cells)      │     ├─ Fact tables
│   Facts &        │     ├─ Dimensions
│   Dimensions     │     └─ Aggregates
└────────┬─────────┘
         │
         ↓
    ✅ Ready for Power BI Direct Lake!
```

---

## 🎯 Cell Execution Tips

### Run All Cells (Recommended First Time)
1. Open notebook
2. Click **"Run all"** button
3. Cells execute sequentially
4. Each waits for previous to complete

### Run Specific Cell
1. Click on cell
2. Press **Ctrl+Enter** or click **"Run cell"**
3. Only that cell executes
4. Useful for debugging

### Run Cells Up To Current
1. Click on any cell
2. Press **Ctrl+Shift+Enter**
3. Executes all cells up to current one

---

## ✅ Verification Checklist

After reorganization:

- [x] All 4 notebooks show 7 cells each
- [x] Each cell has a descriptive header
- [x] Cell boundaries are clear (separation lines)
- [x] Code flows logically from cell to cell
- [x] No cell is empty
- [x] Each cell has single responsibility
- [x] Variables carry over between cells (as expected)

---

## 📝 Example: Running Cell 3 from Bronze Notebook

**What you'll see**:
```
Cell 3: Create Bronze Tables
==============================

[Output]
✅ Table created: brnz_games
✅ Table created: brnz_player_stats  
✅ Table created: brnz_shot_logs
✅ Table created: brnz_execution_audit

All Bronze tables ready for ingestion!
```

Then you can proceed to Cell 4 (API calls) knowing tables are ready.

---

## 🚀 Next Steps

1. **Open Fabric** → workspace "YOUR_WORKSPACE"
2. **Select any notebook** (try Utilities first)
3. **Look at left sidebar** - see the 7 cells listed
4. **Click through cells** to see each section
5. **Run cells** individually or all together
6. **Monitor progress** in output for each cell

---

**Status**: ✅ Reorganization Complete  
**Action**: Open notebooks in Fabric to see the new cell structure!
