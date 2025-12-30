# MemoGarden Project Status

**Last Updated**: 2025-12-31

## Active Step

**Step 5 IN PROGRESS - Flutter App Foundation** 🔄

**Learning-Focused Development:**
- Repository: https://github.com/memogarden/app-budget
- Local: `app-budget/` directory
- Approach: Interactive development (user runs commands, AI guides)
- Architecture: Local SQLite first, sync-later design

**Substeps (11 total, UI-first):**
- ⏳ **5.1** - Project Initialization & Setup
- ⏳ **5.2** - Database Schema Setup
- ⏳ **5.3** - Data Models
- ⏳ **5.4** - Repository Layer
- ⏳ **5.5** - Transaction Capture Screen (Static UI)
- ⏳ **5.6** - Add State to Capture Screen
- ⏳ **5.7** - Wire Up Data Flow
- ⏳ **5.8** - Transaction List Screen
- ⏳ **5.9** - Navigation Structure
- ⏳ **5.10** - Design System Polish
- ⏳ **5.11** - Testing & Refinement

## Architecture Update

**Platform-First Lean Approach:**
- **Soil MVP**: Minimal immutable storage (artifacts, deltas, schema snapshots)
- **Core MVP**: Item-based entity system with dual timestamps
- **Budget MVP**: Financial transactions on platform foundations

**Reference Documents:**
- [plan/memogarden_prd_v4.md](memogarden_prd_v4.md) - Complete platform specification
- [plan/budget_implementation.md](budget_implementation.md) - Updated implementation plan

## Repository

**Core API**: https://github.com/memogarden/memogarden-core
**Budget App**: https://github.com/memogarden/app-budget

## Completed Work

### Step 2: Authentication & Multi-User Support ✅ COMPLETE (2025-12-29)

**All 10 Substeps Completed:**
- ✅ **2.1** - Database Schema: Users and API Keys (commit: 0744b9d)
- ✅ **2.2** - Pydantic Schemas: User, APIKey, Auth (commit: 1a3729a)
- ✅ **2.3** - JWT Token Service (30-day expiry, HS256)
- ✅ **2.4** - Authentication Endpoints (login, logout, user profile)
- ✅ **2.5** - API Key Management Endpoints (list, create, revoke)
- ✅ **2.6** - Authentication Decorators (@localhost_only, @first_time_only)
- ✅ **2.7** - HTML UI Pages (login, api-keys, settings with TailwindCSS)
- ✅ **2.8** - Testing Infrastructure (165 auth tests, 91% coverage)
- ✅ **2.9** - Documentation & Integration (ApiV1-level auth, README updates)
- ✅ **2.10** - Refactor & Test Profiling (1.14s test suite, 97.6% faster)

**Key Deliverables:**
- User authentication with JWT tokens (30-day expiry)
- API key management for agents (create, list, revoke)
- Admin registration flow (localhost only, one-time setup)
- HTML UI pages for auth and API key management
- All API endpoints protected by default (ApiV1 blueprint-level auth)
- Test suite optimized from 47.95s to 1.14s (97.6% faster)
- Code refactoring: removed ~120 lines of auth duplication
- 396 tests passing with 91% coverage

**Test Results:**
- **All 396 tests passing** in 1.14s
- **Coverage**: 91% (exceeds 80% target)
- **No test mocks** (uses real SQLite)

### ~~Step 3: Soil MVP Foundation~~

**REMOVED**: Not needed for Budget MVP.</think>

**Completed:**
- ✅ **1.1** - Project Setup & Structure
- ✅ **1.2** - SQLite Database Schema with entity registry pattern
- ✅ **1.3** - Pydantic Schemas for API validation
- ✅ **1.4** - Flask Application & Configuration
- ✅ **1.5** - API Endpoints Implementation (7 transaction endpoints)
- ✅ **1.6** - Testing Infrastructure (231 tests, 90% coverage)
- ✅ **1.6.5** - Schema Extension & Migration Design (docs in `/plan/future/`)
- ✅ **1.7** - Documentation & Development Workflow (comprehensive README)

**Deliverables:**
- Complete CRUD API for transactions (create, read, update, delete, list, labels)
- Entity registry pattern for global metadata
- 231 tests with 90% coverage (exceeds 80% target)
- Comprehensive README with API documentation

## Architectural Decisions

### Platform Architecture (from PRD v4)
- **Item-based entities**: All entities extend `item` base type with dual timestamps
- **Two-layer storage**: Soil (immutable facts) + Core (mutable state)
- **Document-centric**: Transactions linked to artifacts via relations
- **Lean MVP**: Minimal platform features to support Budget app

### Tech Stack
- **Backend**: Flask (synchronous) + sqlite3 (built-in Python module)
- **Storage**: SQLite for Core, filesystem for Soil
- **Philosophy**: Deterministic synchronous execution for simplicity and debugging

### Design Principles
- **No ORM**: Raw SQL queries with parameterized statements
- **Item base type**: Platform metadata (uuid, _type, realized_at, canonical_at) in item table
- **Labels not Entities**: Accounts and categories are user-defined strings
- **UTC Everywhere**: All timestamps in ISO 8601 UTC format
- **Test-Driven**: Comprehensive test suite (>80% coverage target)
- **No Mocks**: Tests use real dependencies (SQLite, filesystem)

### Code Quality
- **Test Suite**: Optimized to 1.14s (97.6% faster than original 47.95s)
- **Code Duplication**: Removed ~120 lines of auth duplication
- **Coverage**: 91% maintained across refactoring

## Platform Foundation Decisions

### Soil MVP Scope
- **Storage**: Filesystem-based (no database)
- **API**: Simple Python module (`memogarden_core/soil/`)
- **Artifact types**: emails, pdfs, statements (MVP)
- **Reference format**: `artifact:{type}-{uuid}`
- **Location**: Configurable via `SOIL_PATH` (default: `./soil`)

### Item Type Migration Strategy
- **Approach**: Forward migration with rollback script
- **Dual timestamps**: `realized_at` (system) + `canonical_at` (user)
- **Data preservation**: All existing data migrated, no loss
- **Schema archival**: Snapshot stored in Soil before migration
- **Test requirement**: All 396 existing tests must pass after migration

### Relation Types (MVP)
- **Implemented**: `source`, `reconciliation`, `artifact`
- **Deferred**: Project System relations (triggers, replies_to, mentions, etc.)
- **Single table**: Use `relations` table for MVP (defer UniqueRelation/MultiRelation split)

### Delta Tracking
- **Granularity**: Field-level (one delta per field changed)
- **Storage**: Database table + JSON files in Soil
- **Timing**: After database commit (transactional consistency)

## Next Steps

See [budget_implementation.md](budget_implementation.md) for detailed roadmap.

**Current Phase**: Step 5 (Flutter App Foundation)

**Step 5 Approach**: Learning-focused, interactive development
- User is new to Flutter/Dart
- AI guides, user runs commands and adds code
- UI-first with small reviewable steps
- Local SQLite database (DB-first architecture)
- Simple state management (`setState()`)
- Repository layer for future sync integration

**Substeps** (11 total, incremental):
- 5.1: Project Initialization & Setup
- 5.2: Database Schema Setup
- 5.3: Data Models
- 5.4: Repository Layer
- 5.5-5.6: Transaction Capture Screen (UI then state)
- 5.7: Wire Up Data Flow
- 5.8: Transaction List Screen
- 5.9: Navigation Structure
- 5.10: Design System Polish
- 5.11: Testing & Refinement

---

**Guidelines**: Omit technical details (those belong in architecture.md or skills). Always update this file after completion of each task.
