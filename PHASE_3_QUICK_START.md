# Phase 3: Quick Start Deployment Guide
## NBA Live Data Platform - Ready for Fabric

**Total Setup Time:** ~30 minutes  
**Difficulty:** Intermediate (follow steps exactly)  
**Prerequisites:** Fabric workspace access, no coding required  

---

## 🎯 What You'll Have After This

✅ A complete data pipeline in Fabric:
- Bronze layer: Raw NBA API data
- Silver layer: Cleaned, validated data  
- Gold layer: Analytics-ready dimensional model
- **Ready for Power BI Direct Lake connection**

---

## 📋 Checklist Before Starting

- [ ] Access to Fabric workspace: **YOUR_WORKSPACE**
- [ ] Permission level: **Contributor or Admin**
- [ ] Workspace capacity: **Active and assigned**
- [ ] Browser: Modern (Chrome, Edge, or Safari)
- [ ] Internet: Stable connection

---

## 🚀 Step 1: Create Lakehouse (5 minutes)

### In Fabric Web Interface:

1. **Go to workspace:**
   - Open https://app.fabric.microsoft.com
   - Select workspace: **YOUR_WORKSPACE**

2. **Create new lakehouse:**
   - Click **+ New**
   - Select **Lakehouse**
   - Name: `nba_lakehouse`
   - Click **Create**

3. **Wait for completion** (~30-60 seconds)
   - Status changes from "Creating" → "Ready"

**✅ Done!** You now have a lakehouse.

---

## 📓 Step 2: Deploy Notebooks (15 minutes)

### Deploy Notebook 1: Ingestion (Bronze Layer)

1. **Create notebook:**
   - Click **+ New** → **Notebook**
   - Name: `01_Ingestion_Setup_Bronze`

2. **Attach lakehouse:**
   - Look for lakehouse selector (usually top right)
   - Select: `nba_lakehouse`

3. **Add code:**
   - Go to: `Project/notebooks/01_Ingestion_Setup_Bronze.py`
   - Copy entire file content
   - In notebook, paste into Cell 1
   - Click **Publish** (or leave as draft)

4. **Repeat for other 3 notebooks:**

| Notebook | File |
|----------|------|
| `02_Transformation_Silver_Layer` | `02_Transformation_Silver_Layer.py` |
| `03_Dimensional_Model_Gold_Layer` | `03_Dimensional_Model_Gold_Layer.py` |
| `Utilities/init_session` | `Utilities_init_session.py` |

**✅ Done!** All 4 notebooks deployed.

---

## ▶️ Step 3: Run Notebooks in Order (20-30 minutes)

### Run Notebook 1: Bronze Ingestion

1. **Open:** `01_Ingestion_Setup_Bronze`

2. **Review code:** Read through to understand (2-3 min)

3. **Run all cells:**
   - Click **Run All** button (or press Ctrl+Alt+F5)
   - Watch progress in output pane

4. **Expected output:**
   ```
   ✅ Lakehouse connected
   ✅ Schemas created: bronze, silver, gold
   ✅ Bronze tables created
   ✅ Loaded X games to bronze layer
   ✅ Execution logged
   ```

5. **Troubleshooting - No games today?**
   - This is normal if running outside NBA season
   - Or if API has no games scheduled for today
   - Solution: Change Cell 6 to use a past game date:
   ```python
   # Replace this line:
   today = datetime.now().strftime("%Y-%m-%d")
   
   # With this (example - October 22, 2024):
   today = "2024-10-22"
   ```

6. **Wait for completion:** 5-10 minutes ⏱️

**✅ Bronze layer ready!**

---

### Run Notebook 2: Silver Transformation

1. **Open:** `02_Transformation_Silver_Layer`

2. **Click Run All**
   - Wait for completion: 5-10 minutes ⏱️

3. **Expected output:**
   ```
   ✅ Games transformation complete: X records
   📊 Data Quality Report: games_clean
   ✅ Player stats transformation complete: X records
   ✅ Shots transformation complete: X records
   ```

4. **What it does:**
   - Cleans Bronze data
   - Removes duplicates
   - Validates quality
   - Adds calculated fields

**✅ Silver layer ready!**

---

### Run Notebook 3: Gold Dimensional Model

1. **Open:** `03_Dimensional_Model_Gold_Layer`

2. **Click Run All**
   - Wait for completion: 3-5 minutes ⏱️

3. **Expected output:**
   ```
   ✅ DimDate dimension created
   ✅ DimTeam dimension created
   ✅ DimPlayer dimension created
   ✅ FactGames fact table created
   ✅ FactPlayerGames fact table created
   ✅ FactShots fact table created
   ✅ AggPlayerSeasonStats aggregate table created
   ✅ AggTeamGamePerformance aggregate table created
   
   📋 GOLD LAYER SCHEMA SUMMARY
   ✅ gold.dim_date: X rows
   ✅ gold.dim_team: X rows
   ...
   Ready for Power BI Direct Lake!
   ```

**✅ Gold layer ready! 🎉**

---

## ✅ Validation: Verify Everything Works

### Quick Check (2 minutes)

In any notebook, create a new cell with:

