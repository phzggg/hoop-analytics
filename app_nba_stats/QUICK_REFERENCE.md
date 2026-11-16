# Quick Reference: Common Rayfin Workflows

## Development Workflow

### 1. Start Development Server
```bash
npm run dev
```
- Starts Vite dev server (http://localhost:5173)
- Hot-reload enabled
- Rayfin authentication available in dev

### 2. Create a Data Entity

Create a new file: `rayfin/data/YourEntity.ts`

```typescript
import { @entity, @authenticated } from "@microsoft/rayfin-core";

@entity
@authenticated
class YourEntity {
  id: string;
  name: string;
  createdAt: Date;
}
```

**IMPORTANT**: Every entity needs an explicit permission decorator:
- `@authenticated` - Only signed-in users
- `@role('admin')` - Specific role
- `@anonymous` - Public access (rare)

### 3. Register Entity in Schema

Edit: `rayfin/data/schema.ts`

```typescript
import YourEntity from './YourEntity';

export const schema = [YourEntity];
```

### 4. Query Data from Frontend

```typescript
import { RayfinClient } from "@microsoft/rayfin-client";

const client = new RayfinClient({
  publishableKey: "pk-your-key-here"
});

// Query
const items = await client.YourEntity.findMany({
  select: {
    id: true,
    name: true
  }
});

// Get by ID
const item = await client.YourEntity.findById("123");

// Create
const newItem = await client.YourEntity.create({
  name: "New Item"
});

// Update
const updated = await client.YourEntity.update("123", {
  name: "Updated Name"
});

// Delete
await client.YourEntity.delete("123");
```

## Deployment

### Deploy to Fabric

```bash
# Full deploy (app + schema)
npx rayfin up

# Schema only (advanced)
npx rayfin up db apply

# Preview config without applying
npx rayfin up db apply --gen-config-only

# Force destructive changes
npx rayfin up db apply --force
```

### Login to Fabric

```bash
npx rayfin login
```

Authenticates with your Fabric tenant. Required for `rayfin up`.

## Common Entity Decorators

### Permission Decorators (REQUIRED)

```typescript
// Authenticated users only
@authenticated

// Specific role
@role('admin')

// Public (no auth required)
@anonymous

// Custom claims
@authenticated
class MyEntity {
  @text
  @authorize.where(claims => claims.sub === entity.ownerId)
  secretField: string;
}
```

### Field Decorators

```typescript
import { @entity, @text, @int, @decimal, @date, @email, @uuid, @boolean } from "@microsoft/rayfin-core";

@entity
class Example {
  @uuid
  id: string;

  @text
  name: string;

  @email
  userEmail: string;

  @int
  count: number;

  @decimal(10, 2)
  price: number;

  @date
  createdAt: Date;

  @boolean
  isActive: boolean;
}
```

### Relationship Decorators

```typescript
// One-to-many relationship
@one(() => Author)
author: Author;

// Many-to-one relationship
@many(() => Book)
books: Book[];
```

## Environment Configuration

### Workspace Name
Edit: `rayfin/.env`
```
RAYFIN_WORKSPACE_NAME=hoop_analytics
```

### Redirect URIs
Edit: `rayfin/rayfin.yml`
```yaml
allowedRedirectUris:
  - http://localhost:5173     # Dev
  - https://your-app.fabric.com # Prod
```

## File Locations Quick Reference

| What | Where |
|------|-------|
| App config | `rayfin/rayfin.yml` |
| Environment vars | `rayfin/.env` |
| Data entities | `rayfin/data/` |
| Entity schema | `rayfin/data/schema.ts` |
| Rayfin docs | `node_modules/@microsoft/rayfin-*/assets/docs/` |
| Agent skills | `.agents/skills/` |

## CLI Commands

```bash
# List available Rayfin CLI commands
npx @microsoft/rayfin-cli --help

# Search documentation
npx @microsoft/rayfin-cli docs search "decorators"

# View specific doc
npx @microsoft/rayfin-cli docs get "permissions"

# Discover packages for a topic
npx @microsoft/rayfin-cli docs discover "authentication"

# Login
npx @microsoft/rayfin-cli login

# Logout
npx @microsoft/rayfin-cli logout

# Deploy app
npx @microsoft/rayfin-cli up

# Apply schema changes only
npx @microsoft/rayfin-cli up db apply

# Generate config without applying
npx @microsoft/rayfin-cli up db apply --gen-config-only
```

## Development Best Practices

### 1. Permission Decorators First
Always add permission decorators before field decorators:
```typescript
❌ WRONG
@entity
class MyEntity {
  @text
  @authenticated  // Wrong position!
  name: string;
}

✅ CORRECT
@entity
@authenticated   // Permission first!
class MyEntity {
  @text
  name: string;
}
```

### 2. Entity Naming
- Avoid reserved GraphQL names
- Use descriptive names
- PascalCase for entity classes

```typescript
❌ DON'T USE
@entity  // Reserved!
class Query { }

❌ DON'T USE
@entity
class __Internal { }  // Starts with __

✅ USE
@entity
class Player { }

✅ USE
@entity
class GameStatistics { }
```

### 3. Read Versioned Docs
The installed packages contain documentation that matches your versions:

```bash
# Read decorators for YOUR installed version
cat node_modules/@microsoft/rayfin-core/assets/docs/decorators.md

# Read GraphQL API docs
cat node_modules/@microsoft/rayfin-data/assets/docs/index.md
```

### 4. Type Safety
Always use proper TypeScript types:
```typescript
import { @entity, @int, @date } from "@microsoft/rayfin-core";

@entity
@authenticated
class Player {
  id: string;
  name: string;
  jerseyNumber: number;  // Better than `any`
  birthDate: Date;
  isActive: boolean;
}
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5173   # Windows
```

### TypeScript Errors
- Check `rayfin/tsconfig.json` - no `experimentalDecorators`
- Use native TC39 Stage 3 decorators
- Ensure `"module": "nodenext"` is set

### Entity Not Found in GraphQL
- Check entity is registered in `rayfin/data/schema.ts`
- Verify file is in `rayfin/data/` directory
- Check class has `@entity` decorator
- Restart dev server after adding new entities

### Permission Denied Errors
- Every entity needs an explicit permission decorator
- Check decorator syntax matches docs
- Verify user/claims match your `@authorize` rules

### Deployment Fails
- Run `npx rayfin login` first
- Check workspace name in `rayfin/.env`
- Review permissions in `rayfin/rayfin.yml`
- Try `rayfin up db apply --gen-config-only` to inspect config

## Resource Links

- **Rayfin Docs**: `node_modules/@microsoft/rayfin-guide/assets/docs/`
- **Microsoft Fabric**: https://learn.microsoft.com/en-us/fabric/
- **GitHub Issues**: Check framework repos for known issues
