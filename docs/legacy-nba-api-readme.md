# Historical project notes

The following section is preserved for context only. It describes an older
`nba_api` prototype and planned work, **not** the current ESPN pipeline,
semantic model or active Fabric App. Its paths, status claims and instructions
have not been revalidated and should not be used for deployment. Some original
links no longer resolve. See the [current README](../README.md) instead.

A real-world data engineering project building an automated NBA statistics platform using Microsoft Fabric.

## 🎯 Project Objective

Build a dynamic, continuously-updated data platform that ingests live NBA game data, applies medallion architecture transformations, and exposes analytics through a Power BI semantic model.

### Expected Capabilities

- ✅ Automatically retrieve NBA games scheduled for a given day
- ✅ Identify new games vs. previously processed games
- ✅ Retrieve updated game information and player statistics
- ✅ Ingest shot-level data with court coordinates
- ✅ Store raw data in a Lakehouse (Bronze layer)
- ✅ Transform and organize data (Silver and Gold layers)
- ✅ Orchestrate the entire process using Microsoft Fabric
- ✅ Build a dimensional data model for analytics
- ✅ Create a Semantic Model with validated DAX measures
- ✅ Prepare infrastructure for a future Fabric App

## 📊 Architecture

```
NBA API (nba_api)
       ↓
Ingestion Layer (Python Notebooks)
       ↓
Fabric Lakehouse
├── Bronze Layer (Raw JSON)
├── Silver Layer (Cleaned Delta Tables)
└── Gold Layer (Dimensional Model)
       ↓
Semantic Model (Power BI)
       ↓
Analytics & Future Fabric App
```

### Data Flow

1. **Ingestion**: Retrieve data from NBA API endpoints
2. **Bronze**: Store raw API responses as-is (audit trail)
3. **Silver**: Clean, standardize, and deduplicate (PySpark)
4. **Gold**: Build dimensional model (facts and dimensions)
5. **Analytics**: Connect semantic model via Direct Lake

## 🏗️ Project Structure

```
hoop-analytics/
├── src/
│   ├── ingestion/          # NBA API data fetching logic
│   ├── transformations/    # PySpark transformation notebooks
│   └── orchestration/      # Data Factory pipeline definitions
├── notebooks/              # Fabric notebooks (sync from here)
├── tests/                  # Data quality and unit tests
├── data/
│   └── sample/            # Sample API responses for testing
├── config/                # Configuration files
├── docs/                  # Architecture and design documentation
├── logs/                  # Execution logs
└── README.md
```

## 🔧 Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Data Source** | nba_api (Python) | Free NBA API access |
| **Ingestion** | Python + Notebooks | API interaction and data fetching |
| **Storage** | Fabric Lakehouse | Unified OneLake storage |
| **Transformation** | PySpark | Data cleaning and modeling |
| **Orchestration** | Fabric Data Factory | Pipeline scheduling and coordination |
| **Analytics** | Power BI Semantic Model | DAX and data exploration |

## 📋 Prerequisites

- ✅ Microsoft Fabric workspace access (trial or production)
- ✅ Python 3.13+
- ✅ VS Code
- ✅ Microsoft Fabric CLI (`fab`)
- ✅ Internet access to NBA API

### Python Dependencies

```bash
pip install requests pandas python-dotenv pytest
```

## 📈 Project Status

| Phase | Task | Status | Artifacts |
|-------|------|--------|-----------|
| **0** | Environment Assessment | ✅ Complete | Python, Fabric CLI, nba-api verified |
| **1** | Architecture Design | ✅ Complete | Medallion pattern, schema design, data flow |
| **2** | API Validation | ✅ Complete | explore_nba_api_v2.py, sample data collected |
| **3** | Lakehouse Setup & Notebooks | 🟢 Ready | 3 production PySpark notebooks + utilities |
| **4** | Power BI Dashboards | ⏳ Planned | Direct Lake connectivity, reports |
| **5** | Orchestration & Pipelines | ⏳ Planned | Daily refresh, incremental updates |
| **6** | ML & Advanced Analytics | ⏳ Planned | Predictions, clustering, forecasting |

## 🚀 Getting Started

### Phase 3: Lakehouse Setup (CURRENT)

**Quick Start (3 steps, ~30 minutes):**

1. **Create Lakehouse** in Fabric: `nba_lakehouse`
2. **Deploy 4 Notebooks** from `/notebooks/`:
   - `01_Ingestion_Setup_Bronze` - Create tables, ingest games
   - `02_Transformation_Silver_Layer` - Clean data, validate quality
   - `03_Dimensional_Model_Gold_Layer` - Build dimensional model
   - `Utilities/init_session` - Shared utilities

3. **Run Notebooks** in order → Gold layer ready for Power BI

