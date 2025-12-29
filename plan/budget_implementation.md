# MemoGarden Budget - Implementation Plan

## Overview

Building a lightweight personal expenditure capture and review system with three main components:
- **memogarden-core**: Flask backend with SQLite (platform foundation)
- **memogarden-soil**: Immutable append-only storage layer (filesystem-based)
- **memogarden-budget**: Flutter app (web + Android)

**Architecture**: Lean MVP approach with platform foundations
- Soil MVP: Minimal immutable storage (artifacts, deltas, schema snapshots)
- Core MVP: Item-based entity system with Soil integration
- Budget MVP: Financial transaction management on platform

**Tech Stack:** Python 3.13, Flask (synchronous), SQLite (no ORM), Poetry, pytest

**Repositories:**
- Core: https://github.com/memogarden/memogarden-core
- Budget: https://github.com/memogarden/memogarden-budget (to be created)

**Platform Reference:** [plan/memogarden_prd_v4.md](memogarden_prd_v4.md) - Complete platform specification

---

## Implementation Steps

### Step 1: Core Backend Foundation ✅ COMPLETE (2025-12-27)

**Establish foundational backend API with SQLite database, transaction CRUD operations, and testing infrastructure.**

#### Completed Substeps:
- ✅ **1.1** - Project Setup & Structure (commit: 4bfbbe0)
- ✅ **1.2** - SQLite Database Schema with entity registry pattern
- ✅ **1.3** - Pydantic Schemas for API validation
- ✅ **1.4** - Flask Application & Configuration (CORS, error handling, logging)
- ✅ **1.5** - API Endpoints Implementation (7 transaction endpoints)
- ✅ **1.6** - Testing Infrastructure (231 tests, 90% coverage)
- ✅ **1.6.5** - Schema Extension & Migration Design (docs in `/plan/future/`)
- ✅ **1.7** - Documentation & Development Workflow (comprehensive README)

**Deliverables:**
- Complete CRUD API for transactions (create, read, update, delete, list, labels)
- Entity registry pattern for global metadata
- 231 tests with 90% coverage (exceeds 80% target)
- Comprehensive README with API documentation

See [memogarden-core/docs/architecture.md](memogarden-core/docs/architecture.md) for detailed architecture and design patterns.


### Step 2: Authentication & Multi-User Support ✅ COMPLETE (2025-12-29)

**Objective:** Add user management, JWT authentication for device clients, and API key support for agents.

#### Completed Substeps:
- ✅ **2.1** - Database Schema: Users and API Keys (commit: 0744b9d)
- ✅ **2.2** - Pydantic Schemas (User, APIKey, Auth) (commit: 1a3729a)
- ✅ **2.3** - JWT Token Service
- ✅ **2.4** - Authentication Endpoints (login, logout, user profile)
- ✅ **2.5** - API Key Management Endpoints (list, create, revoke)
- ✅ **2.6** - Authentication Decorators (@localhost_only, @first_time_only) (commit: 711ff3a)
- ✅ **2.7** - HTML UI Pages (login, api-keys, settings)
- ✅ **2.8** - Testing Infrastructure (165 auth tests)
- ✅ **2.9** - Documentation & Integration (ApiV1-level auth, README updates)
- ✅ **2.10** - Refactor & Test Profiling (1.14s test suite, 97.6% faster)

**Deliverables:**
- User authentication with JWT tokens (30-day expiry)
- API key management for agents (create, list, revoke)
- Admin registration flow (localhost only, one-time setup)
- HTML UI pages for auth and API key management
- All API endpoints protected by default (ApiV1 blueprint-level auth)
- Test suite optimized from 47.95s to 1.14s (97.6% faster)
- Code refactoring: removed ~120 lines of auth duplication
- 396 tests passing with 91% coverage

**Key Features:**
- Password hashing with bcrypt (work factor 12)
- Case-insensitive usernames (normalized to lowercase)
- JWT and API key authentication support
- API keys: `mg_sk_<type>_<random>` format, shown only on creation
- Soft delete for API keys (revoked_at timestamp)
- Mobile-friendly TailwindCSS UI pages

See [memogarden-core/docs/architecture.md](memogarden-core/docs/architecture.md) for authentication architecture details.

