# Deployment Checklist & Next Steps

## ✅ Setup Verification

- [x] Rayfin project scaffolded (`app_nba_stats`)
- [x] Dependencies installed (381 packages)
- [x] Workspace configured (`hoop_analytics`)
- [x] Authentication enabled (Fabric SSO)
- [x] Database configured (MSSQL)
- [x] Static hosting configured (Vite)
- [x] TypeScript configured (native decorators)
- [x] Documentation created (4 guides)

## 📋 Before First `npm run dev`

### Files to Create/Modify

- [ ] **Frontend Build Scripts** - Add to `package.json`
  ```json
  "scripts": {
    "dev": "rayfin dev",
    "build": "rayfin build",
    "preview": "rayfin preview"
  }
  ```

- [ ] **Data Schema** - Create `rayfin/data/schema.ts`
  ```typescript
  // Register all entities here
  export const schema = [];
  ```

- [ ] **Sample Entity** - Create first entity in `rayfin/data/`
  - Example: `Player.ts`
  - Use decorators from `@microsoft/rayfin-core`
  - Include permission decorator

### Environment Setup

- [ ] Verify `rayfin/.env`:
  ```
  RAYFIN_WORKSPACE_NAME=hoop_analytics
  ```

- [ ] Verify `rayfin/rayfin.yml`:
  - Auth service enabled ✅
  - Data service enabled ✅
  - Static hosting enabled ✅
  - Workspace ID correct ✅

## 🚀 Development Workflow

### Step 1: Start Dev Server
```bash
cd "<USER_HOME>\Documents\YOUR_WORKSPACE\app_nba_stats"
npm run dev
```
- Expect: Server running on http://localhost:5173
- Rayfin authentication will prompt for login

### Step 2: Develop Locally
- Modify `rayfin/data/` entities
- Build UI components
- Test with Rayfin client
- Hot-reload enabled

### Step 3: Prepare for Deployment
- Review all permission decorators
- Test all GraphQL queries
- Verify row-level security policies
- Run `npm run build`

### Step 4: Deploy to Fabric
```bash
npx rayfin login
npx rayfin up
```

## 📦 Data Model Checklist

Before committing entities to production:

### Entity Creation
- [ ] Entity file created in `rayfin/data/`
- [ ] Entity registered in `rayfin/data/schema.ts`
- [ ] `@entity` decorator applied
- [ ] **Permission decorator applied** (`@authenticated`, `@role`, or `@anonymous`)
- [ ] All fields have type decorators (`@text`, `@int`, `@date`, etc.)

### Security
- [ ] No exposed secrets in entity definition
- [ ] All public endpoints have proper authorization
- [ ] Row-level security policies defined for sensitive data
- [ ] Claims-based access control configured where needed

### Testing
- [ ] GraphQL schema validates
- [ ] Queries execute without errors
- [ ] Mutations work correctly
- [ ] Pagination works for large datasets
- [ ] Authorization works as expected

### Documentation
- [ ] Entity purpose documented
- [ ] Field descriptions added
- [ ] Permission model documented
- [ ] Breaking changes documented

## 🔐 Security Checklist

Before deploying to production:

### Authentication & Authorization
- [ ] Fabric SSO enabled (not email/password)
- [ ] All entities have permission decorators
- [ ] Row-level security implemented
- [ ] Role-based access working
- [ ] Claims-based access working

### Data Protection
- [ ] No hardcoded secrets in code
- [ ] Connection strings secured
- [ ] API keys stored securely
- [ ] Sensitive fields protected
- [ ] Data encryption in transit

### API Security
- [ ] Publishable keys (`pk-*`) used client-side
- [ ] Service secrets not exposed
- [ ] API rate limiting configured
- [ ] CORS properly configured
- [ ] Input validation implemented

### Deployment
- [ ] `allowedRedirectUris` matches production domain
- [ ] Static assets served securely
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Regular security audits planned

## 📝 Code Quality Checklist

- [ ] No `experimentalDecorators` in `tsconfig.json`
- [ ] No reserved GraphQL names used
- [ ] TypeScript strict mode enabled
- [ ] No `any` types without justification
- [ ] No `console.log` in production code
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Tests written for critical paths

## 🧪 Testing Checklist

- [ ] Unit tests for entities
- [ ] Integration tests for GraphQL queries
- [ ] Authentication flow tested
- [ ] Authorization rules tested
- [ ] Error scenarios tested
- [ ] Performance tested under load
- [ ] Accessibility tested
- [ ] Cross-browser tested

## 📊 Deployment Checklist

### Pre-Deployment
- [ ] All tasks complete and tested
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Backup created
- [ ] Rollback plan documented

### Deployment
- [ ] Run: `npx rayfin login`
- [ ] Verify login successful
- [ ] Run: `npx rayfin up`
- [ ] Monitor deployment progress
- [ ] Verify app loads correctly
- [ ] Test core functionality

### Post-Deployment
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify user access working
- [ ] Test user-facing features
- [ ] Document any issues
- [ ] Plan for next iteration

## 🎯 Key Commands Reference

### Development
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview build locally
npm run preview

# Generate config without deploying
npx rayfin up db apply --gen-config-only
```

### Authentication
```bash
# Login to Fabric
npx rayfin login

# Check login status
npx rayfin status

# Logout
npx rayfin logout
```

### Deployment
```bash
# Full deployment (app + schema)
npx rayfin up

# Schema migration only
npx rayfin up db apply

# Force destructive changes
npx rayfin up db apply --force

# Dry run config
npx rayfin up --dry-run
```

### Documentation
```bash
# Search documentation
npx @microsoft/rayfin-cli docs search "decorators"

# View specific doc
npx @microsoft/rayfin-cli docs get "permissions"

# Discover packages for topic
npx @microsoft/rayfin-cli docs discover "authentication"
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `PROJECT_SETUP.md` | Detailed framework guide |
| `QUICK_REFERENCE.md` | Common workflows |
| `SETUP_SUMMARY.md` | Setup completion report |
| `DEPLOYMENT_CHECKLIST.md` | This file |

## 🆘 Troubleshooting

### "npm run dev not found"
- Ensure `package.json` has "dev" script
- Or use: `npx rayfin dev`

### "Entity not found in GraphQL"
- Check entity is in `rayfin/data/schema.ts`
- Verify file in `rayfin/data/` directory
- Ensure `@entity` decorator applied
- Restart dev server

### "Permission Denied"
- Check entity has permission decorator
- Verify user claims match `@authorize` rules
- Check scopes in `rayfin.yml`

### "TypeScript Errors"
- No `experimentalDecorators` in tsconfig
- Use native TC39 decorators
- `"module": "nodenext"` must be set

### "Deploy Fails"
- Run `npx rayfin login` first
- Check workspace name in `.env`
- Verify permissions in `rayfin.yml`
- Try `--gen-config-only` to inspect

## 📞 Support Resources

1. **Rayfin Docs**: `node_modules/@microsoft/rayfin-guide/assets/docs/`
2. **Microsoft Fabric**: https://learn.microsoft.com/en-us/fabric/
3. **API Reference**: Read from installed packages
4. **CLI Help**: `npx @microsoft/rayfin-cli --help`

## ✨ You're Ready!

Your Rayfin app is fully scaffolded and configured. Follow this checklist as you develop and deploy to ensure quality and security.

**Start development**: `npm run dev`  
**Deploy to Fabric**: `npx rayfin up`  
**Need help**: Review documentation files or `QUICK_REFERENCE.md`

---

Good luck with your NBA Stats app! 🏀
