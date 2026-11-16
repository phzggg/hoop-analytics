# Getting Started with app_nba_stats

Welcome to your Rayfin-powered NBA Statistics app! This guide will get you up and running in just a few steps.

## 📖 Read These First (In Order)

1. **This file** (5 min) - You are here! Overview and quick start
2. **QUICK_REFERENCE.md** (10 min) - Common tasks and workflows
3. **PROJECT_SETUP.md** (15 min) - Deep dive into the framework
4. **DEPLOYMENT_CHECKLIST.md** - Before going to production

## 🎯 Your First 15 Minutes

### Minute 1-2: Understand the Framework
Rayfin is a full-stack framework for building apps on Microsoft Fabric:

- **Backend**: Entity-based data models (TypeScript decorators)
- **Frontend**: React/Vue/Svelte with GraphQL client
- **Database**: MSSQL in your Fabric workspace
- **Auth**: Fabric SSO (Entra ID)
- **Hosting**: Fabric static hosting

### Minute 3-5: Explore Your Project
```bash
cd "<USER_HOME>\Documents\YOUR_WORKSPACE\app_nba_stats"
ls                          # See project structure
cat rayfin/rayfin.yml       # App configuration
cat rayfin/.env             # Workspace setting
```

### Minute 6-10: Read Configuration
Files you should understand:

- **rayfin/rayfin.yml** - Main app config (services, auth, hosting)
- **rayfin/.env** - Workspace name
- **package.json** - NPM dependencies
- **rayfin/tsconfig.json** - TypeScript settings

### Minute 11-15: Check Dependencies
```bash
npm list --depth=0
# Should show:
# - @microsoft/rayfin-core
# - @microsoft/rayfin-data
# - @microsoft/rayfin-client
# - @microsoft/rayfin-cli
```

## 🚀 Ready to Code? Do This

### Option A: Create Your First Entity (5 minutes)

**Step 1**: Create `rayfin/data/Player.ts`
```typescript
import { @entity, @text, @int, @authenticated } from "@microsoft/rayfin-core";

@entity
@authenticated
class Player {
  id: string;
  
  @text
  name: string;
  
  @text
  team: string;
  
  @int
  number: number;
}

export default Player;
```

**Step 2**: Register in `rayfin/data/schema.ts`
```typescript
import Player from './Player';

export const schema = [Player];
```

**Step 3**: Restart dev server (if running)

### Option B: Read Docs (10 minutes)

Before writing code, understand:
1. Permission decorators (REQUIRED)
2. Field decorators
3. Entity relationships
4. GraphQL queries

**Read**: `node_modules/@microsoft/rayfin-core/assets/docs/decorators.md`

### Option C: Just Start the Server

```bash
# Option 1: Using Rayfin dev
npx rayfin dev

# Option 2: Using npm (if dev script exists)
npm run dev

# Expected: Server at http://localhost:5173
```

## 📚 Knowing What to Do?

### I want to...

- **Create data models** → Read `QUICK_REFERENCE.md` "Create a Data Entity"
- **Build the UI** → Check `PROJECT_SETUP.md` "Frontend" section
- **Query data** → See `QUICK_REFERENCE.md` "Query Data from Frontend"
- **Add permissions** → Review `PROJECT_SETUP.md` "Permission Decorators"
- **Deploy to Fabric** → Follow `DEPLOYMENT_CHECKLIST.md`
- **Understand the framework** → Deep dive into `PROJECT_SETUP.md`

## 🔑 Five Most Important Things

1. **Every Entity Needs Permission Decorator**
   ```typescript
   @entity
   @authenticated  // ← REQUIRED! (or @role, @anonymous)
   class MyEntity { }
   ```

2. **Register Entities in schema.ts**
   ```typescript
   export const schema = [Player, Game, Team];
   ```

3. **Use Native Decorators (No experimentalDecorators)**
   - ✅ Correct: TC39 Stage 3 decorators
   - ❌ Wrong: `experimentalDecorators: true`