### Step 2.5: Soil MVP Foundation 🔄 IN PLANNING

**Objective:** Implement minimal immutable storage layer for artifact archival, delta tracking, and schema snapshots.

**Approach:** Lean MVP - filesystem-based storage (no database), simple Python API

#### Components:

**2.5.1 Soil Storage API**
- Create `memogarden_core/soil/` module
- Filesystem storage with UUID-based artifact IDs
- Environment variable `SOIL_PATH` (default: `./soil`)
- Directory structure:
  ```
  soil/
  ├── artifacts/
  │   ├── emails/
  │   ├── pdfs/
  │   └── statements/
  ├── core-delta/
  │   └── {entity_uuid}/
  │       └── {delta_uuid}.json
  └── core-migration/
      └── snapshots/
          └── {date}-schema.sql
  ```

**2.5.2 Artifact Management**
- `archive_artifact(artifact_type, content) -> artifact_id`
- `get_artifact(artifact_id) -> content`
- Artifact types: `emails`, `pdfs`, `statements`
- UUID-based IDs with type prefix (e.g., `email-a7f3e2b1...`)

**2.5.3 Delta Storage**
- `write_delta(entity_uuid, delta_dict) -> delta_id`
- `get_deltas(entity_uuid) -> list[delta_dict]`
- JSON format per delta record
- Append-only (never modify existing deltas)

**2.5.4 Schema Snapshots**
- `snapshot_schema() -> snapshot_path`
- Automatic SQL dump before migrations
- Date-stamped filenames
- Integration with `_schema_metadata` table

**2.5.5 Testing & Documentation**
- Filesystem operation tests (use pytest tmpdir)
- Soil API documentation
- Integration examples for Core

**Deliverables:**
- Soil storage API module (~200 lines)
- 50+ tests for filesystem operations
- Documentation and usage examples
- Integration hooks for Core mutations

---

### Step 2.6: Core Refactor to Item Type 🔄 IN PLANNING

**Objective:** Refactor existing schema to use Item base type from PRD v4 platform architecture.

**Rationale:** PRD v4 is the complete platform specification. Adopting Item type now enables Soil integration and reduces future migration debt.

#### Migration Strategy:

**2.6.1 Create Item Table**
```sql
CREATE TABLE item (
    uuid TEXT PRIMARY KEY,
    _type TEXT NOT NULL,           -- 'Transaction', 'Recurrence', 'User', etc.
    realized_at TEXT NOT NULL,     -- System time (when recorded)
    canonical_at TEXT NOT NULL,    -- User time (when it happened)
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_item_type ON item(_type);
CREATE INDEX idx_item_realized ON item(realized_at);
```

**2.6.2 Migration Script**
- Create migration: `entity` → `item`
- Migrate data:
  - `entity.type` → `item._type`
  - `entity.created_at` → `item.realized_at` AND `item.canonical_at`
  - Keep `entity.created_at`, `entity.updated_at` as-is
- Update foreign keys:
  - `transactions.id` → references `item.uuid`
  - `users.id` → references `item.uuid`
  - `api_keys.id` → references `item.uuid`
- Archive old schema snapshot to Soil before migration
- Rollback script (drop `item`, restore `entity`)

**2.6.3 Update Entity Operations**
- Refactor `db/entity.py` to use `item` table
- Update all `get_entity()`, `create_entity()`, etc. calls
- Add `realized_at` / `canonical_at` to Pydantic schemas
- Update foreign key constraints in schema.sql

**2.6.4 Testing & Validation**
- Migration test suite (before/after data validation)
- Run all 396 existing tests (must still pass)
- Add tests for dual timestamp behavior
- Test rollback script

**Deliverables:**
- Migration script (forward + rollback)
- Updated schema with Item base type
- All tests passing with new schema
- Schema snapshot archived to Soil
- Migration documentation

---

### Step 3: Advanced Core Features (Updated)

**Objective:** Implement recurrences, relations, and delta tracking with Soil integration.

**Note:** All entities now use Item base type (from Step 2.6). Relations reference both Items and Soil artifacts.

**Components:**

#### 3.1 Recurrences (extends Item)
- Create `recurrences` table (extends `item` with rrule, entities)
- iCal rrule parsing library integration
- Recurrence template → transaction generation
- CRUD endpoints for recurrences
- UI in Budget app for managing recurring transactions

