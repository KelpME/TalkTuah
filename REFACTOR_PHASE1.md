# Phase 1: Low-Risk Structural Cleanup

**Risk Level:** 🟢 LOW  
**Estimated Time:** 30 minutes  
**Can Break:** Documentation links only  
**Prerequisites:** Git branch for backup

---

## Overview

Remove misleading directories and flatten unnecessary nesting without touching any business logic.

### Changes
1. Move `services/vllm/` documentation to `docs/services/`
2. Remove empty test directories
3. Flatten `apps/api/` to `api/`
4. Update all references

---

## Step 1: Create Backup Branch

```bash
cd /home/tmo/Work/TalkTuah

# Create backup
git checkout -b backup-before-refactor
git add -A
git commit -m "Backup before Phase 1: Structural cleanup"

# Return to working branch
git checkout main  # or your current branch
git checkout -b refactor-phase1
```

**Validation:**
```bash
git branch | grep refactor-phase1
# Should show * refactor-phase1
```

---

## Step 2: Move services/vllm to docs/services/

### 2.1 Create new location
```bash
mkdir -p docs/services
```

### 2.2 Move vllm documentation
```bash
mv services/vllm/README.md docs/services/vllm.md
```

### 2.3 Remove empty services directory
```bash
rmdir services/vllm
rmdir services
```

**Validation:**
```bash
# Should exist
test -f docs/services/vllm.md && echo "✓ File moved successfully"

# Should NOT exist
test -d services && echo "✗ services/ still exists" || echo "✓ services/ removed"
```

### 2.4 Update references in documentation

Search for references:
```bash
grep -r "services/vllm" docs/ README.md 2>/dev/null
```

**Files to update manually:**
- Check `README.md` line 91-92 (if it references services)
- Check `docs/README.md` or any index files
- Update any links from `services/vllm/README.md` to `docs/services/vllm.md`

**No automated updates needed if no references found.**

---

## Step 3: Clean Up Empty Test Directories

### 3.1 Verify directories are truly empty
```bash
# Check e2e
find tests/e2e -type f 2>/dev/null | wc -l
# Should output: 0

# Check unit  
find tests/unit -type f 2>/dev/null | wc -l
# Should output: 0
```

### 3.2 Remove if empty
```bash
# Only if previous commands showed 0
rm -rf tests/e2e
rm -rf tests/unit
```

### 3.3 Keep tests/integration (has files)
```bash
# Verify integration has content
ls -la tests/integration/
# Should show files
```

**Validation:**
```bash
ls -la tests/
# Should show: conftest.py, integration/, requirements.txt
# Should NOT show: e2e/, unit/
```

---

## Step 4: Flatten apps/api to api/

**⚠️ CRITICAL:** This affects Docker builds

### 4.1 Move directory
```bash
mv apps/api ./api
rmdir apps
```

**Validation:**
```bash
# Should exist
test -d api && echo "✓ api/ directory exists"

# Should NOT exist  
test -d apps && echo "✗ apps/ still exists" || echo "✓ apps/ removed"

# Verify contents
ls -la api/
# Should show: main.py, config.py, auth.py, models.py, Dockerfile, requirements.txt
```

### 4.2 Update docker-compose.yml

**File:** `/home/tmo/Work/TalkTuah/docker-compose.yml`

**Change lines 60-62:**
```yaml
# BEFORE:
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile

# AFTER:
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
```

**Manual edit:**
```bash
# Open in editor
nano docker-compose.yml

# Or use sed
sed -i 's|context: ./apps/api|context: ./api|g' docker-compose.yml
```

**Validation:**
```bash
# Verify change
grep -A 2 "api:" docker-compose.yml | grep context
# Should show: context: ./api
```

### 4.3 Check .dockerignore

```bash
# Check if apps/ is referenced
grep "apps" api/.dockerignore 2>/dev/null
# If found, remove those lines
```

### 4.4 Update Makefile (if needed)

```bash
# Search for references
grep "apps/api" Makefile
# If found, update to just "api"
```

**No updates needed if no matches found.**

---

## Step 5: Test Docker Build

### 5.1 Build API container
```bash
docker compose build api
```

**Expected output:**
```
[+] Building ...
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load build context
 => CACHED [1/5] FROM docker.io/library/python:3.11-slim
 ...
 => exporting to image
 => => naming to docker.io/library/talktuah-api
```

**If build fails:**
- Check docker-compose.yml context path
- Verify api/Dockerfile exists
- Check for any hardcoded paths in Dockerfile

### 5.2 Verify docker-compose config
```bash
docker compose config | grep -A 5 "api:"
```

**Should show:**
```yaml
  api:
    build:
      context: /home/tmo/Work/TalkTuah/api
      dockerfile: Dockerfile
    ...
```

---

## Step 6: Test Services Startup

### 6.1 Stop current services
```bash
docker compose down
```

### 6.2 Start services
```bash
docker compose up -d
```

### 6.3 Check service status
```bash
docker compose ps
```

**Expected:**
```
NAME                STATUS
vllm-proxy-api      Up
vllm-server         Up
```

### 6.4 Check API health
```bash
# Wait 10 seconds for startup
sleep 10

# Test health endpoint
curl -s http://localhost:8787/api/healthz | jq .
```

**Expected response:**
```json
{
  "status": "healthy" or "degraded",
  "gpu_available": true/false,
  "model_loaded": true/false,
  "upstream_healthy": true/false
}
```

### 6.5 Check logs for errors
```bash
docker compose logs api | tail -50
```

**Look for:**
- No import errors
- No file not found errors  
- "Application startup complete"

---

## Step 7: Commit Changes

```bash
git add -A
git commit -m "Phase 1: Structural cleanup - flatten apps/api, move docs, remove empty dirs"

# Tag for easy rollback
git tag phase1-complete
```

**Validation:**
```bash
git log --oneline -1
# Should show your commit message

git tag | grep phase1
# Should show: phase1-complete
```

---

## Rollback Procedure

If anything breaks:

```bash
# Option 1: Revert last commit
git reset --hard HEAD~1

# Option 2: Go back to backup branch
git checkout backup-before-refactor
mv api apps/api
# Revert docker-compose.yml manually

# Rebuild
docker compose build api
docker compose up -d
```

---

## Verification Checklist

- [ ] `services/` directory removed
- [ ] `docs/services/vllm.md` exists
- [ ] `tests/e2e/` and `tests/unit/` removed (if they were empty)
- [ ] `apps/` directory removed
- [ ] `api/` directory exists at root
- [ ] `docker-compose.yml` updated with `context: ./api`
- [ ] `docker compose build api` succeeds
- [ ] `docker compose up -d` succeeds
- [ ] `curl http://localhost:8787/api/healthz` returns valid JSON
- [ ] No errors in `docker compose logs api`
- [ ] Changes committed to git
- [ ] Git tag `phase1-complete` created

---

## Next Steps

After Phase 1 is complete and validated:
1. Review `REFACTOR_PHASE2.md`
2. Ensure all endpoints are working
3. Create backup before starting Phase 2

---

## Notes

```
Date: ____-__-__
Issues encountered:
- 
- 

Solutions:
- 
- 
```
