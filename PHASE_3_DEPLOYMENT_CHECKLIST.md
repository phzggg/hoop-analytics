# Phase 3 Deployment Checklist
## NBA Live Data Platform - Production Deployment

**Project:** NBA Live Data Platform  
**Workspace:** YOUR_WORKSPACE (Trial)  
**Phase:** 3 - Lakehouse Setup & PySpark Notebooks  
**Status:** Ready for Deployment  

---

## ✅ Pre-Deployment Verification

- [ ] **Workspace Access Confirmed**
  - [ ] Can access "YOUR_WORKSPACE" workspace in Fabric
  - [ ] Have contributor or higher permissions
  - [ ] Workspace shows "Trial" capacity

- [ ] **Development Environment Ready**
  - [ ] Python 3.13+ installed locally
  - [ ] nba-api package installed (`pip install nba-api`)
  - [ ] Fabric CLI available (`fab --version`)
  - [ ] git configured (skipped per user request)

- [ ] **Network & API Access**
  - [ ] Can reach stats.nba.com
  - [ ] NBA API endpoints responding (test in Phase 2 script)
  - [ ] No proxy/firewall blocking Fabric connections

---

## 🔧 Deployment Steps

### Step 1: Create Lakehouse (5 min)

**Option A: Using Fabric Web UI (Recommended)**
1. [ ] Open workspace: https://app.fabric.microsoft.com → "YOUR_WORKSPACE"
2. [ ] Click **New** → **Lakehouse**
3. [ ] Configure:
   - [ ] Name: `nba_lakehouse`
   - [ ] Description: "NBA Live Data Platform - Medallion Architecture"
4. [ ] Click **Create**
5. [ ] Wait for creation (30-60 seconds)

**Option B: Using Fabric CLI**
```bash
fab workspace list --filter "YOUR_WORKSPACE"
fab item create --type Lakehouse --name nba_lakehouse --workspace "YOUR_WORKSPACE"
```

**Verification:**
- [ ] Lakehouse appears in workspace
- [ ] Can view in Fabric browser
- [ ] Default attachment shows `nba_lakehouse` in notebook settings

---

### Step 2: Deploy Notebooks (15 min)

**For Each Notebook:**

#### Notebook 1: `01_Ingestion_Setup_Bronze`
1. [ ] In workspace, click **New** → **Notebook**
2. [ ] Name: `01_Ingestion_Setup_Bronze`
3. [ ] Set **Default lakehouse:** `nba_lakehouse`
4. [ ] Copy entire content from `/notebooks/01_Ingestion_Setup_Bronze.py`
5. [ ] Paste into notebook (all cells)
6. [ ] Click **Publish** (or leave as draft for testing)

#### Notebook 2: `02_Transformation_Silver_Layer`
1. [ ] Click **New** → **Notebook**
2. [ ] Name: `02_Transformation_Silver_Layer`
3. [ ] Set **Default lakehouse:** `nba_lakehouse`
4. [ ] Copy content from `/notebooks/02_Transformation_Silver_Layer.py`
5. [ ] Paste into notebook
6. [ ] Click **Publish**

#### Notebook 3: `03_Dimensional_Model_Gold_Layer`
1. [ ] Click **New** → **Notebook**
2. [ ] Name: `03_Dimensional_Model_Gold_Layer`
3. [ ] Set **Default lakehouse:** `nba_lakehouse`
4. [ ] Copy content from `/notebooks/03_Dimensional_Model_Gold_Layer.py`
5. [ ] Paste into notebook
6. [ ] Click **Publish**

#### Utility Notebook: `Utilities/init_session`
1. [ ] Click **New** → **Notebook**
2. [ ] Path: `Utilities/init_session` (create folder if needed)
3. [ ] Set **Default lakehouse:** `nba_lakehouse`
4. [ ] Copy content from `/notebooks/Utilities_init_session.py`
5. [ ] Paste into notebook
6. [ ] Click **Publish**

**Verification:**
- [ ] All 4 notebooks appear in workspace
- [ ] Each notebook shows "Published" status
- [ ] Each notebook has default lakehouse attached

---

### Step 3: Run Notebooks in Order (20-30 min total)

#### Run Notebook 1: Bronze Layer
1. [ ] Open `01_Ingestion_Setup_Bronze`
2. [ ] Review code to understand flow
3. [ ] Click **Run All** (or run cells sequentially)
4. [ ] Expected output:
   - [ ] ✅ Lakehouse connected
   - [ ] ✅ Schemas created (bronze/silver/gold)
   - [ ] ✅ Bronze tables created
   - [ ] ✅ Games ingested from NBA API
   - [ ] ✅ Execution logged
