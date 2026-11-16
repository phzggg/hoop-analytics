# HoopMetrics - Quick Reference Guide

**Last Updated:** November 16, 2026 | **Status:** Repository Reorganized ✅

## 🎯 Find What You Need

### 📱 Working on the Fabric App?
```bash
cd app_nba_stats/
npm install      # Install dependencies
npm test        # Run tests
npm run dev     # Start development server
npm run build   # Build for production
```
📂 **Location:** `/app_nba_stats/`  
📚 **Docs:** [`docs/fabric-app.md`](./docs/fabric-app.md)

### 📔 Working on Data Pipelines?

#### Bronze Layer (Raw Data Ingestion)
```bash
# Data collection from ESPN
notebooks/bronze/11_ESPN_Bronze.py
notebooks/bronze/14_ESPN_Players_Bronze.py
```

#### Silver Layer (Data Transformation)
```bash
# Clean and transform bronze data
notebooks/silver/12_ESPN_Silver.py
notebooks/silver/15_ESPN_Players_Silver.py
```

#### Gold Layer (Dimensional Modeling)
```bash
# Analytics-ready data for Power BI
notebooks/gold/13_ESPN_Gold.py
notebooks/gold/16_ESPN_Players_Gold.py
```

📂 **Location:** `/notebooks/{bronze|silver|gold}/`  
📚 **Docs:** [`docs/data-engineering.md`](./docs/data-engineering.md)

### 🏗️ Working on Fabric Artifacts?

**Pipeline Definitions:**
```
fabric/pipeline/ESPN_Process_Batches.json
```

**Semantic Model:**
```
fabric/semantic-model/definition/
├── database.tmdl
├── model.tmdl
├── relationships.tmdl
├── expressions.tmdl
└── tables/
```

📂 **Location:** `/fabric/`  
📚 **Docs:** 
- [`docs/architecture.md`](./docs/architecture.md)
- [`docs/semantic-model.md`](./docs/semantic-model.md)

### 🔧 Configuration & Setup

**Environment Variables:**
- `.env.example` - Template (committed)
- `.env.local` - Local development (not committed)
- `.env.production` - Production settings

**Configuration Templates:**
```bash
cd config/
# View available configuration templates
```

📂 **Location:** `/config/`  
📚 **Docs:** [`docs/implementation-guide.md`](./docs/implementation-guide.md)

### 📊 Sample Data

```bash
cd data/sample/
# Browse sample datasets for testing
```

📂 **Location:** `/data/`

---

## 📚 Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| [`README.md`](./README.md) | Project overview and quick start | Everyone |
| [`REPOSITORY_STRUCTURE.md`](./REPOSITORY_STRUCTURE.md) | Detailed structure explanation | Everyone |
| [`MIGRATION_NOTES.md`](./MIGRATION_NOTES.md) | Breaking changes and updates | DevOps/CI-CD |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Development guidelines | Contributors |
| [`docs/architecture.md`](./docs/architecture.md) | System design and data flow | Architects/Leads |
| [`docs/data-engineering.md`](./docs/data-engineering.md) | Medallion architecture details | Data Engineers |
| [`docs/fabric-app.md`](./docs/fabric-app.md) | App features and components | Frontend Developers |
| [`docs/semantic-model.md`](./docs/semantic-model.md) | Model tables and measures | BI/Analytics |
| [`docs/implementation-guide.md`](./docs/implementation-guide.md) | Setup and deployment | DevOps/Operators |
| [`docs/ux-ui-decisions.md`](./docs/ux-ui-decisions.md) | UI/UX rationale | Product/UX |
| [`docs/lessons-learned.md`](./docs/lessons-learned.md) | Development insights | Team/Learning |
| [`docs/security-and-rights.md`](./docs/security-and-rights.md) | Security and licensing | Compliance |

---

## 🚀 Common Tasks

### Starting Development
```bash
# 1. Clone the repository
git clone https://github.com/phzggg/hoop-analytics.git
cd hoop-analytics

# 2. Set up development environment
cp app_nba_stats/.env.example app_nba_stats/.env.local

# 3. Install dependencies
cd app_nba_stats
npm install

# 4. Start development server
npm run dev
```