**Schema:**
```sql
CREATE TABLE recurrences (
    uuid TEXT PRIMARY KEY,
    rrule TEXT NOT NULL,           -- iCal rrule string
    entities TEXT NOT NULL,        -- JSON: transaction templates
    valid_from TEXT NOT NULL,
    valid_until TEXT,

    FOREIGN KEY (uuid) REFERENCES item(uuid) ON DELETE CASCADE
);
```

#### 3.2 Relations (with Soil integration)
- Create `relations` table (links Items to Items or Soil artifacts)
- Link Core entities to Soil artifacts (emails, PDFs, statements)
- CRUD endpoints for relations
- Reference resolution: `artifact:{uuid}` format
- Support relation types: `source`, `reconciliation`, `artifact`

**Schema:**
```sql
CREATE TABLE relations (
    id TEXT PRIMARY KEY,
    core_id TEXT NOT NULL,         -- Item UUID
    ref_id TEXT NOT NULL,          -- Item UUID OR Soil artifact ID
    ref_type TEXT NOT NULL,        -- 'source', 'reconciliation', 'artifact'
    notes TEXT,
    created_at TEXT NOT NULL,
    revoked_on TEXT,

    FOREIGN KEY (core_id) REFERENCES item(uuid)
);
```

#### 3.3 Deltas (Audit Log + Soil Archival)
- Create `deltas` table (field-level change tracking)
- Emit deltas on all mutations (INSERT/UPDATE/DELETE)
- Delta tracking middleware/decorator
- Automatic archival to Soil (`soil/core-delta/{entity_uuid}/{delta_uuid}.json`)
- Query endpoints for audit history

**Schema:**
```sql
CREATE TABLE deltas (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,     -- Item._type
    entity_id TEXT NOT NULL,       -- Item UUID
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    rationale TEXT,
    author TEXT NOT NULL,
    timestamp TEXT NOT NULL,

    FOREIGN KEY (entity_id) REFERENCES item(uuid)
);
```

**Soil Integration:**
- After database commit, write delta JSON to Soil
- Delta format: `{id, entity_type, entity_id, field, old_value, new_value, rationale, author, timestamp}`
- Stored as: `soil/core-delta/{entity_uuid}/{delta_uuid}.json`

#### 3.4 Reference Resolution
- Parse artifact references (format: `artifact:{type}-{uuid}`)
- Validate artifacts exist in Soil before creating relations
- Basic reference syntax (defer complex fragment refs to Project System)

**Deliverables:**
- Recurrence system with iCal compatibility
- Relation management with artifact linking
- Complete audit trail via deltas (DB + Soil)
- Reference resolution for Soil artifacts
- API endpoints for all four features

---

### Step 4: Flutter App Foundation

**Objective:** Initialize Budget app with basic UI and API integration.

**Components:**
- Create `memogarden-budget` repository
- Flutter project setup (web + Android)
- Project structure (clean architecture or feature-based)
- HTTP client for Core API
- State management (Riverpod or Provider)
- Navigation structure
- Design system (colors, typography, components)

**Screens:**
- Transaction capture screen (Monefy-inspired)
- Transaction list screen
- Settings screen

**Deliverables:**
- Flutter app running on web and Android
- API client connected to Core
- Basic transaction creation flow
- Simple, fast UI (<5 second capture goal)

---

### Step 5: Budget App Features

**Objective:** Complete Budget app with spending review and management features.

**Components:**

#### 5.1 Spending Review
- Daily spending view (list grouped by date)
- Monthly summary with category breakdown
- Yearly overview with trends
- Charts/visualizations (optional, defer if complex)

#### 5.2 Account & Category Management
- Account selection during transaction creation
- Category picker with icons
- Manage accounts (create, edit, delete)
- Manage categories (create, edit, delete)

#### 5.3 Transaction Management
- Edit transaction screen
- Delete transaction with confirmation
- Transaction detail view
- Search/filter transactions

#### 5.4 Recurring Transactions UI
- Create recurring transaction template
- View upcoming recurring transactions
- Mark occurrence as completed/skipped

