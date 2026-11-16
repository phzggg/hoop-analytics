# HoopMetrics Repository Structure

This document describes the organization and purpose of each directory in the HoopMetrics repository.

## Overview

The repository follows a **medallion architecture pattern** for data engineering, with clear separation between application code, data pipelines, analytics models, and documentation.

## Directory Structure

```
hoop-analytics/
├── app_nba_stats/              # Fabric App application
│   ├── src/                    # React/TypeScript source code
│   ├── public/                 # Static public assets
│   ├── scripts/                # Build and deployment scripts
│   ├── rayfin/                 # Fabric App connectors and schema
│   ├── local-data/             # Local snapshot data for development
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.ts          # Vite build configuration
│   └── tsconfig.json           # TypeScript configuration
│
├── notebooks/                  # Fabric notebooks organized by medallion layer
│   ├── bronze/                 # Raw data ingestion and collection
│   │   ├── 01_Ingestion_Setup_Bronze.py
│   │   ├── 11_ESPN_Bronze.py
│   │   └── 14_ESPN_Players_Bronze.py
│   ├── silver/                 # Data transformation and validation
│   │   ├── 02_Transformation_Silver_Layer.py
│   │   ├── 12_ESPN_Silver.py
│   │   └── 15_ESPN_Players_Silver.py
│   ├── gold/                   # Dimensional modeling and analytics-ready data
│   │   ├── 03_Dimensional_Model_Gold_Layer.py
│   │   ├── 13_ESPN_Gold.py
│   │   └── 16_ESPN_Players_Gold.py
│   └── utilities/              # Helper notebooks and utilities
│       ├── 17_ESPN_Automatic_Collection.py
│       └── Utilities_init_session.py
│
├── fabric/                     # Microsoft Fabric artifacts
│   ├── pipeline/               # Data factory pipelines
│   │   └── ESPN_Process_Batches.json
│   └── semantic-model/         # Power BI semantic model
│       └── definition/
│           ├── database.tmdl
│           ├── model.tmdl
│           ├── expressions.tmdl
│           ├── relationships.tmdl
│           └── tables/
│
├── config/                     # Configuration templates
│   └── [Configuration files and templates]
│
├── data/                       # Sample and reference data
│   └── sample/                 # Sample datasets for testing and development
│
├── docs/                       # Comprehensive documentation
│   ├── architecture.md         # System architecture and data flow
│   ├── data-engineering.md     # Data pipeline details and medallion architecture
│   ├── fabric-app.md           # Fabric App features and structure
│   ├── semantic-model.md       # Power BI model design
│   ├── ux-ui-decisions.md      # UI/UX rationale and patterns
│   ├── implementation-guide.md # Step-by-step setup and deployment
│   ├── lessons-learned.md      # Insights from development
│   └── security-and-rights.md  # Security, privacy, and licensing
│
├── src/                        # Backend and shared source code
│   └── [Backend implementation]
│
├── tests/                      # Test suites
│   └── [Test files]
│
├── nba-fabric-app/             # Additional app-related artifacts
│   └── [App artifacts]
│
├── .github/                    # GitHub workflows and templates
│   ├── workflows/              # CI/CD workflows
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── PULL_REQUEST_TEMPLATE/  # PR templates
│
├── .gitignore                  # Git ignore rules
├── .vscode/                    # VS Code workspace settings
├── .env.example                # Environment variables template
├── .env.local                  # Local environment (not committed)
├── .env.production             # Production environment
├── .mcp.json                   # MCP configuration
│
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
├── README.md                   # Main project README
├── REPOSITORY_STRUCTURE.md     # This file
└── [Other configuration files]
```

## Key Directory Details

### `/app_nba_stats` - Fabric App
The complete Fabric App application built with React, TypeScript, and Rayfin.

- **src/** - React components, pages, and business logic
- **public/** - Static assets and app resources
- **scripts/** - Utility scripts for building and publishing
- **rayfin/** - Fabric connector configuration and schema definitions
- **local-data/** - Local snapshot files for development without cloud dependency

**Key Files:**
- `package.json` - Node.js 24+ dependencies and scripts
- `vite.config.ts` - Build configuration
- `tsconfig.json` - TypeScript settings

### `/notebooks` - Data Pipelines
Organized following the **Medallion Architecture** pattern:

#### Bronze Layer (`/bronze`)
Raw data ingestion and collection from external sources (ESPN).
- Minimal transformation
- Maintains source schema
- Incremental collection and storage

#### Silver Layer (`/silver`)
Data transformation and validation.
- Schema standardization
- Quality checks and validation
- Incremental updates to Delta Lake tables
- Deduplication and cleansing

#### Gold Layer (`/gold`)
Dimensional modeling and analytics-ready data.
- Conformed dimensions and facts
- Optimized for Power BI queries
- Aggregations and business metrics
- Direct Lake connectivity to semantic model

#### Utilities (`/utilities`)
Helper notebooks and session initialization.
- Session setup and configuration
- Automatic collection schedules
- Common functions and utilities

### `/fabric` - Fabric Artifacts
Microsoft Fabric asset definitions and configurations.

- **pipeline/** - Data factory pipeline JSON definitions with parameterized environment references
- **semantic-model/** - Power BI semantic model in TMDL (Tabular Model Definition Language) format with environment placeholders

**Important:** These files contain environment placeholders that must be manually configured during deployment.

### `/docs` - Documentation
Comprehensive guides covering all aspects of the solution:

| Document | Purpose |
|----------|---------|
| architecture.md | High-level system design and data flow |
| data-engineering.md | Medallion architecture details and ETL/ELT flow |
| fabric-app.md | App features, components, and data access patterns |
| semantic-model.md | Semantic model tables, relationships, and measures |
| ux-ui-decisions.md | UI/UX patterns and design rationale |
| implementation-guide.md | Prerequisites and step-by-step configuration |
| lessons-learned.md | Development insights and best practices |
| security-and-rights.md | Security, privacy, licensing, and third-party rights |

### `/config` - Configuration
Environment-specific configuration templates and settings.

### `/data` - Sample Data
Reference and sample datasets for testing and development.

### `/tests` - Testing
Test suites and test data for validation.

### `/.github` - GitHub Workflows
GitHub Actions workflows for CI/CD, issue templates, and PR templates.

## Development Workflow

### 1. Data Pipeline Development
Make changes to notebooks in `/notebooks/{bronze|silver|gold}/` following the medallion pattern.

### 2. Fabric Artifact Updates
Update pipeline definitions in `/fabric/pipeline/` and semantic model in `/fabric/semantic-model/` with **environment identifiers** as placeholders.

### 3. App Development
Develop React components and logic in `/app_nba_stats/src/`.

### 4. Testing
Run tests with `npm test` from `/app_nba_stats/`.

### 5. Documentation
Update relevant documentation in `/docs/` to reflect changes.

## Configuration Management

- `.env.example` - Template for environment variables (committed)
- `.env.local` - Local development environment (not committed)
- `.env.production` - Production environment settings

Environment identifiers in pipeline and model definitions are replaced during deployment.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines and best practices.

## Related Documents

- [Architecture Overview](./docs/architecture.md)
- [Data Engineering Guide](./docs/data-engineering.md)
- [Implementation Guide](./docs/implementation-guide.md)
- [Contributing Guidelines](./CONTRIBUTING.md)
