# Phase 3: Lakehouse Setup & Schema Design

**Status**: Ready to Start  
**Duration**: ~1-2 sessions  
**Prerequisites**: ✅ All Phase 2 tasks complete  

---

## 🎯 Phase 3 Objectives

1. **Create Fabric Lakehouse** - Set up `nba_lakehouse` in your trial workspace
2. **Design Bronze Layer** - Tables for raw NBA API data
3. **Design Silver Layer** - Cleaned and standardized data structures
4. **Design Gold Layer** - Dimensional model tables (Facts and Dimensions)
5. **Deploy Initial Notebooks** - Get ingestion logic into Fabric
6. **Validate End-to-End Flow** - Test data path from API → Bronze → Silver → Gold

---

## 📊 What We'll Build

### Lakehouse: `nba_lakehouse`

The lakehouse will contain all three medallion layers organized by table groups:

#### Bronze Layer (Raw Data)
```
bronze/
├── games_raw/
│   └── Delta table with raw API responses
│   └── Columns: game_id, game_date, game_status, home_team, away_team,
│                score, json_response, ingestion_timestamp
│
├── player_stats_raw/
│   └── Raw player statistics per game
│
└── shots_raw/
    └── Raw shot-level data with coordinates
```

#### Silver Layer (Cleaned & Standardized)
```
silver/
├── games_clean/
│   └── Deduplicated, typed, validated game records
│   └── Status: SCHEDULED, IN_PROGRESS, FINAL
│
├── player_stats_clean/
│   └── Cleaned player performance data
│   └── All percentages calculated, nulls handled
│
└── shots_clean/
    └── Individual shot records with standard coordinates
```

#### Gold Layer (Analytics-Ready)
```
gold/
├── FactGames/
│   └── Game-level facts with surrogate keys
│
├── FactPlayerStats/
│   └── Player-game-level performance facts
│
├── FactShots/
│   └── Individual shot facts with coordinates
│
├── DimPlayer/
│   └── Player dimension (name, position, height, etc.)
│
├── DimTeam/
│   └── Team dimension (name, city, conference, etc.)
│
├── DimDate/
│   └── Date dimension (year, month, week, etc.)
│
└── DimGame/
    └── Game dimension (type, season, playoff status)
```

---

## 🔄 Phase 3 Step-by-Step Plan

### Step 1: Create Lakehouse in Fabric
**Action**: Create the `nba_lakehouse` item in your workspace

**Tools**:
- Fabric Web Interface OR
- Fabric CLI (`fab mkdir`)

**Expected Output**:
- Empty Lakehouse ready for data

---

### Step 2: Design and Create Bronze Schema
**Action**: Create initial Bronze tables

**Tables to Create**:
```sql
-- games_raw: Raw game data from Scoreboard
CREATE TABLE bronze.games_raw (
    game_id STRING NOT NULL,
    game_date DATE NOT NULL,
    game_status INT,
    season INT,
    home_team_id INT,
    away_team_id INT,
    home_team_name STRING,
    away_team_name STRING,
    home_score INT,
    away_score INT,
    quarter INT,
    game_status_text STRING,
    api_response_json STRING,  -- Store full JSON
    ingestion_timestamp TIMESTAMP,
    _processed_date DATE GENERATED ALWAYS AS (CAST(ingestion_timestamp AS DATE))
)
USING DELTA
PARTITIONED BY (_processed_date)
COMMENT 'Raw NBA game data from ScoreboardV3 endpoint'
```

**Rationale**:
- Partition by `_processed_date` for efficient queries
- Store full JSON for audit trail
- One record per game per ingestion
- Handles game updates (status changes)

---

### Step 3: Design and Create Silver Schema
**Action**: Create Bronze → Silver transformation structure

**Tables to Create**:
```sql
-- games_clean: Cleaned and validated game records
CREATE TABLE silver.games_clean (
    game_id STRING NOT NULL,
    game_date DATE NOT NULL,
    season INT,
    game_type STRING,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    home_score INT NOT NULL,
    away_score INT NOT NULL,
    game_status STRING NOT NULL,  -- SCHEDULED, IN_PROGRESS, FINAL
    game_start_time TIMESTAMP,
    game_end_time TIMESTAMP,
    duration_minutes INT,
    data_quality_flag STRING,  -- OK, PARTIAL, ERROR
    silver_loaded_timestamp TIMESTAMP,
    source_file STRING
)
USING DELTA
PARTITIONED BY (game_date)
COMMENT 'Cleaned and deduplicated game records'
```