**Deliverables:**
- Complete spending review interface
- Account and category management
- Full transaction CRUD in UI
- Recurring transaction interface

---

### Step 6: Agent Integration & Deployment

**Objective:** Enable agent workflows and prepare for production deployment.

**Components:**

#### 6.1 Agent Workflows
- Statement reconciliation endpoint
- Email parsing integration (with Soil)
- Transaction suggestion API
- Bulk operations for agents
- Reconciliation status tracking

#### 6.2 Testing & CI/CD
- Integration tests for full workflows
- E2E tests for critical paths
- GitHub Actions for CI
- Automated testing on PR

#### 6.3 Deployment
- Docker configuration for Core API
- Docker Compose for local full-stack
- Railway deployment configuration
- Raspberry Pi deployment guide
- Environment variable management
- Database backup strategy

#### 6.4 Documentation
- API documentation for agents
- Agent integration guide
- Deployment runbook
- Troubleshooting guide

**Deliverables:**
- Agent-ready API endpoints
- CI/CD pipeline
- Production deployment configurations
- Complete documentation

---

## Key Principles

### Platform Architecture (from PRD v4)
- **Item-based entities**: All entities extend `item` base type with dual timestamps (`realized_at`, `canonical_at`)
- **Two-layer storage**: Soil (immutable facts) + Core (mutable state)
- **Document-centric**: Transactions linked to immutable artifacts via relations
- **Lean MVP**: Implement minimal platform features to support Budget app, grow iteratively

### Database Philosophy
- **SQLite as source of truth**: Schema.sql defines reality, Pydantic validates API
- **Item base type**: Common platform metadata (uuid, _type, realized_at, canonical_at) in `item` table, domain attributes in type-specific tables
- **Plain UUIDs**: Entity IDs are standard UUID4 strings (no prefixes), type stored in `_type` field
- **Dual timestamps**: System time (`realized_at`) + user time (`canonical_at`) for all entities
- **UTC everywhere**: All timestamps in UTC ISO 8601 format
- **Day-level dates**: Transaction dates are DATE (YYYY-MM-DD), not timestamps
- **No ORM**: Raw SQL queries with sqlite3 for control and simplicity
- **Synchronous execution**: Deterministic, simpler debugging, sufficient for personal use

### Soil Philosophy
- **Immutable storage**: Artifacts never modified once archived (append-only)
- **Filesystem-based**: No database needed for MVP (use Python pathlib)
- **Reference format**: `artifact:{type}-{uuid}` for cross-referencing
- **Automatic archival**: Deltas written to Soil after database commit
- **Schema snapshots**: Full schema dumps archived before migrations

### API Philosophy
- **RESTful conventions**: Standard HTTP methods and resource URLs
- **Versioning**: `/api/v1/` prefix for future compatibility
- **Rich filtering**: Query parameters for common operations
- **Pagination ready**: Limit/offset from the start

### Development Philosophy
- **Minimal dependencies**: Only add what's needed
- **Local-first**: Everything runs without external services
- **Test early**: Tests written alongside features
- **Document as you go**: README and docstrings updated incrementally
- **Incremental delivery**: Each step delivers working software
- **Platform-first lean**: Build minimal platform foundations, then applications on top

---

## Critical Files Reference

### Current Step Critical Files (Step 2.5-2.6 Planning)
- `/home/kureshii/memogarden/plan/budget_prd.md` - Budget app requirements
- `/home/kureshii/memogarden/plan/memogarden_prd_v4.md` - Platform architecture reference (Item type, Soil)
- `/home/kureshii/memogarden/memogarden-core/memogarden_core/schema/schema.sql` - Current database schema (to be migrated)
- `/home/kureshii/memogarden/memogarden-core/memogarden_core/db/` - Database operations (entity.py to be refactored)
- `/home/kureshii/memogarden/plan/future/soil-design.md` - Soil architecture reference

### Platform Architecture References
- `plan/memogarden_prd_v4.md` - Complete platform specification (Soil + Core + applications)
- `plan/future/soil-design.md` - Soil storage architecture details
- `plan/future/schema-extension-design.md` - Schema versioning and extension system
- `plan/future/migration-mechanism.md` - Database migration workflow

---

## Next Actions

**Step 1 COMPLETE** ✅ (Core Backend Foundation - 2025-12-27)

