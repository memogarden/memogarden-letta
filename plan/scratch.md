# MemoGarden - Session Context (2025-12-27)

**Purpose**: Session notes for next session
**Last Updated**: 2025-12-27

---

## Completed Work (2025-12-27)

### Documentation Consistency Updates
- **Updated skills to reference /plan/future/**:
  - memogarden-schema: Added Future Design Reference section, fixed migrations path
  - memogarden-development: Added Future Design Reference section + Working Directory Reminder
  - memogarden-testing: Enhanced working directory reminder
- **Updated implementation plan**:
  - Step 1.6.5 now references /plan/future/ design docs
  - Fixed all async → sync corrections (10+ locations updated)
  - Updated testing section to reflect Flask (not FastAPI)
  - Updated documentation section to reflect manual API docs
  - Marked Step 1.6 as COMPLETE ✅
- **Updated status.md**:
  - Fixed "memogarden-update" → "change-reviewer/change-commit"
  - Added Architectural Decisions section documenting Flask + sqlite3 choice
  - Added Documentation Updates (2025-12-27) entry
  - Added Testing Infrastructure (2025-12-27) section

### Step 1.6: Testing Infrastructure - COMPLETE ✅
- **Added pytest-cov** to dev dependencies for coverage reporting
- **Verified test suite**: 231 tests passing (excellent coverage)
- **Achieved 90% coverage** (exceeds 80% target)
- **Test organization**: api/, db/, schema/, utils/ modules
- **Fixtures**: test_db and client fixtures in conftest.py

### Step 1.7: Documentation & Development Workflow - COMPLETE ✅
- **Updated README.md**: Comprehensive rewrite with current status
  - Added complete API documentation with curl examples for all 7 endpoints
  - Updated test coverage (231 tests, 90%)
  - Added convenience scripts reference (./scripts/run.sh, test.sh, test-coverage.sh)
  - Updated implementation status (Steps 1.1-1.6 complete)
  - Added design principles section
  - Added development workflow section
- **Verified .env.example**: All 4 environment variables documented
- **End-to-end validation**: Server starts, API responds (health check + accounts endpoint tested)
- **Working directory reminders**: Added to memogarden-development and memogarden-testing skills

**Architectural Alignment**: All documentation now consistent with decision to use synchronous Flask + sqlite3 for simplicity and deterministic debugging.

---

## Completed Work (2025-12-24)

### Documentation & Skills Refactor
- **AGENTS.md**: Condensed from 752 to 179 lines (76% reduction)
- **Created 7 Agent Skills** in `.claude/skills/`:
  - memogarden-development: environment setup, constraints, anti-patterns
  - memogarden-testing: testing philosophy, workflows
  - memogarden-api-endpoint: API endpoint creation
  - memogarden-debugging: debugging workflows
  - memogarden-schema: schema modifications + data model reference
  - change-reviewer: pre-commit review workflow
  - change-commit: git commit operations
- **Created 3 convenience scripts**: `scripts/run.sh`, `scripts/test.sh`, `scripts/test-coverage.sh`
- **Created plan/status.md** for project status tracking
- **Scripts pre-approved** in `.claude/settings.local.json`

### Schema Extension Design
- **Created plan/future/** directory for future design work
- **schema-extension-design.md**: Base schema vs. extensions, two extension mechanisms (SQL + JSON)
- **migration-mechanism.md**: Complete migration workflow with deconfliction and rollback
- **soil-design.md**: Immutable storage architecture for emails, invoices, statements

---

## Implementation Plan Status

**Current Step**: Step 1 COMPLETE ✅ - Core Backend Foundation
**Completed**: Steps 1.1 ✅, 1.2 ✅, 1.3 ✅, 1.4 ✅, 1.5 ✅, 1.6 ✅, 1.7 ✅, 1.6.5 ✅ (design)
**Tests**: 231 passing, 90% coverage

**Ready for**: Step 2 (Authentication & Multi-User Support) OR Production Deployment

**Step 1 Achievement**: Complete REST API with transaction CRUD, entity registry pattern, 90% test coverage, comprehensive documentation with API examples.

---

## Repository State

- **memogarden-core**: Separate git repo (https://github.com/memogarden/memogarden-core)
- **Meta-repo**: `/home/kureshii/memogarden/` - git repo for AGENTS.md, scripts, skills, plan (local only)
- **Scripts location**: `scripts/` in parent directory, referenced from memogarden-core
- **Uncommitted changes**: Documentation updates in plan/, .claude/skills/, pyproject.toml (pytest-cov)

---

## Current Status

### Completed Steps

**Step 1.1: Project Setup & Structure** ✅ (commit: 4bfbbe0)
**Step 1.2: SQLite Database Schema** ✅ (refactored to sync Flask + sqlite3)
**Step 1.3: Pydantic Schemas (API Validation)** ✅ (18 schema tests)
**Step 1.4: Flask Application & Configuration** ✅ (Flask app with CORS, error handling, logging)
**Step 1.5: API Endpoints Implementation** ✅ (7 endpoints, 21 API tests)
**Step 1.6: Testing Infrastructure** ✅ (231 tests, 90% coverage)
**Step 1.6.5: Schema Extension & Migration Design** ✅ (docs in /plan/future/)
**Step 1.7: Documentation & Development Workflow** ✅ (comprehensive README, API docs, working directory reminders)

### Step 1 Complete! ✅ Core Backend Foundation

**Achievements:**
- Complete CRUD API for transactions (7 endpoints)
- Entity registry pattern for global metadata
- 231 tests with 90% coverage
- Comprehensive README with curl examples for all endpoints
- Working directory reminders in agent skills
- Development scripts validated (run.sh, test.sh, test-coverage.sh)
- End-to-end workflow tested and working

**Next:** Step 2 (Authentication & Multi-User Support) or production deployment

### Test Status
**231 tests passing, 90% coverage** (exceeds 80% target)
- API tests: transactions, validation, health
- Database tests: entity, transaction, query, core operations
- Schema tests: types (Timestamp, Date)
- Utils tests: isodatetime, uid
- App tests: main app, config, errors, schemas

---

## Step 1.7: Documentation & Development Workflow

### Objective
Create comprehensive documentation and ensure smooth local development experience.

### Substeps to Complete

#### 1.7.1 Write README.md
**File**: `/home/kureshii/memogarden/memogarden-core/README.md`

**Content needed**:
- Project overview and architecture
- Prerequisites (Python 3.13, Poetry)
- Installation steps (Poetry install)
- Running locally: `./scripts/run.sh` or `poetry run flask --app memogarden_core.main run --debug`
- Running tests: `./scripts/test.sh` or `poetry run pytest`
- Database setup and seed data: `poetry run python -m memogarden_core.db.seed`
- API documentation (list endpoints with curl examples - NO Swagger)
- Environment variables reference (.env.example)
- Development workflow

**Note**: Flask does NOT auto-generate Swagger docs like FastAPI. Provide curl examples for each endpoint.

#### 1.7.2 Document API Endpoints
Add comprehensive docstrings to all endpoint functions in `memogarden_core/api/v1/transactions.py` (already mostly done).

Create API documentation section in README with curl examples:

```bash
# Health check
curl http://localhost:5000/health

# Create transaction
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "amount": -15.50,
    "currency": "SGD",
    "transaction_date": "2025-12-27",
    "description": "Coffee at Starbucks",
    "account": "Personal",
    "category": "Food"
  }'

# List transactions
curl http://localhost:5000/api/v1/transactions

# Get single transaction
curl http://localhost:5000/api/v1/transactions/{id}

# Update transaction
curl -X PUT http://localhost:5000/api/v1/transactions/{id} \
  -H "Content-Type: application/json" \
  -d '{"amount": -16.00}'

# Delete transaction
curl -X DELETE http://localhost:5000/api/v1/transactions/{id}

# List accounts
curl http://localhost:5000/api/v1/transactions/accounts

# List categories
curl http://localhost:5000/api/v1/transactions/categories
```

#### 1.7.3 Development Scripts
**Status**: Convenience scripts already exist in `/scripts/`:
- `run.sh` - Start development server
- `test.sh` - Run tests
- `test-coverage.sh` - Run tests with coverage

Alternatively, add to `pyproject.toml`:
```toml
[tool.poetry.scripts]
dev = "flask --app memogarden_core.main run --debug"
seed = "python -m memogarden_core.db.seed"
test = "pytest"
test-cov = "pytest --cov=memogarden_core"
```

#### 1.7.4 Update .env.example
**File**: `/home/kureshii/memogarden/memogarden-core/.env.example`

Ensure all environment variables are documented:
```
DATABASE_PATH=./data/memogarden.db
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000"]
DEFAULT_CURRENCY=SGD
```

#### 1.7.5 Validate End-to-End Workflow
Test the following workflow:
1. Fresh clone → Poetry install
2. Seed data: `poetry run python -m memogarden_core.db.seed`
3. Run server: `./scripts/run.sh` or `poetry run flask --app memogarden_core.main run --debug`
4. Test API with curl
5. Run tests: `./scripts/test.sh` or `poetry run pytest`
6. Check coverage: `./scripts/test-coverage.sh` or `poetry run pytest --cov=memogarden_core`

Document any gotchas or setup issues in README.

---

## File Checklist

### Files to Update/Create
- 📝 `README.md` - Create comprehensive documentation
- 🔄 `pyproject.toml` - Add poetry scripts section (optional)
- 🔄 `.env.example` - Ensure all vars documented

### Files to Reference
- `memogarden_core/api/v1/transactions.py` - API endpoints (docstrings)
- `memogarden_core/db/seed.py` - Seed data script
- `tests/conftest.py` - Test fixtures

---

## Development Environment

**Working directory**: `/home/kureshii/memogarden/memogarden-core`
**Database**: `./data/memogarden.db`
**Python**: 3.13.11 (via Poetry)
**Framework**: Flask 3.x (synchronous)
**Database Library**: sqlite3 (built-in)
**Tests**: 94 passing

**Quick commands:**
```bash
# Run Flask dev server (using convenience script)
./scripts/run.sh

# Or run manually
poetry run flask --app memogarden_core.main run --debug

# Seed database
poetry run python -m memogarden_core.db.seed

# Run tests
./scripts/test.sh

# Or run tests manually
poetry run pytest

# Run tests with coverage
./scripts/test-coverage.sh

# Or run coverage manually
poetry run pytest --cov=memogarden_core

# Run specific test file
poetry run pytest tests/api/test_transactions.py -v
```

---

## Key Architectural Decisions

### Why Flask + sqlite3 (Not FastAPI + aiosqlite)?
1. **Simplicity**: Synchronous code is easier to understand and debug
2. **Determinism**: No async/await complexity, execution order is predictable
3. **Sufficient for personal use**: Single-user system with low traffic
4. **Built-in sqlite3**: No external async database dependencies needed
5. **Better debugging**: Stack traces are clearer without async context switching

### Consequences
- No auto-generated Swagger UI docs (manual documentation required)
- Manual API documentation with curl examples
- Simpler test fixtures (Flask test client, not AsyncClient)
- Request context pattern for database connections (Flask `g` object)

---

## Key Reminders for Step 1.7

1. **Flask != FastAPI**: No auto-generated Swagger docs - provide curl examples
2. **Poetry scripts**: Use `flask --app` instead of `uvicorn`
3. **Convenience scripts exist**: Use `./scripts/run.sh`, `./scripts/test.sh`
4. **Seed script**: Remind users to run `poetry run python -m memogarden_core.db.seed`
5. **Environment**: Document `.env` setup from `.env.example`
6. **Coverage**: Include coverage command (target >80% achieved)
7. **Test everything**: Verify end-to-end workflow works on fresh clone

---

## After Step 1.7

When Step 1.7 is complete:
- Update implementation.md to mark Step 1.7 as complete
- Update plan/status.md
- Consider creating git commit for documentation work
- Ready for Step 2 (Authentication & Multi-User Support)

---

## Future Design Reference

Schema extension and migration mechanisms are documented in `/plan/future/`:
- **schema-extension-design.md**: Base schema vs. extensions philosophy
- **migration-mechanism.md**: Migration workflow with validation and rollback
- **soil-design.md**: Immutable storage architecture

These are design references for future implementation. No code changes needed until Step 3+.

---

Ready to implement Step 1.7: Documentation & Development Workflow!