**Transformations Applied**:
- Remove duplicate records from multiple API calls
- Validate data types and ranges
- Calculate derived fields (duration, status mapping)
- Flag data quality issues
- Add lineage (source_file, loaded_timestamp)

---

### Step 4: Design and Create Gold Schema
**Action**: Create dimensional model structure

**Dimension Tables**:
```sql
-- DimPlayer: Player attributes
CREATE TABLE gold.DimPlayer (
    player_key INT GENERATED ALWAYS AS IDENTITY,
    player_id INT NOT NULL,
    player_name STRING NOT NULL,
    position STRING,
    height STRING,
    weight INT,
    birth_date DATE,
    college STRING,
    country STRING,
    draft_year INT,
    active_flag BOOLEAN,
    dw_insert_ts TIMESTAMP,
    dw_update_ts TIMESTAMP
)
USING DELTA

-- DimTeam: Team attributes
CREATE TABLE gold.DimTeam (
    team_key INT GENERATED ALWAYS AS IDENTITY,
    team_id INT NOT NULL,
    team_code STRING NOT NULL,
    team_name STRING NOT NULL,
    city STRING,
    abbreviation STRING,
    conference STRING,
    division STRING,
    founded_year INT,
    active_flag BOOLEAN,
    dw_insert_ts TIMESTAMP
)
USING DELTA

-- DimDate: Date dimension for analysis
CREATE TABLE gold.DimDate (
    date_key INT,
    full_date DATE NOT NULL,
    year INT,
    quarter INT,
    month INT,
    month_name STRING,
    day_of_month INT,
    day_of_week INT,
    day_name STRING,
    week_of_year INT,
    is_weekend BOOLEAN,
    nba_season_year INT
)
USING DELTA
```

**Fact Tables**:
```sql
-- FactGames: Game-level facts
CREATE TABLE gold.FactGames (
    game_key INT GENERATED ALWAYS AS IDENTITY,
    game_id STRING NOT NULL,
    date_key INT,
    home_team_key INT NOT NULL,
    away_team_key INT NOT NULL,
    home_score INT NOT NULL,
    away_score INT NOT NULL,
    game_status STRING,
    game_type STRING,
    duration_minutes INT,
    dw_insert_ts TIMESTAMP,
    dw_update_ts TIMESTAMP
)
USING DELTA

-- FactPlayerStats: Player-game level facts
CREATE TABLE gold.FactPlayerStats (
    player_stats_key INT GENERATED ALWAYS AS IDENTITY,
    game_key INT NOT NULL,
    date_key INT,
    player_key INT NOT NULL,
    team_key INT NOT NULL,
    minutes_played INT,
    field_goals_made INT,
    field_goals_attempted INT,
    three_pointers_made INT,
    three_pointers_attempted INT,
    free_throws_made INT,
    free_throws_attempted INT,
    rebounds INT,
    assists INT,
    steals INT,
    blocks INT,
    turnovers INT,
    points INT,
    plus_minus INT,
    dw_insert_ts TIMESTAMP
)
USING DELTA

-- FactShots: Individual shot facts
CREATE TABLE gold.FactShots (
    shot_key INT GENERATED ALWAYS AS IDENTITY,
    game_key INT NOT NULL,
    date_key INT,
    player_key INT NOT NULL,
    team_key INT NOT NULL,
    shot_number INT,
    x_coordinate DOUBLE,
    y_coordinate DOUBLE,
    shot_type STRING,
    shot_distance DOUBLE,
    is_made BOOLEAN,
    quarter INT,
    minutes_remaining INT,
    seconds_remaining INT,
    dw_insert_ts TIMESTAMP
)
USING DELTA
```

---

### Step 5: Deploy Initial Ingestion Notebook
**Action**: Create and test ingestion logic

**Notebook**: `Notebooks/01_Ingestion_Bronze_Load.py`

**Functionality**:
```python
# Pseudo-code structure

def ingest_games(game_date):
    """
    1. Call NBA API ScoreboardV3
    2. Extract game details
    3. Store raw response in Bronze layer
    4. Handle duplicates and errors
    """
    
def ingest_player_stats(game_id):
    """
    1. Call NBA API BoxScoreTraditionalV2
    2. Extract player statistics
    3. Store in Bronze layer
    """

def ingest_shots(game_id):
    """
    1. Call NBA API ShotChartDetail
    2. Extract shot coordinates and details
    3. Store in Bronze layer
    """
    
# Main orchestration
if __name__ == "__main__":
    date_to_process = datetime.now().strftime("%Y-%m-%d")
    games = ingest_games(date_to_process)
    
    for game in games:
        ingest_player_stats(game['game_id'])
        ingest_shots(game['game_id'])
```

