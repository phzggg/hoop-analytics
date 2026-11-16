# NBA Stats Rayfin App - Project Setup Guide

## Overview

This is a **Microsoft Fabric App** built with **Rayfin**, a full-stack framework for building data-driven applications on Microsoft Fabric. The project is called `app_nba_stats` and is configured to work with the "hoop_analytics" workspace.

## Project Structure

```
app_nba_stats/
├── .agents/                          # Agent skills for Copilot integration
│   ├── skills/
│   │   ├── rayfin/                  # Rayfin core skill documentation
│   │   ├── rayfin-connectors/       # Rayfin connectors skill
│   │   └── rayfin-functions/        # Rayfin functions skill
│
├── rayfin/                           # Rayfin app configuration and data models
│   ├── rayfin.yml                   # Main app configuration
│   ├── .env                         # Environment configuration (workspace name)
│   ├── tsconfig.json                # TypeScript configuration
│   ├── .project.json                # Project metadata for telemetry
│   ├── data/                        # Data models directory (entities will go here)
│   └── .lockfile.json               # Dependency lock file
│
├── node_modules/                     # Dependencies installed via npm
├── .mcp.json                        # Model Context Protocol configuration
├── .gitignore                       # Git ignore rules
├── package.json                     # Root package configuration
├── package-lock.json                # Lock file for npm dependencies
└── AGENTS.md                        # Agent context information

```

## Rayfin Framework Components

### rayfin.yml Configuration

The main configuration file defines:

- **ID & Name**: `app-nba-stats` (ID) and `app_nba_stats` (name)
- **Version**: 1.0.11
- **Services Enabled**:
  - **Auth**: User authentication with Fabric SSO (Entra ID), scopes for read/write data
  - **Data**: MSSQL database dialect for data models
  - **Static Hosting**: Serves built frontend from `dist` folder

### Key Settings

```yaml
services:
  auth:
    enabled: true
    customClaims:
      app_version: 1.0.0
    scopes:
      - read:data
      - write:data
    fabric:
      enabled: true                    # Fabric SSO enabled
    allowedRedirectUris:
      - http://localhost:5173         # Dev environment
  
  data:
    enabled: true
    dialect: mssql                     # SQL Server dialect
  
  staticHosting:
    enabled: true
    folder: dist
    buildCommand: npm run build
    indexDocument: index.html
```

## Installed Dependencies

### Production Dependencies (in package.json)

- `@microsoft/rayfin-core`: Core entity decorators and data models
- `@microsoft/rayfin-data`: GraphQL queries and data operations
- `@microsoft/rayfin-client`: Frontend client library

### Dev Dependencies

- `@microsoft/rayfin-cli`: Command-line interface for development and deployment

## Environment Configuration

The `.env` file in the `rayfin/` directory contains:

```
RAYFIN_WORKSPACE_NAME=hoop_analytics
```

This connects the app to the "YOUR_WORKSPACE" Fabric workspace.

## Important Rayfin Concepts

### Data Models (Entities)

- **Location**: `rayfin/data/` directory
- **Registration**: Every entity must be registered in `rayfin/data/schema.ts`
- **Decorators**: Built on TC39 Stage 3 decorators (no `experimentalDecorators` flag!)
- **Permissions**: Every entity MUST have an explicit permission decorator for security

### Authentication

- **Development**: Local email/password auth via `rayfin login`
- **Production**: Fabric SSO (Entra ID) exclusively
- **Publishable Keys**: Prefixed with `pk-*`, safe for client-side code
- **Service Secrets**: Never expose in client-side code

### Deployment

- **Primary Command**: `rayfin up` - Deploys app AND applies schema migrations
- **Schema-Only**: `rayfin up db apply` - Applies migrations without static deploy
- **Force Flag**: `--force` allows destructive changes (drop table/column)

### Important Constraints

- **Reserved Entity Names**: Cannot use GraphQL built-in scalars or names starting with `__`
- **Decorator Surface**: Read documentation from `node_modules` - it matches the installed version
- **No experimentalDecorators**: The framework requires native TC39 decorators

## Documentation Access

All Rayfin documentation is versioned and installed in `node_modules`:

| Topic | Location |
|-------|----------|
| Decorators & Field Options | `node_modules/@microsoft/rayfin-core/assets/docs/` |
| Client Queries & Mutations | `node_modules/@microsoft/rayfin-data/assets/docs/` |
| Guides & Best Practices | `node_modules/@microsoft/rayfin-guide/assets/docs/` |
| Client Configuration | `node_modules/@microsoft/rayfin-client/assets/docs/` |
| Local Development | `node_modules/@microsoft/rayfin-local-dev/assets/docs/` |
| Server Functions (UDFs) | `node_modules/@microsoft/rayfin-guide/assets/docs/functions/` |
| App State Deep Linking | `node_modules/@microsoft/rayfin-app-state-fabric/assets/docs/` |

**Always read the package docs first** - they describe the exact versions installed in this project.

## Next Steps

1. **Start Development Server**: `npm run dev`
   - Starts Vite dev server (typically on http://localhost:5173)
   - Hot-reload enabled for iterative development

2. **Create Data Models**:
   - Add entities to `rayfin/data/` directory
   - Use decorators from `@microsoft/rayfin-core`
   - Register in `rayfin/data/schema.ts`
   - Include permission decorators for security

3. **Build Frontend**:
   - Create UI components using your preferred framework
   - Use `@microsoft/rayfin-client` for data access
   - Use `@microsoft/rayfin-data` for GraphQL queries

4. **Deploy to Fabric**:
   - Run: `npx rayfin up`
   - This deploys the app and applies all schema migrations
   - Requires `rayfin login` and Fabric workspace access

## Security Best Practices

✅ **DO**:
- Add explicit permission decorators to every entity
- Keep `allowedRedirectUris` tightly scoped
- Use publishable keys (`pk-*`) for client-side code only
- Use Fabric SSO for production deployments
- Read permission documentation before writing entities

❌ **DON'T**:
- Expose service secrets or connection strings in client code
- Omit permission decorators (silently grants full CRUD)
- Use email/password auth in production (use Fabric SSO)
- Enable `experimentalDecorators` in tsconfig
- Use reserved GraphQL type names for entities

## TypeScript Configuration

The project uses **modern TypeScript with native decorators**:

```json
{
  "compilerOptions": {
    "outDir": ".temp/compiled",
    "rootDir": ".",
    "declaration": true,
    "composite": true,
    "noEmit": false,
    "module": "nodenext",
    "moduleResolution": "nodenext"
  },
  "include": ["**/*"],
  "exclude": [".temp/**/*"]
}
```

Key points:
- No `experimentalDecorators` flag
- Uses native TC39 Stage 3 decorators
- Composite project setup for monorepo support
- Outputs declarations for library usage

## Agent Skills for IDE Integration

The project includes Copilot agent skills:

- **skill:rayfin** - Main Rayfin framework support
- **skill:rayfin-functions** - Server-side functions (UDFs)
- **skill:rayfin-connectors** - Data connectors
- **mcp:rayfin** - Model Context Protocol server for enhanced IDE support

Load these skills in your IDE for better Rayfin code assistance and documentation access.

## Ready to Build!

Your Rayfin app is now scaffolded and ready for development. The framework handles:

- ✅ TypeScript compilation
- ✅ Entity schema management
- ✅ GraphQL API generation
- ✅ Authentication & authorization
- ✅ Static hosting
- ✅ Fabric workspace integration

Next: Define your data models, build your UI, and deploy with `rayfin up`!
