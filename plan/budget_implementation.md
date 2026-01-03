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
- Budget: https://github.com/memogarden/app-budget

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

### Step 4: Recurrences ✅ COMPLETE (2025-12-30)

**Objective:** Implement recurrences for Budget app.

**Note:**
- **Relations** are NOT part of Budget MVP (deferred to future agent workflows)
- **Deltas** are NOT part of Budget MVP (deferred to future when Soil integration needed)
- Recurrences are user-managed, not agent-driven

**Dependencies:**
- `python-dateutil` - iCal RFC 5545 RRULE parsing
- All datetime/recurrence logic confined to `memogarden_core/utils/recurrence.py`

#### Completed Substeps:
- ✅ **4.1** - Recurrence Utils Module (memogarden_core/utils/recurrence.py)
- ✅ **4.2** - Database Schema (recurrences table, migration)
- ✅ **4.3** - Pydantic Schemas (RecurrenceCreate, RecurrenceUpdate, RecurrenceResponse)
- ✅ **4.4** - Core API Operations (db/recurrence.py - RecurrenceOperations)
- ✅ **4.5** - API Endpoints (api/v1/recurrences.py - CRUD endpoints)
- ✅ **4.6** - Testing (19 recurrence tests, all passing)

**Deliverables:**
- Recurrence system with iCal RFC 5545 RRULE compatibility
- CRUD API endpoints for recurrences
- `utils/recurrence.py` module with all datetime/recurrence logic
- `python-dateutil` dependency confined to recurrence utils module
- Database migration (20251229 → 20251230)
- 415 total tests passing (396 original + 19 new)

**API Endpoints:**
- POST /api/v1/recurrences - Create recurrence
- GET /api/v1/recurrences - List recurrences with filtering
- GET /api/v1/recurrences/{id} - Get single recurrence
- PUT /api/v1/recurrences/{id} - Update recurrence
- DELETE /api/v1/recurrences/{id} - Delete recurrence (soft delete via superseding)

**Schema:**
```sql
CREATE TABLE recurrences (
    id TEXT PRIMARY KEY,           -- References entity(id)
    rrule TEXT NOT NULL,           -- iCal rrule string
    entities TEXT NOT NULL,        -- JSON: transaction templates
    valid_from TEXT NOT NULL,      -- ISO 8601 datetime (start of recurrence window)
    valid_until TEXT,              -- ISO 8601 datetime (end of recurrence window, NULL = forever)

    FOREIGN KEY (id) REFERENCES entity(id) ON DELETE CASCADE
);
```

**Note:** Recurrences are Entities (mutable, in Core), not Items.

#### ~~4.3 Relations~~ ~~4.4 Deltas~~ ~~4.5 Reference Resolution~~

**NOT PART OF BUDGET MVP** - These features require:
- Email parsing and triage
- Agent-assisted classification and extraction
- Statement reconciliation workflows
- Document linking to transactions

These will be considered in future iterations after Budget MVP is complete.

---

### Step 5: Flutter App Foundation 🔄 IN PROGRESS (2025-12-31)

**Objective:** Build Budget app with local-first SQLite architecture and simple state management.

**Approach:** Learning-focused substeps (user is new to Flutter/Dart)
- **Interactive development**: User runs commands and adds code based on AI guidance
- **UI-first**: Build screens incrementally with visual feedback
- **Small reviewable steps**: Each substep is reviewed before proceeding
- **Context-friendly**: Break down to avoid context window limits

**Architecture Decisions:**
- **Local DB first**: SQLite with integer PK, extension pattern for MemoGarden sync
- **Simple state**: `setState()` (no Riverpod/Provider complexity for now)
- **Repository layer**: Business logic between widgets and DB
- **Local-first, sync-optional**: Works offline without MemoGarden; sync is add-on
- **No API calls in Phase 1**: DB-only, API client added in Phase 2
- **Hybrid schema**: Core columns + `extension` (JSON) + `metadata` (JSON)
- **Recurrences as first-class**: Built from start with RRULE validation

**Database Design Principles:**
1. **Integer PK** for performance (local use)
2. **MemoGarden UUID in extension** (not top-level column)
3. **Hash-based sync** (via `extension.memogarden.last_sync_hash`)
4. **Recurrence realization** (generated transactions pending until user confirms)

