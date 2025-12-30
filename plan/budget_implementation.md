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

### ~~Step 3: Soil MVP Foundation~~ ~~🔄 IN PLANNING~~

**REMOVED**: Not needed for Budget MVP.

**Rationale:**
- Schema is tentative and will see drastic changes
- No value in archiving schema this early
- Budget app is simple enough that schema snapshots aren't needed yet
- Soil (schema snapshots, Item archival) will be implemented when agent workflows are added

**Future Consideration**: Soil will be implemented when we add:
- Email parsing and archival
- Statement reconciliation
- Document linking (Relations)
- Agent-assisted workflows

For now, Budget app manages schema migrations manually without archival.

---

### Step 4: Advanced Core Features 🔄 IN PLANNING

**Objective:** Implement recurrences for Budget app.

**Note:**
- **Relations** are NOT part of Budget MVP (deferred to future agent workflows)
- **Deltas** are NOT part of Budget MVP (deferred to future when Soil integration needed)
- Recurrences are user-managed, not agent-driven

**Components:**

#### 4.1 Recurrences (Entity-based)
- Create `recurrences` table (Entity type)
- iCal rrule parsing library integration
- Recurrence template → transaction generation
- CRUD endpoints for recurrences
- UI in Budget app for managing recurring transactions

**Schema:**
```sql
CREATE TABLE recurrences (
    uuid TEXT PRIMARY KEY,         -- References entity.uuid
    rrule TEXT NOT NULL,           -- iCal rrule string
    entities TEXT NOT NULL,        -- JSON: transaction templates
    valid_from TEXT NOT NULL,
    valid_until TEXT,

    FOREIGN KEY (uuid) REFERENCES entity(uuid) ON DELETE CASCADE
);
```

**Note:** Recurrences are Entities (mutable, in Core), not Items.

#### ~~4.2 Relations~~ ~~4.3 Deltas~~ ~~4.4 Reference Resolution~~

**NOT PART OF BUDGET MVP** - These features require:
- Email parsing and triage
- Agent-assisted classification and extraction
- Statement reconciliation workflows
- Document linking to transactions

These will be considered in future iterations after Budget MVP is complete.

**Deliverables:**
- Recurrence system with iCal compatibility
- CRUD API endpoints for recurrences
- Budget app UI for managing recurring transactions

---

### Step 5: Flutter App Foundation

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

### Step 6: Budget App Features

**Objective:** Complete Budget app with spending review and management features.

**Components:**

#### 6.1 Spending Review
- Daily spending view (list grouped by date)
- Monthly summary with category breakdown
- Yearly overview with trends
- Charts/visualizations (optional, defer if complex)

#### 6.2 Account & Category Management
- Account selection during transaction creation
- Category picker with icons
- Manage accounts (create, edit, delete)
- Manage categories (create, edit, delete)

#### 6.3 Transaction Management
- Edit transaction screen
- Delete transaction with confirmation
- Transaction detail view
- Search/filter transactions

#### 6.4 Recurring Transactions UI
- Create recurring transaction template
- View upcoming recurring transactions
- Mark occurrence as completed/skipped

**Deliverables:**
- Complete spending review interface
- Account and category management
- Full transaction CRUD in UI
- Recurring transaction interface

---

### Step 7: Agent Integration & Deployment

**Objective:** Enable agent workflows and prepare for production deployment.

**Components:**

#### 7.1 Agent Workflows
- Statement reconciliation endpoint
- Email parsing integration (with Soil)
- Transaction suggestion API
- Bulk operations for agents
- Reconciliation status tracking

#### 7.2 Testing & CI/CD
- Integration tests for full workflows
- E2E tests for critical paths
- GitHub Actions for CI
- Automated testing on PR

#### 7.3 Deployment
- Docker configuration for Core API
- Docker Compose for local full-stack
- Railway deployment configuration
- Raspberry Pi deployment guide
- Environment variable management
- Database backup strategy

#### 7.4 Documentation
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

### Current Step Critical Files (Steps 3-4 Planning)
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

**Currently Planning:** Advanced Core Features (Step 4)

**Next:**
- ~~**Step 3** (Soil MVP Foundation)~~ - REMOVED (not needed for Budget)
- **Step 4** (Advanced Core Features) - Recurrences only (Relations/Deltas deferred)
- **Step 5** (Flutter App Foundation) - Budget app UI and API integration

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

**Step 3 (Soil)** was removed from Budget MVP:
- Schema is tentative and will see drastic changes
- No value in archiving schema this early
- Will be implemented when agent workflows are added

**Step 4 (Advanced Core Features - Recurrences)** comes now because:
- User needs recurring transaction management in Budget app
- Recurrences are Entities (no Item refactor needed)
- Relations and Deltas deferred to future agent workflows

**Step 5-6 (Flutter)** come after stable API because:
- Need stable API contract first
- Backend can be tested independently
- Reduces rework from API changes

**Step 7 (Agents & Deployment)** last because:
- Most complex workflows
- Depends on all core features
- Can defer without blocking user value

---

## Platform Foundation Decisions

The following design decisions clarify the Budget MVP scope:

### Soil (Removed from Budget MVP)
- **Decision**: Soil (schema snapshots, Item archival) NOT included in Budget MVP
- **Rationale**: Schema is tentative and will see drastic changes; no value in archiving this early
- **Future**: Soil will be implemented when agent workflows are added (email parsing, statement reconciliation)

### Entity vs Item Architecture
- **Entities** (Budget app): Mutable shared beliefs in Core (transactions, recurrences, users)
- **Items** (future): Immutable artifacts in Soil (emails, PDFs, statements)
- **No Item migration**: Budget app uses Entity model only
- **Future bridge**: Agents will create Entities based on Items (email → transaction)
- **UUID prefixes**: `entity_` for Entities, `item_` for Items (separate databases, no collision risk)

### Relation Types
- **NOT part of Budget MVP**: Relations are backend agent feature, not managed through Budget app
- **Backend scope**: Document linking (invoices/receipts → transactions) happens via agents
- **Deferred to future**: `triggers`, `supercedes`, `replies_to`, `mentions`, `derived_from`, `contains` (Project System features)

### Delta Tracking
- **NOT part of Budget MVP**: No delta archival to Soil needed
- **Deferred to future**: When audit trail/history reconstruction features needed

### Deferred Features (Post-Budget MVP)
- Fragment system (Project System feature)
- ConversationLog/Frame/Stack (Project System features)
- UniqueRelation vs MultiRelation split (Project System features)
- ToolCall items (Project System feature)
- ArtifactDelta (Project System feature)
- Soil implementation (schema snapshots, Item archival)
- Email/PDF archival (agent workflow feature)

---

**Guidelines**: Omit technical details (those belong in architecture.md or skills). Always update this file after completion of each task.