5. [ ] Check execution time: **5-10 minutes**

**Troubleshooting Cell 6 (Ingestion):**
If no games found for today:
- [ ] Use a past game date (October 22 - April 13 for regular season)
- [ ] Modify Cell 6:
```python
from datetime import datetime, timedelta
today = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
```

#### Run Notebook 2: Silver Layer
1. [ ] Wait for Notebook 1 to complete fully
2. [ ] Open `02_Transformation_Silver_Layer`
3. [ ] Click **Run All**
4. [ ] Expected output:
   - [ ] ✅ Silver schemas created
   - [ ] ✅ Games transformation complete
   - [ ] ✅ Player stats transformation complete
   - [ ] ✅ Shots transformation complete
   - [ ] ✅ Data quality reports shown
5. [ ] Check execution time: **5-10 minutes**
6. [ ] Review data quality warnings (should be minimal)

#### Run Notebook 3: Gold Layer
1. [ ] Wait for Notebook 2 to complete
2. [ ] Open `03_Dimensional_Model_Gold_Layer`
3. [ ] Click **Run All**
4. [ ] Expected output:
   - [ ] ✅ Dimension tables created (dim_date, dim_team, dim_player)
   - [ ] ✅ Fact tables created (fact_games, fact_player_games, fact_shots)
   - [ ] ✅ Aggregate tables created
   - [ ] ✅ Schema summary displayed
5. [ ] Check execution time: **3-5 minutes**

**Verification After All Notebooks:**
- [ ] View execution logs in Fabric
- [ ] Each run shows green ✅ status
- [ ] No errors in output
- [ ] Total runtime: ~20-30 minutes

---

## 🔍 Post-Deployment Validation

### Validate Bronze Layer
```sql
-- Run in Fabric SQL Editor or notebook

-- Check tables exist
SHOW TABLES IN bronze;

-- Verify data
SELECT COUNT(*) as games_count FROM bronze.games_raw;
SELECT COUNT(*) as player_records FROM bronze.player_stats_raw;
SELECT COUNT(*) as shots_count FROM bronze.shots_raw;

-- Check audit log
SELECT * FROM bronze.execution_log ORDER BY start_time DESC LIMIT 5;
```

**Expected Results:**
- [ ] `games_raw` table exists with records
- [ ] `player_stats_raw` table exists with records
- [ ] `shots_raw` table exists
- [ ] Execution log shows successful run

### Validate Silver Layer
```sql
-- Check tables exist
SHOW TABLES IN silver;

-- Verify no nulls in required fields
SELECT 
    'games_clean' as table_name,
    COUNT(*) FILTER (WHERE game_id IS NULL) as null_game_ids
FROM silver.games_clean
UNION ALL
SELECT 
    'player_stats_clean',
    COUNT(*) FILTER (WHERE player_id IS NULL)
FROM silver.player_stats_clean;

-- Check deduplication effectiveness
SELECT 
    COUNT(DISTINCT game_id) as unique_games
FROM silver.games_clean;
```

**Expected Results:**
- [ ] `games_clean`, `player_stats_clean`, `shots_clean` exist
- [ ] Required fields have 0 nulls
- [ ] No unintended duplicates

### Validate Gold Layer
```sql
-- Check all tables exist
SHOW TABLES IN gold;

-- Verify dimensions populated
SELECT COUNT(*) as date_keys FROM gold.dim_date;
SELECT COUNT(*) as teams FROM gold.dim_team;
SELECT COUNT(*) as players FROM gold.dim_player;

-- Verify facts populated
SELECT COUNT(*) as game_facts FROM gold.fact_games;
SELECT COUNT(*) as player_game_facts FROM gold.fact_player_games;
SELECT COUNT(*) as shot_facts FROM gold.fact_shots;

-- Check aggregates
SELECT COUNT(*) as season_stats FROM gold.agg_player_season_stats;
```

**Expected Results:**
- [ ] All 8 Gold tables exist (3 dimensions + 3 facts + 2 aggregates)
- [ ] `dim_date` has ~1,460 rows (4 years of dates)
- [ ] `dim_team` has ~30-32 rows (NBA teams)
- [ ] `dim_player` has 500+ rows
- [ ] `fact_games` has records
- [ ] Record counts flow correctly (Bronze > Silver ≥ Gold)

### Validate Referential Integrity
```sql
-- Check foreign key relationships
SELECT COUNT(*) as unmatched_home_teams
FROM gold.fact_games fg
LEFT JOIN gold.dim_team dt 
    ON fg.home_team_key = dt.team_key
WHERE dt.team_key IS NULL;

-- Should be 0
```