```sql
-- Check all tables exist
SELECT 'BRONZE' as layer, COUNT(*) as table_count FROM (
    SELECT 'games_raw' FROM bronze.games_raw LIMIT 1
    UNION ALL
    SELECT 'player_stats_raw' FROM bronze.player_stats_raw LIMIT 1
    UNION ALL
    SELECT 'shots_raw' FROM bronze.shots_raw LIMIT 1
)
UNION ALL
SELECT 'SILVER', COUNT(*) FROM (
    SELECT 'games_clean' FROM silver.games_clean LIMIT 1
    UNION ALL
    SELECT 'player_stats_clean' FROM silver.player_stats_clean LIMIT 1
    UNION ALL
    SELECT 'shots_clean' FROM silver.shots_clean LIMIT 1
)
UNION ALL
SELECT 'GOLD', COUNT(*) FROM (
    SELECT 'fact_games' FROM gold.fact_games LIMIT 1
    UNION ALL
    SELECT 'dim_date' FROM gold.dim_date LIMIT 1
)
```

**Expected:** 3 rows (BRONZE: 3, SILVER: 3, GOLD: multiple tables)

---

## 🎨 Next: Connect Power BI (Phase 4)

Once Gold layer is ready, you can create Power BI dashboards:

1. **Create Semantic Model** in Fabric
   - Type: Direct Lake
   - Select workspace: YOUR_WORKSPACE
   - Select lakehouse: nba_lakehouse

2. **Available tables for reporting:**
   - `fact_games` - Game scores and status
   - `fact_player_games` - Player performance
   - `fact_shots` - Shot-level detail
   - `dim_date`, `dim_team`, `dim_player` - Dimensions

3. **Example reports:**
   - Game results and scores
   - Player statistics by date
   - Team performance comparisons
   - Shot charts with court visualization

---

## 🐛 Common Issues & Quick Fixes

### Issue: "Module not found: nba_api"
**Solution:** In any notebook cell, run:
```python
pip install nba-api
```

### Issue: "No games ingested"
**Reason:** NBA season is typically October-April  
**Solution:** Use a past game date in Cell 6 of Notebook 1

### Issue: "Table already exists" error
**Solution:** This is safe - notebooks handle it automatically  
**Action:** Re-run the notebook (idempotent design)

### Issue: Slow notebook execution
**Reason:** First run may take longer  
**Solution:** Subsequent runs are faster (caching)

### Issue: "Lakehouse not found"
**Solution:** 
1. Verify lakehouse name: `nba_lakehouse` (check spelling)
2. Verify in notebook settings → Default lakehouse
3. Re-attach if needed

---

## 📊 What Each Notebook Does

### Notebook 1: Bronze Layer Setup
- ✅ Creates lakehouse structure
- ✅ Fetches games from NBA API
- ✅ Stores raw data (audit trail)
- ✅ Logs execution

**Time:** 5-10 min  
**Output:** games_raw, player_stats_raw, shots_raw tables

### Notebook 2: Silver Layer Transformation
- ✅ Cleans and standardizes data
- ✅ Validates quality (nulls, ranges)
- ✅ Deduplicates records
- ✅ Adds calculated fields (percentages, etc.)

**Time:** 5-10 min  
**Output:** games_clean, player_stats_clean, shots_clean tables

### Notebook 3: Gold Layer Dimensional Model
- ✅ Creates dimensions (date, team, player)
- ✅ Creates facts (games, player_games, shots)
- ✅ Pre-calculates aggregates
- ✅ Optimizes for Power BI

**Time:** 3-5 min  
**Output:** 8 tables ready for analytics

---

## 🎯 Success Criteria

You're done when you see:

✅ All 4 notebooks show status: **Published**  
✅ All 3 notebooks executed without errors  
✅ Gold layer shows 8+ tables  
✅ No red errors in output  
✅ Execution logs show SUCCESS  
✅ Ready message: "Ready for Power BI Direct Lake!"

---

## 📞 Troubleshooting Resources

| Issue | File |
|-------|------|
| Step-by-step details | PHASE_3_DEPLOYMENT_CHECKLIST.md |
| Complete reference | docs/PHASE_3_IMPLEMENTATION_GUIDE.md |
| Commands & tips | QUICK_REFERENCE.md |
| Architecture | docs/PHASE_3_SUMMARY.md |

---

## ⏱️ Timeline Summary

```
Start
  ↓
Step 1: Create Lakehouse (5 min)
  ↓
Step 2: Deploy 4 Notebooks (15 min)
  ↓
Step 3a: Run Notebook 1 (10 min)
  ↓
Step 3b: Run Notebook 2 (10 min)
  ↓
Step 3c: Run Notebook 3 (5 min)
  ↓
Validation (5 min)
  ↓
✅ DONE! (~50 minutes total)
```

---

## 🎓 What You Learned

- ✅ How to create a Fabric Lakehouse
- ✅ How to deploy PySpark notebooks
- ✅ Medallion architecture (Bronze/Silver/Gold)
- ✅ Data quality validation
- ✅ Delta Lake format
- ✅ Direct Lake Power BI connectivity

---

## 🚀 Next Phase (Optional)

Ready to build dashboards? See Phase 4 guide for:
- Creating Power BI reports
- Building semantic models
- Visualizing with Direct Lake
- Dashboard best practices

---

## 📝 Notes

- **Notebooks are idempotent** - Safe to re-run
- **All data partitioned by date** - Efficient queries
- **Automatic deduplication** - No manual cleanup needed
- **Execution logs track everything** - Audit trail included

---

**Estimated Completion Time:** 30-50 minutes  
**Difficulty Level:** Intermediate (follow steps exactly)  
**Support:** See reference documents above

**Ready to start? Go to Step 1! ⬆️**

---

Generated: 2024 | Version: 1.0 | Status: Ready for Production