4. **Read Docs from node_modules**
   ```
   node_modules/@microsoft/rayfin-core/assets/docs/
   node_modules/@microsoft/rayfin-data/assets/docs/
   node_modules/@microsoft/rayfin-guide/assets/docs/
   ```

5. **Deploy with `rayfin up`**
   ```bash
   npx rayfin up  # App + schema migrations
   ```

## 🎨 Project Layout

```
app_nba_stats/
├── rayfin/
│   ├── rayfin.yml           # App config
│   ├── .env                 # Workspace
│   ├── data/
│   │   ├── Player.ts        # You'll create these
│   │   ├── Game.ts
│   │   ├── Team.ts
│   │   └── schema.ts        # Register them here
│   └── tsconfig.json
├── src/                     # Frontend (create as needed)
│   ├── components/
│   ├── pages/
│   └── App.tsx
└── dist/                    # Built output (created by build)
```

## 💡 Common Tasks

### Start Coding
```bash
cd "<USER_HOME>\Documents\YOUR_WORKSPACE\app_nba_stats"
npx rayfin dev
```

### Create an Entity
1. New file: `rayfin/data/EntityName.ts`
2. Add decorators from `@microsoft/rayfin-core`
3. Add to `rayfin/data/schema.ts`

### Query from Frontend
```typescript
const client = new RayfinClient({ publishableKey: "pk-..." });
const players = await client.Player.findMany();
```

### Deploy
```bash
npx rayfin login
npx rayfin up
```

## 🛡️ Security Essentials

| Do | Don't |
|----|----|
| ✅ Add permission decorators | ❌ Omit permission decorators |
| ✅ Use Fabric SSO | ❌ Use email/password in prod |
| ✅ Read versioned docs | ❌ Trust old docs online |
| ✅ Secure secrets | ❌ Commit secrets to code |

## 🆘 Quick Help

**"Where do I put entities?"**  
→ `rayfin/data/` directory, one per file

**"How do I query data?"**  
→ Use `@microsoft/rayfin-client` from frontend

**"What's a permission decorator?"**  
→ `@authenticated`, `@role`, or `@anonymous` on every entity

**"How do I deploy?"**  
→ `npx rayfin login` then `npx rayfin up`

**"Where are the docs?"**  
→ `node_modules/@microsoft/rayfin-*/assets/docs/`

## 📋 Your Checklist

- [ ] Read this file ✓
- [ ] Read QUICK_REFERENCE.md
- [ ] Review PROJECT_SETUP.md
- [ ] Check rayfin/rayfin.yml
- [ ] Verify npm dependencies
- [ ] Create first entity (optional)
- [ ] Start dev server
- [ ] Build your app!

## 🎯 What's Next?

**Immediate** (Next 30 minutes):
- [ ] Review QUICK_REFERENCE.md
- [ ] Start dev server
- [ ] Create a sample entity

**Short term** (Next week):
- [ ] Build data models
- [ ] Create frontend
- [ ] Test locally

**Medium term** (Before launch):
- [ ] Add authentication flows
- [ ] Implement permissions
- [ ] Security review
- [ ] Performance testing

**Launch**:
- [ ] Run deployment checklist
- [ ] Deploy with `rayfin up`
- [ ] Monitor production

## 📞 Resources

| Need Help With | Where |
|---|---|
| Decorators | `node_modules/@microsoft/rayfin-core/assets/docs/` |
| GraphQL queries | `node_modules/@microsoft/rayfin-data/assets/docs/` |
| Guides | `node_modules/@microsoft/rayfin-guide/assets/docs/` |
| Client code | `node_modules/@microsoft/rayfin-client/assets/docs/` |
| Troubleshooting | QUICK_REFERENCE.md "Troubleshooting" |

## ✨ You're Ready!

Everything is set up. Time to build! 

**Next step**: Open QUICK_REFERENCE.md or start your dev server.

```bash
npx rayfin dev
```

Happy coding! 🚀

---

**Project**: app_nba_stats  
**Framework**: Rayfin 1.36.2  
**Status**: Ready for development  
**Your workspace**: hoop_analytics