---

### Step 6: Validate End-to-End Flow
**Action**: Test complete data pipeline

**Test Checklist**:
- [ ] Can read from NBA API
- [ ] Data lands in Bronze tables
- [ ] Data has correct schema
- [ ] Timestamps and metadata present
- [ ] No duplicates on repeated runs
- [ ] Error handling works

**Expected Results**:
- ✅ Sample data in Bronze layer
- ✅ Query results from Silver tables
- ✅ Schema validation passed

---

## 🛠️ Tools & Technologies for Phase 3

| Tool | Use | Notes |
|------|-----|-------|
| **Fabric Lakehouse** | Data storage | OneLake native |
| **Delta Lake** | Table format | ACID, time travel |
| **Fabric Notebooks** | Code execution | PySpark available |
| **SQL Endpoint** | Query interface | Automatic with Lakehouse |
| **Fabric CLI** | Automation | Optional, can use UI |

---

## 📋 Deliverables for Phase 3

By the end of Phase 3, you should have:

1. **Lakehouse Structure**
   - ✓ `nba_lakehouse` created in workspace
   - ✓ Bronze layer tables defined
   - ✓ Silver layer tables defined
   - ✓ Gold layer tables defined

2. **Initial Data**
   - ✓ Sample game data in Bronze
   - ✓ Sample transformed data in Silver
   - ✓ Dimensional tables in Gold (initially empty, ready for data)

3. **Documentation**
   - ✓ Data dictionary updated
   - ✓ Schema designs documented
   - ✓ ETL logic documented

4. **Code**
   - ✓ Ingestion notebook deployed to Fabric
   - ✓ Transformation logic ready for Silver/Gold
   - ✓ Test data validated

---

## 🚀 How to Start Phase 3

When you're ready to begin Phase 3, we'll:

1. **Access Fabric Workspace**
   - Log into your "YOUR_WORKSPACE" workspace
   - Verify access and permissions

2. **Create Lakehouse**
   - Use Fabric UI or CLI to create `nba_lakehouse`
   - Verify creation

3. **Deploy Initial Notebooks**
   - Upload Python scripts as Fabric notebooks
   - Test with sample data

4. **Build and Test Schemas**
   - Create Bronze tables
   - Test data ingestion
   - Validate schema

5. **Design Silver/Gold**
   - Plan transformations
   - Create table structures
   - Document logic

6. **Validate End-to-End**
   - Run full pipeline
   - Verify data quality
   - Test recovery scenarios

---

## 🎓 Learning Objectives for Phase 3

After completing Phase 3, you will understand:

1. **Lakehouse Architecture**
   - How OneLake storage works
   - Delta table benefits and capabilities
   - Partitioning strategies

2. **Data Medallion Pattern**
   - Bronze layer purposes
   - Silver layer transformations
   - Gold layer dimensional modeling

3. **Fabric Development**
   - Creating and managing Lakehouses
   - Writing PySpark code in notebooks
   - Using SQL endpoints for queries

4. **Data Quality**
   - Schema validation
   - Deduplication logic
   - Error handling patterns

---

## ⏱️ Estimated Timeline

- **Step 1-2**: Create Lakehouse, Bronze schema (15 mins)
- **Step 3-4**: Design and create Silver/Gold (30 mins)
- **Step 5**: Deploy ingestion notebook (20 mins)
- **Step 6**: Validate and debug (15 mins)
- **Buffer**: 20 mins for issues

**Total**: 1.5-2 hours for Phase 3

---

## 🔗 Dependencies & Prerequisites

**Must Complete Before Phase 3**:
- ✅ Phase 0: Environment assessment
- ✅ Phase 1: Architecture planning
- ✅ Phase 2: Local development & API exploration

**External Requirements**:
- Fabric workspace access: "YOUR_WORKSPACE"
- Trial or production Fabric capacity
- Internet access to stats.nba.com

**Tools Ready**:
- ✅ Python environment
- ✅ Fabric CLI (fab)
- ✅ nba-api package
- ✅ VS Code

---

## 🎬 Next Actions

**Ready to Start Phase 3?**

1. Confirm Fabric workspace access: "YOUR_WORKSPACE" ✅
2. Verify we can create Lakehouses
3. Decide: Create via Web UI or Fabric CLI
4. Set aside 1-2 hours for execution

**Let me know when you're ready to begin!**

---

**Phase 2 Status**: ✅ COMPLETE  
**Phase 3 Status**: 🟡 PLANNED (Ready to Start)  
**Overall Progress**: 30% → 50% (after Phase 3)