**Dependencies (pubspec.yaml):**
- `sqflite: ^2.4.2` - SQLite database
- `path: ^1.9.1` - File path manipulation
- `shared_preferences: ^2.5.4` - Local storage (auth tokens)
- `rrule: ^0.2.0` - iCal RRULE validation (client-side)

**Repository:** https://github.com/memogarden/app-budget

---

#### Substeps (Learning-Focused Breakdown)

**5.1: Project Initialization & Setup** ✅ COMPLETE
- Initialize Flutter project in `app-budget/`
- Configure `pubspec.yaml` (sqflite, path, shared_preferences, rrule)
- Run baseline app (Flutter counter demo)
- Verify web target works (Chrome)
- **Goal**: Empty Flutter project running

**5.2: Database Schema Setup** ✅ COMPLETE (2025-12-31)
- Create `database/database_helper.dart` ✅
- Define SQLite schema:
  - `transactions` table (with extension, metadata) ✅
  - `recurrences` table (with RRULE, template, occurrence tracking) ✅
- Implement `onCreate` migration ✅
- Add web support via `sqflite_common_ffi_web` ✅
- Test database initialization ✅
- **Goal**: Database ready, empty tables created ✅

**Deliverables:**
- `DatabaseHelper` singleton with cross-platform support (web + native)
- `transactions` table: id, date, amount, description, account, category, labels, extension, metadata
- `recurrences` table: id, rrule, template, valid_from, valid_until, last_generated, next_occurrence, extension, metadata
- Extension-ready schema (JSON columns for future extensibility)
- Successfully tested on Chrome/web platform

**5.3: Data Models** ✅ COMPLETE (2025-12-31)
- Create `models/transaction.dart` (plain data class) ✅
- Create `models/recurrence.dart` ✅
- Implement `fromMap()` and `toMap()` methods ✅
- Handle JSON encoding/decoding for extensionData and metadata ✅
- **Goal**: Data structures matching local schema ✅

**Deliverables:**
- `Transaction` data class with SQLite serialization
  - Fields: id, date, amount, description, account, category, labels, extensionData, metadata
  - `fromMap()` factory constructor for database rows → model
  - `toMap()` method for model → database rows
- `Recurrence` data class with SQLite serialization
  - Fields: id, rrule, template, valid_from, valid_until, last_generated, next_occurrence, extensionData, metadata
  - Same serialization pattern as Transaction
- JSON encoding/decoding for extensionData and metadata fields
- Renamed `extension` → `extensionData` (Dart keyword conflict)

**5.4: Repository Layer** ✅ COMPLETE (2026-01-02)
- Create `repositories/transaction_repository.dart` ✅
- Create `repositories/recurrence_repository.dart` ✅
- Implement CRUD methods (create, getAll, getById, update, delete) ✅
- Use raw SQL queries via `sqflite` ✅
- Implement transaction realization logic (deferred to UI implementation)
- **Goal**: Business logic layer ready ✅

**Deliverables:**
- `TransactionRepository` with full CRUD operations
- `RecurrenceRepository` with full CRUD operations
- Table name constants to avoid magic strings
- Input validation (null ID checks for create/update)
- Parameterized queries for SQL injection prevention

**5.5: Transaction Capture Screen (Static UI)** ✅ COMPLETE (2026-01-02)
- Build main transaction capture UI (Monefy-inspired)
- Big amount display, number pad (0-9, decimal, backspace)
- Date display (static for now, date selector added later)
- Account/category selector dropdowns (use placeholder values)
  - Future: Settings screen for adding/removing accounts & categories
- Save button only (autosave UX: back/close implies cancel)
- Placeholder spot for future recurrence button
- **No state yet** - just static layout
- **Goal**: See what the app will look like

**5.6: Add State to Capture Screen**
- Make number pad buttons work
- Update amount display in real-time
- Select account/category (simple dropdown or buttons)
- **Goal**: Interactive UI, but no data persistence

**5.7: Wire Up Data Flow** ✅ COMPLETE (2026-01-03)
- Connect capture screen to repository
- Save transactions to DB on submit
- Navigate away after save (better UX than clearing form)
- **Goal**: Capture screen actually saves data ✅