### Running Tests
```bash
cd app_nba_stats
npm test
```

### Building for Production
```bash
cd app_nba_stats
npm run build
```

### Publishing the App
```bash
cd app_nba_stats
npx rayfin login
npx rayfin up
npx rayfin up status
```

### Updating Notebooks in Fabric
1. Edit notebook in `/notebooks/{bronze|silver|gold}/`
2. Upload to Fabric workspace
3. Test execution
4. Update pipeline if needed

### Deploying Semantic Model
1. Update TMDL files in `/fabric/semantic-model/definition/`
2. Replace environment identifiers
3. Deploy using Fabric APIs or CLI
4. Verify model refresh

---

## 🔄 Git Workflow

### View Recent Changes
```bash
git log --oneline -10
```

### See What Changed
```bash
git status
git diff
```

### Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# Make changes
git add .
git commit -m "feat: description of changes"
git push origin feature/your-feature-name
# Create PR on GitHub
```

### Latest Reorganization Commits
```
f074511 docs: add migration notes for repository reorganization
29a9d0d refactor: remove redundant README and reorganize repository structure
```

---

## 📊 Directory Quick Reference

```
hoop-analytics/
│
├── app_nba_stats/           # Fabric App - React + TypeScript
│   ├── src/                 # Source code
│   ├── scripts/             # Build & deployment scripts
│   └── package.json         # Dependencies
│
├── notebooks/               # Data pipelines (Medallion Architecture)
│   ├── bronze/              # Raw data ingestion
│   ├── silver/              # Data transformation
│   ├── gold/                # Dimensional modeling
│   └── utilities/           # Helper functions
│
├── fabric/                  # Fabric artifacts
│   ├── pipeline/            # Pipeline definitions
│   └── semantic-model/      # Power BI semantic model (TMDL)
│
├── docs/                    # Documentation
├── config/                  # Configuration templates
├── data/                    # Sample data
├── tests/                   # Test suites
├── src/                     # Backend source
├── .github/                 # GitHub workflows & templates
│
├── README.md                # Main documentation
├── REPOSITORY_STRUCTURE.md  # Structure guide
├── MIGRATION_NOTES.md       # Migration instructions
└── CONTRIBUTING.md          # Contribution guidelines
```

---

## 🆘 Troubleshooting

### Path Not Found Errors?
Check [`MIGRATION_NOTES.md`](./MIGRATION_NOTES.md) - paths changed in reorganization:
- `fabric-artifacts/` → `fabric/`
- `semantic-model/` → `fabric/semantic-model/`
- `notebooks/` → `notebooks/{bronze|silver|gold|utilities}/`

### Need Setup Help?
See [`docs/implementation-guide.md`](./docs/implementation-guide.md)

### Want to Understand the Architecture?
Start with [`docs/architecture.md`](./docs/architecture.md)

### Looking for Best Practices?
Check [`docs/lessons-learned.md`](./docs/lessons-learned.md)

---

## 👥 Need to Know?

- **Project Lead:** Contact repository owner
- **Data Engineering:** See [`docs/data-engineering.md`](./docs/data-engineering.md)
- **Frontend/App:** See [`docs/fabric-app.md`](./docs/fabric-app.md)
- **Analytics/BI:** See [`docs/semantic-model.md`](./docs/semantic-model.md)
- **DevOps/Deployment:** See [`docs/implementation-guide.md`](./docs/implementation-guide.md) and [`MIGRATION_NOTES.md`](./MIGRATION_NOTES.md)

---

## ✨ Quick Links

- 🌐 **Live App:** https://vast-aspen-e38fa96203-brazilsouth.webapp.fabricapps.net/
- 📖 **Main README:** [`README.md`](./README.md)
- 📋 **Repository Structure:** [`REPOSITORY_STRUCTURE.md`](./REPOSITORY_STRUCTURE.md)
- 📝 **Migration Guide:** [`MIGRATION_NOTES.md`](./MIGRATION_NOTES.md)
- 🤝 **Contributing:** [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- ⚖️ **License:** [`LICENSE`](./LICENSE)

---

**Happy coding! 🚀**