**Step 2 COMPLETE** ✅ (Authentication & Multi-User Support - 2025-12-29)
- 2.1: Database Schema ✅
- 2.2: Pydantic Schemas ✅
- 2.3: JWT Token Service ✅
- 2.4: Authentication Endpoints ✅
- 2.5: API Key Management Endpoints ✅
- 2.6: Authentication Decorators ✅
- 2.7: HTML UI Pages ✅
- 2.8: Testing Infrastructure ✅
- 2.9: Documentation & Integration ✅
- 2.10: Refactor & Test Profiling ✅

**Currently Planning:** Platform Foundation (Steps 2.5-2.6)

**Next:**
- **Step 2.5** (Soil MVP Foundation) - Implement filesystem-based immutable storage
- **Step 2.6** (Core Refactor to Item Type) - Migrate from `entity` to `item` table
- **Step 3** (Advanced Core Features) - Recurrences, Relations, Deltas with Soil integration

---

## Implementation Sequence Rationale

**Step 1 (Core Backend)** comes first because:
- Backend is single source of truth
- API contract defines all interactions
- Can validate data model in isolation
- Easy to test without UI dependencies

**Step 2 (Auth)** comes after Core because:
- Core CRUD validated first
- Auth affects all endpoints, easier to add after basics work
- Can test with "system" author initially

**Step 2.5 (Soil MVP)** comes before Core refactor because:
- Soil has no dependencies (filesystem only)
- Core refactor needs Soil for schema snapshots
- Relations and deltas need Soil integration
- Can be implemented independently (1-2 days)

**Step 2.6 (Core Refactor to Item Type)** comes before Step 3 because:
- Adopting platform architecture now reduces future migration debt
- All new entities (Recurrences, Relations) should extend Item
- Easier to refactor 3 tables (transactions, users, api_keys) now than 10+ later
- Enables Soil integration from the ground up

**Step 3 (Advanced Features)** after refactor because:
- Recurrences, Relations, Deltas should use Item base type
- Soil integration requires Item-based foreign keys
- Cleaner to implement with new architecture than migrate later

**Step 4-5 (Flutter)** come after stable API because:
- Need stable API contract first
- Backend can be tested independently
- Reduces rework from API changes

**Step 6 (Agents & Deployment)** last because:
- Most complex workflows
- Depends on all core features
- Can defer without blocking user value

---

## Platform Foundation Decisions

The following design decisions from [budget_prd_update_analysis.md](budget_prd_update_analysis.md) are adopted:

### Soil MVP Scope
- **Storage**: Filesystem-based (no database)
- **API**: Simple Python module (`memogarden_core/soil/`)
- **Artifact types**: emails, pdfs, statements (MVP)
- **Reference format**: `artifact:{type}-{uuid}`
- **Location**: Configurable via `SOIL_PATH` environment variable (default: `./soil`)

### Item Type Migration
- **Approach**: Forward migration with rollback script
- **Dual timestamps**: `realized_at` (system) + `canonical_at` (user)
- **Data preservation**: All existing data migrated, no loss
- **Schema archival**: Snapshot stored in Soil before migration
- **Test requirement**: All 396 existing tests must pass after migration

### Relation Types (MVP)
- **Subset implemented**: `source`, `reconciliation`, `artifact`
- **Deferred to future**: `triggers`, `supercedes`, `replies_to`, `mentions`, `derived_from`, `contains` (Project System features)
- **Single table**: Use `relations` table for MVP (defer UniqueRelation/MultiRelation split)

### Delta Tracking
- **Granularity**: Field-level (one delta per field changed)
- **Storage**: Database table + JSON files in Soil
- **Timing**: After database commit (transactional consistency)
- **Format**: JSON with metadata (id, entity_type, entity_id, field, old_value, new_value, rationale, author, timestamp)

### Deferred Features (Post-MVP)
- Fragment system (Project System feature)
- ConversationLog/Frame/Stack (Project System features)
- UniqueRelation vs MultiRelation split
- Fossilization (Soil compaction)
- Extension archival (soil/core-migration/extensions/)
- Tool call tracking

---

**Guidelines**: Omit technical details (those belong in architecture.md or skills). Always update this file after completion of each task.