**Completed Substeps:**
- ✅ Import Transaction model and TransactionRepository
- ✅ Instantiate repository in screen state
- ✅ Implement `_isFormValid()` for validation (prevents zero-amount transactions)
- ✅ Implement `_saveTransaction()` with error handling and async/await
- ✅ Wire save button to validation + save method
- ✅ Navigate away on successful save
- ✅ Add backspace button to amount display with proper positioning
- ✅ Fix Transaction and Recurrence model constructor syntax

**5.8: Transaction List Screen** 🔄 UI COMPLETE (2026-01-02, commit: b5bf609)
- Build list UI to show saved transactions
- Pull from DB via repository
- Display generated transactions differently (italic/grey/bold)
- **Layout Requirements:**
  - Left sidebar (Drawer) with:
    - Account filter: All / Household / Personal
    - Date range selector: Day / Month / Year
    - Auto-hide with hamburger icon
  - Settings icon in app bar overflow menu (three dots)
  - Floating Action Button (FAB) to add transactions
- **Transaction List Grouping:**
  - Group transactions by category
  - Sort categories by total amount (descending)
  - Sort transactions within category by date ascending
  - Category headers show: name + emoji, total amount, % of period
  - Transaction items show: emoji icon, description, account•date, amount (red/green)
- **Completed** (UI Phase):
  - Collapsible category sections with state management
  - Category headers with expand/collapse icons
  - Drawer with filters (Material Design compliant)
  - Sample data display (Food, Transport, Income categories)
- **Pending** (Data Phase):
  - Connect to repository to pull real transactions
  - Apply account and date range filters
  - Calculate category totals and percentages dynamically
- **Goal**: See what you captured with proper grouping and sorting

**5.9: Recurrence Management**
- Create recurrence CRUD UI
- Validate RRULE syntax (client-side via `rrule` package)
- Generate transactions from recurrence template
- Implement realization flow (tap button or edit)
- **Goal**: Recurring transactions work

**5.10: Navigation Structure** 🔄 SCREENS CONNECTED (2026-01-02, commit: b5bf609)
- Add navigation (capture ↔ list ↔ settings)
- Bottom navigation bar or simple drawer
- **Completed**:
  - FAB on transaction list screen → capture screen
  - Overflow menu on transaction list screen → settings screen
  - Automatic back navigation on all screens via AppBar
  - MaterialPageRoute transitions between screens
- **Pending**:
  - Recurrence management navigation (when Step 5.9 is complete)
- **Goal**: Can move between screens

**5.11: Design System Polish**
- Define app colors (primary, secondary, background)
- Typography (font sizes, weights)
- Consistent button styles
- Make it look professional
- **Goal**: Polished MVP foundation

**5.12: Testing & Refinement**
- Test on web (chrome)
- Fix bugs, refine UX
- Test recurrence generation and realization
- **Goal**: Stable MVP foundation ready for features

---

#### Progress Tracking

- ✅ **5.1** - Project Initialization & Setup
- ✅ **5.2** - Database Schema Setup
- ✅ **5.3** - Data Models (2025-12-31)
- ✅ **5.4** - Repository Layer (2026-01-02)
- ✅ **5.5** - Transaction Capture Screen (Static UI) (2026-01-02)
- ✅ **5.6** - Add State to Capture Screen (2026-01-02)
- ✅ **5.7** - Wire Up Data Flow (2026-01-03)
- 🔄 **5.8** - Transaction List Screen (UI complete, data connection pending)
- ⏳ **5.9** - Recurrence Management
- 🔄 **5.10** - Navigation Structure (screens connected, navigation flow established)
- ⏳ **5.11** - Design System Polish
- ⏳ **5.12** - Testing & Refinement

---

#### Dependencies (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter

  # Database
  sqflite: ^2.4.2
  path: ^1.9.1
  sqflite_common_ffi_web: ^1.1.0  # Web SQLite support

  # Local storage (for auth tokens)
  shared_preferences: ^2.5.4

  # Recurrence support (iCal RRULE)
  rrule: ^0.2.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^6.0.0