**Expected Results:**
- [ ] All foreign keys match (0 nulls after LEFT JOIN)
- [ ] No orphaned fact records

### Validate Schema Quality
```sql
-- Check for data quality flags
SELECT 
    'games_clean' as table_name,
    COUNT(*) FILTER (WHERE dq_validation_status = 'VALIDATED') as valid_records
FROM silver.games_clean
UNION ALL
SELECT 
    'player_stats_clean',
    COUNT(*) FILTER (WHERE dq_validation_status = 'VALIDATED')
FROM silver.player_stats_clean;

-- All should show record count (not 0)
```

**Expected Results:**
- [ ] All records marked as VALIDATED
- [ ] 0 failed validation records

---

## 🎨 Prepare for Power BI (Optional - Phase 4)

If ready to connect Power BI now:

- [ ] **Note workspace ID** for Direct Lake setup
  ```bash
  # In Notebook, Cell 1 shows: "Workspace ID: xxxxx"
  ```

- [ ] **List available tables** for Power BI:
  ```sql
  SELECT table_name 
  FROM information_schema.tables 
  WHERE table_schema = 'gold';
  ```

- [ ] **Expected tables for Power BI Direct Lake:**
  - [ ] `fact_games` (main facts)
  - [ ] `fact_player_games` (player performance)
  - [ ] `fact_shots` (shot detail)
  - [ ] `dim_date`, `dim_team`, `dim_player` (dimensions)
  - [ ] `agg_player_season_stats`, `agg_team_game_performance` (aggregates)

- [ ] **Verify column names** match expected conventions (ready for Power BI):
  ```sql
  DESCRIBE gold.fact_games;
  DESCRIBE gold.dim_player;
  ```

---

## 🐛 Common Issues & Resolution

| Issue | Solution | Status |
|-------|----------|--------|
| "No games found for today" | Use past game date in Cell 6 | ✅ Resolved |
| "Table already exists" | Drop table first (dev only) | ✅ Resolved |
| Null values in Silver | Check filtering logic in transformation | ✅ Resolved |
| Slow Gold layer queries | Run OPTIMIZE after build | ⏳ Pending |
| Power BI can't connect | Verify Direct Lake setup | ⏳ Pending |

---

## 📊 Performance Benchmarks

| Operation | Target Time | Actual | Status |
|-----------|------------|--------|--------|
| Bronze table creation | <1 min | TBD | ⏳ |
| Games ingestion (1 day) | <2 min | TBD | ⏳ |
| Silver transformation | 5-10 min | TBD | ⏳ |
| Gold dimensional build | 3-5 min | TBD | ⏳ |
| **Total Pipeline** | **15-20 min** | TBD | ⏳ |

---

## 📝 Documentation Review

Before moving to Phase 4, verify these docs are updated:

- [ ] `/docs/PHASE_3_IMPLEMENTATION_GUIDE.md` - ✅ Created
- [ ] `/PHASE_3_DEPLOYMENT_CHECKLIST.md` - ✅ This file
- [ ] `/README.md` - Updated with Phase 3 info
- [ ] `/QUICK_REFERENCE.md` - Updated with Phase 3 commands
- [ ] Sample notebooks in `/notebooks/` - ✅ All 4 created

---

## ✅ Phase 3 Sign-Off

**Deployment Complete When:**
- [ ] All 4 notebooks created and published
- [ ] All 3 notebooks executed successfully
- [ ] All validation queries pass
- [ ] No errors in execution logs
- [ ] Data flows correctly: Bronze → Silver → Gold
- [ ] 8+ Gold tables created and populated
- [ ] Ready for Phase 4 (Power BI dashboards)

---

## 📞 Next Steps

**Immediate (Day 1):**
1. [ ] Complete all deployment steps above
2. [ ] Run all validation queries
3. [ ] Document any issues in troubleshooting

**Short Term (Week 1):**
1. [ ] Set up Power BI Direct Lake connection (Phase 4)
2. [ ] Create initial dashboard reports
3. [ ] Validate report performance

**Medium Term (Week 2+):**
1. [ ] Deploy Fabric Pipelines for daily refresh (Phase 5)
2. [ ] Implement alerting on data quality
3. [ ] Add incremental update logic

---

## 📚 Reference Materials

| Document | Purpose |
|----------|---------|
| [PHASE_3_IMPLEMENTATION_GUIDE.md](PHASE_3_IMPLEMENTATION_GUIDE.md) | Complete implementation reference |
| [README.md](../README.md) | Project overview |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Commands and troubleshooting |
| [PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md) | Phase 2 completion details |

---

**Last Updated:** 2024  
**Status:** Ready for Deployment  
**Version:** 1.0

