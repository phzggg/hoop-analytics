# NBA Live Data Platform - Quick Execution Guide

## Deploy Complete ✓

All 4 production-ready PySpark notebooks are now deployed to Fabric workspace **"YOUR_WORKSPACE"**.

### What Was Deployed

```
Workspace: YOUR_WORKSPACE
Lakehouse: nba_lakehouse (auto-created)

Notebooks:
  ✓ Utilities_init_session
  ✓ 01_Ingestion_Setup_Bronze  
  ✓ 02_Transformation_Silver_Layer
  ✓ 03_Dimensional_Model_Gold_Layer
```

## How to Execute

### In Fabric Portal:

1. Go to **Fabric Workspace** → **YOUR_WORKSPACE**
2. Expand **Lakehouses** → Open **nba_lakehouse**
3. Find notebooks in the workspace file explorer

### Run Notebooks in Order

**IMPORTANT: Execute in this exact order!**

#### Step 1: Run Utilities_init_session
- **Time**: ~1 minute
- **Purpose**: Initialize shared utilities and logging framework
- **Action**: Open notebook → Click "Run all"
- **Expected**: No output, but sets up for other notebooks

#### Step 2: Run 01_Ingestion_Setup_Bronze
- **Time**: 5-10 minutes  
- **Purpose**: Create Bronze tables, ingest NBA data from live API
- **Action**: Open notebook → Click "Run all"
- **Expected Output**:
  ```
  ✓ Bronze layer initialized
  ✓ Tables created: brnz_games, brnz_player_stats, brnz_shot_logs, brnz_execution_audit
  ✓ Ingested X game records
  ✓ Execution logged to audit table
  ```

#### Step 3: Run 02_Transformation_Silver_Layer
- **Time**: 5-10 minutes
- **Purpose**: Clean, validate, and transform Bronze data to Silver layer
- **Action**: Open notebook → Click "Run all"
- **Expected Output**:
  ```
  ✓ Silver layer initialized
  ✓ Tables created: slv_games_clean, slv_player_stats_clean, slv_shot_logs_clean
  ✓ Data quality checks passed
  ✓ X rows transformed to Silver
  ✓ Execution logged
  ```

#### Step 4: Run 03_Dimensional_Model_Gold_Layer
- **Time**: 3-5 minutes
- **Purpose**: Create analytical dimensional model (facts + dimensions)
- **Action**: Open notebook → Click "Run all"
- **Expected Output**:
  ```
  ✓ Gold layer initialized
  ✓ Dimension tables created: dim_date, dim_team, dim_player
  ✓ Fact tables created: fact_games, fact_player_games, fact_shots
  ✓ Aggregates created: agg_player_season_stats, agg_team_game_performance
  ✓ Ready for Power BI Direct Lake
  ✓ Execution logged
  ```

## Validation Checklist

After all notebooks complete:

### ✓ Table Verification
Open lakehouse and verify all 15 tables exist:

**Bronze (4)**: 
- brnz_games
- brnz_player_stats
- brnz_shot_logs
- brnz_execution_audit

**Silver (3)**:
- slv_games_clean
- slv_player_stats_clean
- slv_shot_logs_clean

**Gold (8)**:
- dim_date
- dim_team
- dim_player
- fact_games
- fact_player_games
- fact_shots
- agg_player_season_stats
- agg_team_game_performance

### ✓ Data Verification

In Fabric, run SQL queries in the SQL editor to verify:

```sql
-- Check table row counts
SELECT * FROM nba_lakehouse.dbo.brnz_games;
SELECT COUNT(*) as row_count FROM nba_lakehouse.dbo.slv_games_clean;
SELECT COUNT(*) as row_count FROM nba_lakehouse.dbo.fact_games;

-- Check execution logs
SELECT * FROM nba_lakehouse.dbo.brnz_execution_audit ORDER BY execution_timestamp DESC;

-- Check Gold layer quality
SELECT COUNT(*) FROM nba_lakehouse.dbo.dim_player;
SELECT COUNT(*) FROM nba_lakehouse.dbo.dim_team;
SELECT COUNT(*) FROM nba_lakehouse.dbo.agg_player_season_stats;
```

## Troubleshooting

### Issue: Notebook fails immediately

**Check 1**: Look at error message in notebook output
**Check 2**: Verify lakehouse is attached (metadata shows nba_lakehouse)
**Check 3**: Check capacity status (may be suspended)
**Check 4**: Verify network connectivity to stats.nba.com

### Issue: "No games today" - empty result

**Normal behavior**: Happens during NBA off-season or before first game of day
**Solution**: 
- Manually add test data
- Re-run notebook tomorrow
- Or download historical data from sample files

### Issue: Timeout after 5+ minutes

**Cause**: Large historical data load or network latency
**Solution**:
- Increase Spark session timeout in notebook settings
- Reduce batch size for first run
- Check internet connectivity

### Issue: Authentication error

**Solution**:
- Verify user has Editor role in workspace
- Check Fabric trial capacity is active
- Refresh browser and reconnect

## Next Steps (Phase 4)

Once validation complete:

1. **Create Power BI Semantic Model**
   - Connect to Gold layer tables
   - Build measures and relationships
   - Create Direct Lake dataset

2. **Build Power BI Reports**
   - Dashboard: Team performance
   - Dashboard: Player statistics
   - Dashboard: Live game tracking

3. **Set Up Pipelines**
   - Automate daily refresh
   - Schedule notebooks in Fabric Pipelines
   - Add alerting and monitoring

## Documentation Files

Quick reference:
- `PHASE_3_DEPLOYMENT_STATUS.md` - Deployment summary
- `PHASE_3_DEPLOYMENT_CHECKLIST.md` - Full validation guide
- `PHASE_3_QUICK_START.md` - 5-minute overview
- `docs/PHASE_3_IMPLEMENTATION_GUIDE.md` - Technical details

## Support

For issues, check:
1. Notebook output logs (first line of errors)
2. Execution audit table: brnz_execution_audit
3. Fabric workspace capacity metrics
4. Network connectivity to NBA API

---

**Status**: Phase 3 Complete - Ready for Execution  
**Last Updated**: November 11, 2024

You're all set! Run the notebooks in order and let me know if you hit any issues.