```

**Notes:**
- `sqflite_common_ffi_web` enables SQLite on web platform (IndexedDB-based)
- No `uuid` package needed (UUIDs come from MemoGarden server, or use integer PK locally)
- `rrule` package validates iCal RRULE syntax client-side (enables local-only usage)

---

#### Tech Stack Notes

**Why this approach:**
1. **UI first** - Visual feedback early (motivating for learning)
2. **DB-first** - Local SQLite makes app fast and responsive
3. **Simple state** - `setState()` is built into Flutter, no new concepts
4. **Repository layer** - Makes adding sync easier later
5. **No Riverpod yet** - Add only if complexity grows
6. **Integer PK locally** - Performance for local queries, UUID in extension for sync
7. **Extension pattern** - Avoid schema migrations, add MemoGarden data via JSON
8. **Recurrences first-class** - Built from start, not added as afterthought

**Phase 2 (Future - Sync):**
- Add HTTP client (`http` package)
- Create sync service (background DB ↔ API)
- Implement hash-based conflict detection (via `extension.memogarden.last_sync_hash`)
- Repositories gain dual-write capability (DB + API)
- Widgets unchanged - still talk to repositories
- User resolves conflicts (merge, discard local, discard server)

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

**Step 4 COMPLETE** ✅ (Recurrences - 2025-12-30)
- 4.1: Recurrence Utils Module ✅
- 4.2: Database Schema ✅
- 4.3: Pydantic Schemas ✅
- 4.4: Core API Operations ✅
- 4.5: API Endpoints ✅
- 4.6: Testing ✅

**Next:**
- ~~**Step 3** (Soil MVP Foundation)~~ - REMOVED (not needed for Budget)
- **Step 5** (Flutter App Foundation) - Budget app UI and API integration
- **Step 6** (Budget App Features) - Spending review, account/category management, recurring transactions UI

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

**Step 4 (Recurrences)** came before Flutter because:
- User needs recurring transaction management in Budget app
- Recurrences are Entities (no Item refactor needed)
- Backend recurrence system enables Budget app UI
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

#### Technical Improvements
- **Replace Pydantic with dataclasses** (Post-Budget MVP)
  - **Rationale**:
    - Reduce memory footprint (3.3 MB runtime, 440 bytes/object)
    - Faster validation (24% faster with manual validation)
    - Model consolidation: 1 dataclass vs 4 Pydantic classes per entity
    - Easier customization (response-only fields, computed properties)
    - Stdlib only (simpler deployment, fewer dependencies)
  - **Performance impact**:
    - Pydantic: 1.90 μs/validation
    - Dataclass + manual validation: 1.53 μs/validation
    - At 1000 req/s: Pydantic adds 0.37ms total overhead (negligible)
  - **Memory impact**:
    - Current: 58.6 MB for 100K Pydantic objects
    - Dataclass: 15.6 MB for 100K objects (440 bytes/object savings)
  - **Migration strategy**:
    - Phase 1: Add `validate()` classmethod to each schema
    - Phase 2: Convert Pydantic models to dataclasses with factory methods
    - Phase 3: Update `@validate_request` decorator to use dataclass validation
    - Phase 4: Replace `model_dump(exclude_unset=True)` with helper function
      - Current usage in update endpoints: `data.model_dump(exclude_unset=True)`
      - Dataclass alternative: Custom helper or manual dict comprehension
    - Phase 5: Remove Pydantic dependency
    - **Zero endpoint changes needed** (abstraction boundary at `@validate_request`)
  - **Design principle**: Keep Pydantic-specific methods out of endpoints
    - Avoid: `.model_dump()`, `.model_dump_json()`, `.dict()`, `.json()`
    - Use: Direct field access (`data.amount`, `data.description`)

#### Functional Features
- Fragment system (Project System feature)
- ConversationLog/Frame/Stack (Project System features)
- UniqueRelation vs MultiRelation split (Project System features)
- ToolCall items (Project System feature)
- ArtifactDelta (Project System feature)
- Soil implementation (schema snapshots, Item archival)
- Email/PDF archival (agent workflow feature)

---

**Guidelines**: Omit technical details (those belong in architecture.md or skills). Always update this file after completion of each task.
