# TalkTuah Refactoring Checklist

**Created:** 2025-10-16  
**Purpose:** Reorganize project structure, trim main.py from 744→50 lines, eliminate duplicate logic  
**Status:** 🔴 PLANNING PHASE  
**Delete when:** All phases complete and tested

---

## 📊 Overview

### Current Problems
1. **main.py is 744 lines** - Needs splitting into modules
2. **Duplicate logic** - API calls shell scripts for downloads
3. **Misleading structure** - `services/` contains only docs, `apps/` has only 1 app
4. **Frontend clutter** - Multiple config files, utils not organized

### Target Structure
```
TalkTuah/
├── api/                    # Flattened from apps/api/
│   ├── routers/           # ~120 lines each
│   ├── lib/               # Business logic ~80 lines each
│   ├── utils/             # HTTP, streaming ~50 lines each
│   └── main.py            # ~50 lines (down from 744)
├── frontend/
│   ├── utils/             # Consolidated utilities
│   └── widgets/
├── scripts/
│   ├── dev/               # Testing only
│   └── setup/             # One-time setup only
└── docs/
    └── services/          # Moved from services/vllm/
```

### Phases Summary

| Phase | Risk | Time | Can Break |
|-------|------|------|-----------|
| 1: Structural Cleanup | 🟢 Low | 30min | Docs only |
| 2: API Refactoring | 🟡 Medium | 3-4hr | All API endpoints |
| 3: Eliminate Duplicates | 🔴 High | 2-3hr | Downloads, model mgmt |
| 4: Frontend Cleanup | 🟢 Low | 1hr | Frontend only |

---

## Phase 1: Low-Risk Structural Cleanup ✅

**Goal:** Remove misleading directories, flatten unnecessary nesting  
**Time:** 30 minutes  
**See:** `REFACTOR_PHASE1.md` for detailed steps

### Checklist Summary
- [ ] Move `services/vllm/` → `docs/services/vllm.md`
- [ ] Remove empty test directories (`tests/e2e`, `tests/unit`)
- [ ] Flatten `apps/api/` → `api/`
- [ ] Update docker-compose.yml build context
- [ ] Update documentation references
- [ ] **Validation:** `docker compose build api` succeeds

---

## Phase 2: API Refactoring (main.py 744→50 lines) ⚙️

**Goal:** Split monolithic main.py into organized modules  
**Time:** 3-4 hours  
**See:** `REFACTOR_PHASE2.md` for detailed steps

### File Creation Order (Low→High Risk)

1. **Utilities** (Safest - pure functions)
   - [ ] `api/utils/streaming.py` - SSE streaming (lines 63-93)
   - [ ] `api/utils/http_client.py` - HTTP client management (lines 45-60, 122-172)

2. **Business Logic** (Services layer)
   - [ ] `api/lib/vllm.py` - vLLM health checks (lines 248-314, 596-638)
   - [ ] `api/lib/docker.py` - Container operations (lines 519-576, 647-663)
   - [ ] `api/lib/models.py` - Model management (lines 370-424, 467-593)
   - [ ] `api/lib/downloads.py` - Download management (lines 427-464, 672-743)

3. **Routers** (API endpoints)
   - [ ] `api/routers/chat.py` - Chat + models list (lines 96-214, 216-245)
   - [ ] `api/routers/models.py` - Model management endpoints
   - [ ] `api/routers/monitoring.py` - Health, metrics, root

4. **Main Refactor**
   - [ ] Rewrite `api/main.py` to ~50 lines (app init + router registration)

### Critical Dependencies
- **Imports:** config, models, auth stay in api/ root
- **Docker mount:** `.:/workspace` allows subprocess calls to scripts
- **Rate limiter:** Must be passed to routers via app.state or dependency
- **HTTP client:** Lifecycle managed via app startup/shutdown events

### Validation Checklist
- [ ] All endpoints respond correctly
- [ ] Streaming works
- [ ] Model switching works
- [ ] Downloads work (via subprocess for now)
- [ ] No errors in logs

---

## Phase 3: Eliminate Duplicate Logic 🔥

**Goal:** Remove shell script dependencies, pure Python implementation  
**Time:** 2-3 hours  
**See:** `REFACTOR_PHASE3.md` for detailed steps

