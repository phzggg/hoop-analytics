# Repository Reorganization - Migration Notes

## Overview
On November 16, 2026, the repository structure was reorganized to improve navigation and clarity following a medallion architecture pattern.

**Commit:** `29a9d0d` - "refactor: remove redundant README and reorganize repository structure for better navigation"

## Breaking Changes

### Directory Renames and Moves
If you have any scripts, CI/CD pipelines, or tools that reference the old paths, they need to be updated:

| Old Path | New Path | Notes |
|----------|----------|-------|
| `fabric-artifacts/` | `fabric/` | Top-level rename for clarity |
| `semantic-model/` | `fabric/semantic-model/` | Moved under `fabric/` for grouping |
| `notebooks/` (flat) | `notebooks/{bronze,silver,gold,utilities}/` | Organized by pipeline stage |

### Deleted Files
- `app_nba_stats/README.md` - Redundant content moved to main README.md

### New Files
- `REPOSITORY_STRUCTURE.md` - Comprehensive documentation of repository layout
- `.github/` directory structure (empty, ready for workflows)

## Updating Your Workflows

### Python Path References
If Fabric notebooks or Python scripts reference paths like:
```python
# OLD
path = "semantic-model/definition/tables/..."

# NEW
path = "fabric/semantic-model/definition/tables/..."
```

Update all file references to use the new paths.

### Fabric Artifact References
If you're syncing files between git and Fabric workspace:

**Old sync command example:**
```bash
# Copy pipeline definitions
cp -r fabric-artifacts/pipeline/* $FABRIC_PIPELINE_PATH/
cp -r semantic-model/* $FABRIC_MODEL_PATH/
```

**New sync command example:**
```bash
# Copy pipeline definitions
cp -r fabric/pipeline/* $FABRIC_PIPELINE_PATH/
cp -r fabric/semantic-model/* $FABRIC_MODEL_PATH/
```

### CI/CD Pipeline Updates

#### If using GitHub Actions
Update any workflow files that reference old paths:

```yaml
# In .github/workflows/*.yml files:

# OLD
- path: semantic-model/**
  ...
- path: fabric-artifacts/**
  ...

# NEW
- path: fabric/semantic-model/**
  ...
- path: fabric/pipeline/**
  ...
```

#### If using Azure DevOps
Update pipeline YAML that checks out or deploys:

```yaml
# OLD
- checkout: self
  path: $(Build.SourcesDirectory)/semantic-model

# NEW
- checkout: self
  path: $(Build.SourcesDirectory)/fabric/semantic-model
```

### Notebook Import Updates

If you have notebooks importing from each other or accessing shared utilities:

**Old imports:**
```python
# From notebooks/utilities or notebooks/ root
exec(open("../Utilities_init_session.py").read())
```

**New imports:**
```python
# From organized subdirectories
exec(open("../utilities/Utilities_init_session.py").read())
```

## Notebooks Organization

The `/notebooks` directory is now organized following the medallion architecture:

### `/notebooks/bronze` - Raw Data Ingestion
- **Purpose:** Collect and store raw data from external sources (ESPN)
- **Notebooks:**
  - `01_Ingestion_Setup_Bronze.py` - Initialize bronze layer
  - `11_ESPN_Bronze.py` - ESPN data collection
  - `14_ESPN_Players_Bronze.py` - ESPN player data collection

### `/notebooks/silver` - Data Transformation
- **Purpose:** Clean, validate, and transform bronze data
- **Notebooks:**
  - `02_Transformation_Silver_Layer.py` - Silver layer setup
  - `12_ESPN_Silver.py` - ESPN data transformation
  - `15_ESPN_Players_Silver.py` - ESPN player data transformation

### `/notebooks/gold` - Dimensional Modeling
- **Purpose:** Create conformed dimensions and facts for analytics
- **Notebooks:**
  - `03_Dimensional_Model_Gold_Layer.py` - Gold layer setup
  - `13_ESPN_Gold.py` - ESPN dimensional model
  - `16_ESPN_Players_Gold.py` - ESPN player dimensional model

### `/notebooks/utilities` - Helper Functions
- **Purpose:** Session initialization and utility functions
- **Notebooks:**
  - `17_ESPN_Automatic_Collection.py` - Automated collection
  - `Utilities_init_session.py` - Session initialization

## Fabric Workspace Considerations

### Pipeline Definitions
The pipeline definition file moved from `fabric-artifacts/pipeline/` to `fabric/pipeline/`.

If you're managing Fabric pipelines through Git integration:
1. Update your Git sync settings to point to the new location
2. Re-sync the pipeline definition to ensure it's referencing the correct notebook paths
3. Test a manual pipeline run before relying on scheduled execution

### Semantic Model
The semantic model TMDL files moved from `semantic-model/` to `fabric/semantic-model/`.

If using TMDL deployment:
1. Update deployment scripts to reference the new path
2. Ensure all environment identifiers are properly replaced before deployment
3. Verify the semantic model refresh completes successfully after updating references

## Documentation

### New Files
- `REPOSITORY_STRUCTURE.md` - Detailed explanation of directory organization
- `.github/workflows/` - Ready for GitHub Actions workflows
- `.github/ISSUE_TEMPLATE/` - Ready for issue templates
- `.github/PULL_REQUEST_TEMPLATE/` - Ready for PR templates

### Updated Files
- `README.md` - Updated directory references to reflect new structure

## Testing Checklist

After updating your environment, verify:

- [ ] All Python imports and file references work correctly
- [ ] CI/CD pipelines execute without path-related errors
- [ ] Fabric pipeline runs successfully with updated notebook references
- [ ] Semantic model deployment completes without issues
- [ ] Git sync (if enabled) correctly identifies files in new locations
- [ ] Documentation links and cross-references are correct
- [ ] Team members have updated their local environments

## Rollback (if needed)

If you need to revert to the previous structure:

```bash
git checkout 753c301  # Previous commit before reorganization
```

However, we recommend moving forward with the new structure as it's more scalable and maintainable.

## Questions or Issues

Refer to:
- `REPOSITORY_STRUCTURE.md` - For detailed structure explanation
- `README.md` - For quick reference
- `docs/` - For architectural and implementation details

---

**Last Updated:** 2026-11-16  
**Reorganized by:** Repository Reorganization Task  
**Status:** Complete and deployed to `origin/main`