**See:** [PHASE_3_DEPLOYMENT_CHECKLIST.md](PHASE_3_DEPLOYMENT_CHECKLIST.md)  
**Reference:** [PHASE_3_IMPLEMENTATION_GUIDE.md](docs/PHASE_3_IMPLEMENTATION_GUIDE.md)

---

### Previous Phases (Completed)

#### 1. Environment Setup

```bash
# Create a Python virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\Activate.ps1

# Or (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install requests pandas python-dotenv pytest
```

### 2. Configuration

Create a `.env` file in the project root:

```ini
# Fabric Configuration
FABRIC_WORKSPACE_NAME=YOUR_WORKSPACE
FABRIC_LAKEHOUSE_NAME=nba_lakehouse

# NBA API Configuration
NBA_API_ENABLE=true
NBA_API_TIMEOUT=30
NBA_API_RETRIES=3
NBA_API_BACKOFF_FACTOR=1.5

# Application Settings
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### 3. Explore the NBA API

```bash
# Start with Phase 2: API Exploration
python src/ingestion/explore_nba_api.py

# This will:
# - Test NBA API connectivity
# - Verify endpoint availability
# - Fetch sample data for validation
# - Display data structure
```

## 📚 Project Phases

### ✅ Phase 0: Environment Assessment
Completed. Environment verified, tools installed.

### 🔄 Phase 1: Architecture & Planning
Completed. Schema designed, medallion architecture defined.

### 🚀 Phase 2: Project Structure & Local Development
**CURRENT** - Creating local project structure, exploring NBA API.

### Phase 3: Lakehouse Setup
- Create nba_lakehouse in Fabric
- Define Bronze layer schema
- Deploy initial notebooks

### Phase 4: Ingestion Pipeline
- Implement data fetching logic
- Create Bronze layer storage
- Build error handling and retries

### Phase 5: Transformations
- Implement Silver layer logic
- Implement Gold layer dimensional model
- Create data quality checks

### Phase 6: Orchestration
- Build Data Factory pipeline
- Configure scheduling
- Set up monitoring

### Phase 7: Semantic Model
- Create Power BI semantic model
- Define relationships
- Implement DAX measures

### Phase 8: Documentation & Deployment
- Complete documentation
- Create runbooks
- Prepare for production

## 📖 Documentation

- [Architecture Design](docs/ARCHITECTURE.md) - Detailed architecture and design decisions
- [NBA API Reference](docs/NBA_API_REFERENCE.md) - Endpoints, parameters, and response formats
- [Data Dictionary](docs/DATA_DICTIONARY.md) - Schema and field definitions
- [Medallion Architecture](docs/MEDALLION_ARCHITECTURE.md) - Bronze/Silver/Gold design

## 🔍 API Endpoints

This project uses the following NBA API endpoints:

- **ScoreboardV3**: Game schedules and status for a specific date
- **BoxScoreTraditionalV3**: Individual player statistics per game
- **ShotChartDetail**: Shot-level data including court coordinates
- **PlayByPlayV3**: (Optional) Event-level game information

**Important**: The nba_api is not an official NBA API. It reverse-engineers publicly available endpoints from NBA.com. Use responsibly and respect API rate limits.

## 💾 Data Retention

- **Bronze**: Keep indefinitely (audit trail)
- **Silver**: Keep indefinitely (transformation source)
- **Gold**: Keep current + 2 years for analytics
- **Logs**: Keep 6 months

## 📊 Expected Data Volume

Estimated storage needs (yearly):

- Bronze layer: ~50-100 GB
- Silver layer: ~30-50 GB
- Gold layer: ~10-20 GB
- **Total: ~100-150 GB**

This assumes ~1,230 games/season with detailed shot and play-by-play data.

## ⚠️ Important Notes

1. **Not Official**: The NBA API is not an officially documented API. Endpoints may change.
2. **Rate Limits**: Respect NBA.com rate limiting. Current implementation uses conservative delays.
3. **Terms of Service**: Verify compliance with NBA.com terms before production use.
4. **Credentials**: Never commit API keys or credentials. Use environment variables.
5. **Data Freshness**: Data reflects NBA.com availability. Some live data may be delayed.

## 🎓 Learning Outcomes

By completing this project, you will have practical experience with:

- Data ingestion from REST APIs
- Error handling and retry strategies
- Medallion architecture implementation
- PySpark for data transformation
- Dimensional modeling for analytics
- Fabric Data Factory orchestration
- Direct Lake and semantic models
- DAX measure development
- Data quality validation
- Production-grade logging and monitoring

## 📞 Support

For issues or questions:
1. Check execution logs in `logs/`
2. Review error messages in data quality reports
3. Consult documentation in `docs/`
4. Review sample data in `data/sample/`

## 📝 License

This project is for educational and development purposes. Ensure compliance with NBA.com terms of service.

---

**Status**: Phase 2 - Project Structure & Local Development  
**Last Updated**: 2026-11-11  
**Next Phase**: Phase 3 - Lakehouse Setup