### Current Duplicates

| Function | API Endpoint | Shell Script | Action |
|----------|-------------|--------------|--------|
| Download | POST /api/download-model | download_model.sh | ✂️ Remove subprocess call |
| Delete | ❌ Missing | delete_model.sh | ➕ Create API endpoint |
| Progress | GET /api/download-progress | /tmp/ text file | ✂️ Use proper state mgmt |

### Refactoring Steps
- [ ] Implement Python download using `huggingface_hub` library
- [ ] Replace `/tmp/model_download_progress.txt` with in-memory state
- [ ] Add `DELETE /api/delete-model` endpoint
- [ ] Convert scripts to thin CLI wrappers (optional)

---

## Phase 4: Frontend Cleanup 🎨

**Goal:** Consolidate config files, organize utilities  
**Time:** 1 hour  
**See:** `REFACTOR_PHASE4.md` for detailed steps

### Changes
- [ ] Move `llm_client.py` → `frontend/utils/api_client.py`
- [ ] Move `theme_loader.py` → `frontend/utils/theme.py`
- [ ] Merge `settings.py` into `config.py` or vice versa
- [ ] Update imports in `TuivLLM.py` and widgets

---

## Testing & Validation 🧪

### Baseline Before Starting
```bash
# Save baseline behavior
curl http://localhost:8787/api/healthz > baseline_health.json
curl -H "Authorization: Bearer $PROXY_API_KEY" \
     http://localhost:8787/api/models > baseline_models.json
```

### After Each Phase
```bash
# Compare responses
curl http://localhost:8787/api/healthz | diff - baseline_health.json
curl -H "Authorization: Bearer $PROXY_API_KEY" \
     http://localhost:8787/api/models | diff - baseline_models.json
```

### Full Integration Test
```bash
# Start fresh
docker compose down
docker compose build
docker compose up -d

# Wait for startup
sleep 30

# Run all endpoints
./scripts/dev/test_model_management.sh
./scripts/dev/test_api_temperature.sh

# Test frontend
cd frontend && bash run.sh
# Try sending a message
```

---

## Rollback Procedures 🔄

### If Phase 1 Breaks
```bash
git checkout backup-before-flatten
mv api/ apps/api/
# Revert docker-compose.yml
```

### If Phase 2 Breaks
```bash
cp api/main.py.backup api/main.py
rm -rf api/routers api/lib api/utils
docker compose build api
docker compose restart api
```

### If Phase 3 Breaks
```bash
git checkout <commit-before-phase3>
docker compose build api
docker compose restart api
```

### Nuclear Option
```bash
# Full reset to last known good state
git stash
docker compose down
git checkout main  # or last good commit
docker compose build
docker compose up -d
```

---

## Progress Tracking

### Phase 1: Structural Cleanup
- [ ] Started: ____-__-__
- [ ] Completed: ____-__-__
- [ ] Tested: ____-__-__
- [ ] Issues: _______________________

### Phase 2: API Refactoring  
- [ ] Started: ____-__-__
- [ ] Completed: ____-__-__
- [ ] Tested: ____-__-__
- [ ] Issues: _______________________

### Phase 3: Eliminate Duplicates
- [ ] Started: ____-__-__
- [ ] Completed: ____-__-__
- [ ] Tested: ____-__-__
- [ ] Issues: _______________________

### Phase 4: Frontend Cleanup
- [ ] Started: ____-__-__
- [ ] Completed: ____-__-__
- [ ] Tested: ____-__-__
- [ ] Issues: _______________________

---

## Notes & Discoveries

### Issues Found During Refactoring
```
Date       | Issue | Solution | Ref
-----------|-------|----------|----
           |       |          |
           |       |          |
```

### Performance Improvements
```
Metric               | Before | After | Change
---------------------|--------|-------|-------
API Response Time    |        |       |
Docker Build Time    |        |       |
main.py Line Count   | 744    |       |
```

---

## Completion Checklist

- [ ] All phases complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No regressions in functionality
- [ ] Performance maintained or improved
- [ ] Team has reviewed changes
- [ ] **DELETE THIS FILE**

---

**Detailed phase instructions:** See `REFACTOR_PHASE[1-4].md` files
