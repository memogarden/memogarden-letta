# MemoGarden Implementation Plan

**Version:** 1.0
**Status:** Active Development
**Created:** 2026-02-07
**Supersedes:** rfc-004-implementation-plan.md

## Executive Summary

This document consolidates all implementation planning for MemoGarden across multiple codebases:
- **memogarden-system** - Core system library (Soil + Core)
- **memogarden-api** - Flask REST + Semantic API server
- **memogarden-sdk** - Client SDKs for apps (future)
- **providers/** - Data import providers (future)

**Approach:** This plan identifies gaps between current PRD/RFC specifications and existing implementations, organized by priority and dependency.

**Current Compliance:** ~45% of PRD v0.11.1 requirements implemented (Session 10 complete)

**Document Structure:**
- **Completed Work (Sessions 1-6.5):** Summary format with key deliverables, test counts, and file references. Technical implementation details are in module docstrings and git commit history.
- **Implementation Gaps:** Detailed task lists for remaining work (Priority 1-4)
- **Future Sessions (7-13):** Full implementation details for upcoming work
- **Testing Gaps & Invariants:** Reference materials for development

---

## Table of Contents

1. [Implementation Status Summary](#implementation-status-summary)
2. [Completed Work](#completed-work)
3. [Implementation Gaps](#implementation-gaps)
4. [Testing Gaps](#testing-gaps)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Open Questions](#open-questions)

---

## Implementation Status Summary

### By Component

| Component | Status | Coverage | Notes |
|-----------|--------|----------|-------|
| **Soil Storage** | ✅ Implemented | 80% | Item CRUD, SystemRelation working. Missing: fossilization, fidelity management |
| **Core Storage** | ✅ Implemented | 70% | Entity registry, Transaction/Recurrence CRUD. Missing: user relations, context tracking |
| **Authentication** | ✅ Implemented | 95% | JWT + API key auth complete. Missing: permissions enforcement |
| **REST API** | ⚠️ Partial | 50% | Entity CRUD for Transaction/Recurrence only. **Note:** REST API is Entity-only for external CRUD apps. Full MemoGarden capabilities (Facts, Relations, Context) accessed via Semantic API. |
| **Semantic API** | ⚠️ Partial | 50% | Core bundle complete (5 verbs). Soil bundle complete (4 verbs). Relations/Context/Search bundles missing. |
| **Context Mechanism** | ❌ Not Implemented | 0% | RFC-003: ContextFrame, View stream, enter/leave/focus/rejoin |
| **Fossilization** | ❌ Not Implemented | 0% | RFC-002: Time horizon decay, item compression |
| **Relations API** | ❌ Not Implemented | 5% | Schema exists, no operations |
| **Provider Plugins** | ⚠️ Partial | 30% | Email importer skeleton exists |
| **App Framework** | ❌ Not Implemented | 0% | RFC-009: App model, IPC, SDKs |

### By RFC

| RFC | Title | Status | Notes |
|-----|-------|--------|-------|
| **RFC-001 v4** | Security Operations | ⚠️ 60% | Encryption defined but not implemented. Auth complete. |
| **RFC-002 v5** | Relations & Fossilization | ⚠️ 20% | Schema exists. No time horizon logic, no fossilization engine. |
| **RFC-003 v4** | Context Mechanism | ⚠️ 70% | Session 4-5 complete. Missing: rejoin, capture decorator, fork/merge. |
| **RFC-004 v2** | Package Deployment | ⚠️ 50% | Structure correct. Missing: get_db_path(), schema bundling. |
| **RFC-005 v7.1** | API Design | ⚠️ 60% | Sessions 1-2 complete. Missing: track, explore, enhanced query filters, rejoin. |
| **RFC-006 v1** | Error Handling | ✅ 80% | Exception hierarchy complete. Diagnostics tools missing. |
| **RFC-007 v2** | Runtime Operations | ❌ 0% | No system agent, no background tasks. |
| **RFC-008 v1.2** | Transaction Semantics | ✅ 90% | Session 6.5 aligned. Missing: recovery tools, startup checks. |
| **RFC-009 v1** | App Model | ❌ 0% | No IPC, no SDKs, no app registry. |

---

## Completed Work Summary

| Component | Session | Tests | Status | Key Features |
|-----------|---------|-------|--------|--------------|
| **Core Schema** | - | - | ✅ Complete | Soil/Core SQL schemas, hash chain fields, indexes |
| **Type Schemas** | - | - | ✅ Complete | 7 Item types (email, note, etc.), 6 Entity types |
| **memogarden-system** | - | - | ✅ Complete | Soil/Core operations, utilities, host interface, exceptions |
| **REST API** | - | 41 | ✅ Complete | Transaction/Recurrence CRUD endpoints, authentication |
| **Semantic API - Core** | 1 | 22 | ✅ Complete | create, get, edit, forget, query verbs |
| **Semantic API - Soil** | 2 | 15 | ✅ Complete | add, amend, get, query verbs for facts |
| **User Relations** | 3 | 25 | ✅ Complete | Time horizon decay, link verb, relation queries |
| **Context Framework** | 4 | 26 | ✅ Complete | ContextFrame, View stream, LRU-N eviction |
| **Context Verbs** | 5 | 48 | ✅ Complete | enter/leave/focus scope, context capture |
| **Audit Facts** | 6 | 8 | ✅ Complete | Action/ActionResult trails, audit decorator |
| **Connection Refactor** | 6.5 | 159 | ✅ Complete | Context manager enforcement, atomic transactions |
| **ActionResult Schema** | 6.6 | 167 | ✅ Complete | Structured error capture (code, message, details) |
| **Relations Bundle** | 7 | 185 | ✅ Complete | unlink, edit_relation, get_relation, query_relation, explore verbs |
| **Code Review Fixes** | 7.5 | 185 | ✅ Complete | Fixed architectural violations, added public APIs |
| **Track Verb** | 8 | 192 | ✅ Complete | Causal chain tracing, derived_from links, depth limits |
| **Search Verb** | 9 | 200 | ✅ Complete | Fuzzy text search, coverage levels, effort modes |
| **Code Review Fixes** | 9.1 | 200 | ✅ Complete | Fixed architectural violations, added public APIs |
| **Config-Based Path Resolution** | 10 | 215 | ✅ Complete | RFC-004 environment variable support |
| **Schema Access Utilities** | 11 | 19 | ✅ Complete | RFC-004 schema bundling and runtime access |

**Total:** 234 tests passing (215 API + 19 system)

**Implementation Details:** See individual session summaries below and git commit history

---

## Implementation Gaps

### 🔴 Priority 1: Core Platform Features

#### 1.1 Semantic API (RFC-005 v7)

**Status:** ⚠️ Partial (Session 1 Complete - Core Bundle)

**Completed (Session 1):**

1. **`/mg` Endpoint** ✅
   - [x] Request envelope parsing (op, params)
   - [x] Response envelope (ok, actor, timestamp, result/error)
   - [x] Actor tracking (user vs agent)
   - [x] Authentication middleware for all requests

2. **Core Bundle Verbs:** ✅
   - [x] `create` - Create entity (baseline types)
   - [x] `edit` - Edit entity (set/unset semantics)
   - [x] `forget` - Soft delete entity
   - [x] `get` - Get entity by UUID
   - [x] `query` - Query with basic filters and pagination
   - [ ] `register` - Register custom schema (DEFERRED)

**Remaining Work:**

3. **Soil Bundle Verbs:**
   - [ ] `add` - Add fact (bring external data into MemoGarden)
   - [ ] `amend` - Amend fact (create superseding fact)
   - [ ] `get` - Get fact by UUID
   - [ ] `query` - Query facts with filters

4. **Relations Bundle Verbs:**
   - [ ] `link` - Create user relation (with time_horizon)
   - [ ] `unlink` - Remove relation
   - [ ] `edit` - Edit relation attributes
   - [ ] `get` - Get relation by UUID
   - [ ] `query` - Query relations
   - [ ] `explore` - Graph expansion from anchor

5. **Semantic Bundle Verbs:**
   - [ ] `search` - Semantic search (content-based, fuzzy, or auto)

6. **Context Bundle Verbs** (Core, per RFC-003):
   - [ ] `enter` - Add scope to active set
   - [ ] `leave` - Remove scope from active set
   - [ ] `focus` - Switch primary scope
   - [ ] `rejoin` - Merge subordinate context

**Files Created:**
- [x] `/memogarden-api/api/semantic.py` - Semantic API dispatcher
- [x] `/memogarden-api/api/handlers/core.py` - Core verb handlers
- [x] `/memogarden-api/api/schemas/semantic.py` - Pydantic schemas
- [x] `/memogarden-api/tests/test_semantic_api.py` - 22 tests, all passing

**Files to Create:**
- [ ] `/memogarden-api/api/handlers/soil.py` - Soil verb handlers
- [ ] `/memogarden-api/api/handlers/relations.py` - Relation verb handlers
- [ ] `/memogarden-api/api/handlers/semantic.py` - Search verb handler
- [ ] `/memogarden-api/api/handlers/context.py` - Context verb handlers

**Dependencies:** None (Core bundle complete, Soil bundle next)

#### 1.2 Audit Facts (RFC-005 v7 Section 7)

**Status:** ❌ Not Implemented

**Required Components:**

1. **Action Fact Schema:**
   - [ ] Add `Action` type to `/schemas/types/items/action.schema.json`
   - [ ] Fields: uuid, type, actor, operation, params, context, timestamp, request_id, parent_action

2. **ActionResult Fact Schema:**
   - [ ] Add `ActionResult` type to item schemas
   - [ ] Fields: uuid, type, result, error, result_summary, timestamp, duration_ms

3. **System Relation:**
   - [ ] Add `result_of` to SYSTEM_RELATION_KINDS
   - [ ] Create relation linking ActionResult → Action

4. **Automatic Creation:**
   - [ ] Decorator/wrapper for all Semantic API operations
   - [ ] Create Action fact on operation start
   - [ ] Create ActionResult fact on operation completion
   - [ ] Link via `result_of` relation
   - [ ] Use `bypass_semantic_api=True` to prevent recursion

5. **Fossilization Policy:**
   - [ ] High-frequency operations (search): +7d retention
   - [ ] Mutations (edits, adds): +30d retention
   - [ ] Security events (permission denials): +1y retention

**Dependencies:** Semantic API (1.1)

#### 1.3 User Relations (RFC-002 v5)

**Status:** ⚠️ Schema Exists, Operations Missing

**Required Components:**

1. **UserRelation Operations:**
   - [ ] Create `/memogarden-system/system/core/relation.py`
   - [ ] `create()` - Create user relation with initial time_horizon
   - [ ] `get_by_id()` - Retrieve relation
   - [ ] `list_inbound()` - Get relations targeting entity
   - [ ] `list_outbound()` - Get relations from entity
   - [ ] `update_time_horizon()` - Update on access (SAFETY_COEFFICIENT * delta)
   - [ ] `expire()` - Mark for fossilization

2. **Time Horizon Logic:**
   - [ ] `on_relation_access()` - Update time_horizon on access
   - [ ] `relation_is_alive()` - Check if time_horizon >= today
   - [ ] `fact_time_horizon()` - Compute from inbound user relations
   - [ ] Current day function: `(date - EPOCH_2020_01_01).days`

3. **Fact Significance Computation:**
   - [ ] Get max time_horizon from inbound user relations
   - [ ] Return None for orphaned facts

**Dependencies:** None (can start immediately)

#### 1.4 Context Mechanism (RFC-003 v4)

**Status:** ❌ Not Implemented (schema exists)

**Required Components:**

1. **ContextFrame Operations:**
   - [ ] Create `/memogarden-system/system/core/context.py`
   - [ ] `get_context_frame()` - Get by owner (user or scope)
   - [ ] `update_containers()` - LRU-N eviction on visit
   - [ ] `get_context()` - Return current containers list
   - [ ] `fork_context()` - Create subordinate context
   - [ ] `merge_context()` - Merge subordinate back to parent
   - [ ] `destroy_context()` - Delete subordinate ContextFrame

2. **View Operations:**
   - [ ] `create_view()` - Create new View with actions
   - [ ] `append_view()` - Append to ContextFrame's view timeline
   - [ ] `coalesce_view()` - End inactive View (timeout-based)

3. **Context Capture:**
   - [ ] Decorator for entity mutations
   - [ ] Capture ContextFrame.containers at mutation time
   - [ ] Store in EntityDelta.context or delta metadata

4. **Visit Tracking:**
   - [ ] Substantive vs primitive classification (hardcoded initially)
   - [ ] `visit_entity()` - Update containers on access
   - [ ] Type-based: Artifact, Note = substantive; Schema = primitive

5. **Scope Operations (Semantic API):**
   - [ ] `enter_scope()` - Add to active set
   - [ ] `leave_scope()` - Remove from active set
   - [ ] `focus_scope()` - Switch primary scope
   - [ ] `rejoin()` - Merge subordinate context

6. **Invariants to Implement:**
   - [ ] INV-1: Unique View UUID
   - [ ] INV-2: Synchronized Append (user + scope ContextFrames)
   - [ ] INV-3: Primary Context Capture
   - [ ] INV-4: Automatic Capture
   - [ ] INV-5: Fork Inheritance
   - [ ] INV-6: Merge Termination
   - [ ] INV-7: No Automatic Context Inheritance
   - [ ] INV-8: Stream Suspension on Leave
   - [ ] INV-9: Linked List Structure
   - [ ] INV-10: ViewMerge Structure
   - [ ] INV-11: Explicit Scope Control
   - [ ] INV-11a: Focus Separation
   - [ ] INV-11b: Implied Focus
   - [ ] INV-12: LRU-N Limit (N=7 initially)
   - [ ] INV-13: Tunable N
   - [ ] INV-14: Cross-Session Persistence
   - [ ] INV-15: Persistent Users Only
   - [ ] INV-16: Explicit Context Break
   - [ ] INV-17: Substantive vs Primitive Objects
   - [ ] INV-18: Type-Based Classification
   - [ ] INV-19: Hardcoded Initial Classification
   - [ ] INV-20: One Primary Context Per Owner
   - [ ] INV-21: Subordinate Context Ownership
   - [ ] INV-22: Action Grouping (coalescence)
   - [ ] INV-23: Coalescence Boundaries
   - [ ] INV-24: View Stream Compression
   - [ ] INV-25: Context Preservation in Deltas
   - [ ] INV-26: No Shared ContextFrame

**Dependencies:** User Relations (1.3) - for linking entities to context

#### 1.5 Fossilization Engine (RFC-002 v5)

**Status:** ❌ Not Implemented

**Required Components:**

1. **Fossilization Sweep:**
   - [ ] Create `/memogarden-system/system/soil/fossilization.py`
   - [ ] `fossilization_sweep()` - Daily background task
   - [ ] `query_fossilization_candidates()` - Find facts with expired time_horizon
   - [ ] `should_fossilize_item()` - Check if item should fossilize
   - [ ] `fossilize_item()` - Compress item to summary/stub
   - [ ] Metrics collection (SweepMetrics)

2. **Summary Generation:**
   - [ ] Extractive summary (sentence selection)
   - [ ] LLM-based summary (optional, configurable)
   - [ ] Summary length limits (configurable)

3. **Item Fidelity Management:**
   - [ ] `full` → `summary` - First fossilization
   - [ ] `summary` → `stub` - Second fossilization
   - [ ] `stub` → `tombstone` - Deletion under pressure
   - [ ] `fossilized_at` timestamp tracking

4. **Storage Pressure Handling:**
   - [ ] Eviction score computation
   - [ ] `delete_under_pressure()` - Free space when threshold exceeded
   - [ ] Degraded item warnings in API responses

5. **Relation Fossilization:**
   - [ ] Move expired user_relations from Core to Soil
   - [ ] Change UUID prefix from `core_` to `soil_`
   - [ ] Update `source_type`/`target_type` references

6. **Configuration:**
   - [ ] FossilizationConfig dataclass
   - [ ] `safety_coefficient` (default: 1.2)
   - [ ] `sweep_interval_hours` (default: 24)
   - [ ] `summary_method`, `summary_max_tokens`
   - [ ] `storage_pressure_threshold_pct`, `eviction_target_free_pct`

**Dependencies:** User Relations (1.3), Context Mechanism (1.4)

---

### 🟡 Priority 2: Platform Integration

#### 2.1 Schema Access Utilities (RFC-004 v2)

**Status:** ✅ Completed (Session 11)

**Completed Components:**

1. **`system.schemas` Module:**
   - [x] Create `/memogarden-system/system/schemas.py`
   - [x] `get_sql_schema(layer)` - Return soil.sql or core.sql content
   - [x] `get_type_schema(category, type_name)` - Return JSON schema
   - [x] `list_type_schemas(category)` - List available schemas

2. **Resource Bundling:**
   - [x] Bundle schemas in package (pyproject.toml configuration)
   - [x] Use importlib.resources for package access
   - [x] Fallback to file reading in development mode

3. **Update Init Logic:**
   - [x] Soil/Core use `get_sql_schema()` instead of hardcoded paths
   - [x] Remove hardcoded `../schemas/sql/` paths

**RFC-004 Invariants Enforced:**
- INV-PKG-004: Try importlib.resources first (bundled package)
- INV-PKG-005: Fall back to file reading (development mode)
- INV-PKG-006: Raise FileNotFoundError if schema not found in either location

**Dependencies:** None (standalone utility)

#### 2.2 Config-Based Path Resolution (RFC-004 v2)

**Status:** ✅ Completed (Session 10)

**Completed Components:**

1. **Environment Variable Support:**
   - [x] `MEMOGARDEN_SOIL_DB` - Explicit Soil database path
   - [x] `MEMOGARDEN_CORE_DB` - Explicit Core database path
   - [x] `MEMOGARDEN_DATA_DIR` - Shared data directory

2. **`get_db_path()` Function:**
   - [x] Add to `/memogarden-system/system/host/environment.py`
   - [x] Resolution order: env var → data dir → current directory
   - [x] Layer parameter: 'soil' or 'core'

3. **Update Soil/Core Initialization:**
   - [x] Default db_path to `None` in __init__
   - [x] Call `get_db_path()` when db_path is None
   - [x] Maintain backward compatibility (explicit paths still work)

**RFC-004 Invariants Enforced:**
- INV-PKG-001: Resolution order: layer-specific override → shared data dir → current dir
- INV-PKG-002: Backward compatible - explicit paths still work
- INV-PKG-003: Default paths: `./{layer}.db`

#### 2.3 REST API for Soil Items

**Status:** ❌ Not Implemented

**Required Components:**

1. **Item Endpoints:**
   - [ ] `POST /api/v1/items` - Add item
   - [ ] `GET /api/v1/items` - List with filters (_type, start, end, limit)
   - [ ] `GET /api/v1/items/{uuid}` - Get single item
   - [ ] `PUT /api/v1/items/{uuid}` - Amend (create superseding item)
   - [ ] `DELETE /api/v1/items/{uuid}` - Soft delete via supersession

2. **SystemRelation Endpoints:**
   - [ ] `POST /api/v1/relations` - Create system relation
   - [ ] `GET /api/v1/relations` - List with filters (source, kind, target)
   - [ ] `GET /api/v1/relations/{uuid}` - Get single relation

3. **Pydantic Schemas:**
   - [ ] `ItemCreate`, `ItemResponse`
   - [ ] `SystemRelationCreate`, `SystemRelationResponse`

**Dependencies:** Semantic API (1.1) - for pattern consistency

#### 2.4 REST API for Entities

**Status:** ⚠️ Partial (Transaction only)

**Required Components:**

1. **Generic Entity Endpoints:**
   - [ ] `POST /api/v1/entities` - Create entity (any type)
   - [ ] `GET /api/v1/entities` - List with filters (type, start, end)
   - [ ] `GET /api/v1/entities/{uuid}` - Get single entity
   - [ ] `PATCH /api/v1/entities/{uuid}` - Edit (set/unset semantics)
   - [ ] `DELETE /api/v1/entities/{uuid}` - Forget (soft delete)

2. **Type-Specific Endpoints:**
   - [ ] `POST /api/v1/artifacts` - Create artifact
   - [ ] `POST /api/v1/labels` - Create label
   - [ ] Generic CRUD for all entity types

**Dependencies:** Semantic API (1.1)

#### 2.5 Cross-Database Transaction Coordination (RFC-008 v1)

**Status:** ⚠️ Defined but Not Enforced

**Required Components:**

1. **Atomic Cross-DB Operations:**
   - [ ] `get_core(atomic=True)` context manager
   - [ ] Begin transaction on both Soil and Core
   - [ ] Commit both or rollback both
   - [ ] Handle failure modes

2. **Inconsistency Detection:**
   - [ ] Orphaned EntityDeltas (Soil committed, Core did not)
   - [ ] Broken entity hash chains
   - [ ] Dangling relation references

3. **Recovery Tools:**
   - [ ] `memogarden diagnose` - Report inconsistencies
   - [ ] `memogarden repair` - Automated repairs
   - [ ] Operator-in-the-loop resolution

4. **Failure Logging:**
   - [ ] Create SystemEvent on cross-DB failure
   - [ ] Mark system as INCONSISTENT state
   - [ ] Require manual intervention before continue

**Dependencies:** Semantic API (1.1), Audit Facts (1.2)

---

### 🟢 Priority 3: Advanced Features

#### 3.1 Search (Semantic Bundle)

**Status:** ❌ Not Implemented

**Required Components:**

1. **Search Strategies:**
   - [ ] Semantic - Embedding similarity (vector DB or external service)
   - [ ] Fuzzy - Text matching with typo tolerance
   - [ ] Auto - System chooses based on query

2. **Coverage Levels:**
   - [ ] Names - Title/name fields only (fast)
   - [ ] Content - Names + body text
   - [ ] Full - All indexed fields including metadata

3. **Effort Modes:**
   - [ ] Quick - Cached results, shallow index
   - [ ] Standard - Full search
   - [ ] Deep - Exhaustive search

4. **Continuation Tokens:**
   - [ ] Pagination for large result sets
   - [ ] Token-based resumption

5. **Configuration:**
   - [ ] SearchConfig dataclass
   - [ ] Default strategy, coverage, effort

**Dependencies:** Semantic API (1.1)

#### 3.2 Provider Plugin Interface

**Status:** ⚠️ Skeleton Only

**Required Components:**

1. **Provider Protocol:**
   - [ ] Define `Provider` Protocol class
   - [ ] `sync(since)` - Fetch facts from source
   - [ ] `create_relations(item)` - Create system relations

2. **Email Providers:**
   - [ ] Gmail provider (OAuth)
   - [ ] Outlook provider (OAuth)
   - [ ] mbox provider (local files)

3. **Provider Registry:**
   - [ ] Register installed providers
   - [ ] Discover providers by capability
   - [ ] Provider configuration management

**Dependencies:** Soil Items API (2.3)

#### 3.3 App Framework (RFC-009 v1)

**Status:** ❌ Not Implemented

**Required Components:**

1. **IPC Protocol:**
   - [ ] stdin/stdout JSON-lines protocol
   - [ ] Message types: request, response, notification, subscribe, shutdown
   - [ ] Process lifecycle management

2. **App Registry:**
   - [ ] `memogarden app install` - Register app
   - [ ] `memogarden app list` - List installed apps
   - [ ] `memogarden app load` - Launch app process
   - [ ] `memogarden app unload` - Terminate app

3. **App SDKs:**
   - [ ] Python SDK
   - [ ] TypeScript/JavaScript SDK
   - [ ] Dart SDK (Flutter)
   - [ ] Target Semantic API exclusively

4. **Capability Discovery:**
   - [ ] App manifest schema (YAML)
   - [ ] Toolcall definitions
   - [ ] Profile declarations (Core, Soil, Relational, Factual, Semantic)

5. **Standalone Backend:**
   - [ ] SQLiteBackend - Core bundle only
   - [ ] MemoryBackend - Testing
   - [ ] Capability querying

**Dependencies:** Semantic API (1.1), Search (3.1)

#### 3.4 Encryption at Rest (RFC-001 v4)

**Status:** ❌ Not Implemented

**Required Components:**

1. **SQLCipher Integration:**
   - [ ] Replace sqlite3 with pysqlcipher3
   - [ ] Encryption key derivation
   - [ ] Database encryption/decryption

2. **Key Management:**
   - [ ] Shamir's Secret Sharing
   - [ ] Hardware security module integration (optional)
   - [ ] Key recovery workflow

3. **Configuration:**
   - [ ] EncryptionConfig dataclass
   - [ ] `enabled` flag, algorithm selection

**Dependencies:** None (can start independently)

#### 3.5 System Agent (RFC-007 v2)

**Status:** ❌ Not Implemented

**Required Components:**

1. **Background Tasks:**
   - [ ] Fossilization sweeps (daily)
   - [ ] View coalescence (hourly)
   - [ ] Context GC (weekly)
   - [ ] Health monitoring

2. **Observability:**
   - [ ] SSD health monitoring (wear level, reallocated sectors)
   - [ ] Statistical Process Control (SPC) for metrics
   - [ ] SystemEvent creation for significant events

3. **Task Scheduler:**
   - [ ] Cron-like scheduling
   - [ ] Task history and logs
   - [ ] Failure recovery

**Dependencies:** Fossilization Engine (1.5), Context Mechanism (1.4)

---

### 🔵 Priority 4: Future Work

#### 4.1 SDKs for Multiple Languages

- [ ] Python SDK (Semantic API client)
- [ ] TypeScript/JavaScript SDK
- [ ] Dart SDK (Flutter apps)
- [ ] Java SDK (Android apps)

#### 4.2 Graph Visualization

- [ ] Relation graph rendering
- [ ] Force-directed layout
- [ ] Interactive exploration UI

#### 4.3 Advanced Context Features

- [ ] Automatic context inference (machine learning)
- [ ] Context templates (predefined patterns)
- [ ] Multi-device context sync

#### 4.4 Performance Optimization

- [ ] Query profiling and optimization
- [ ] Index tuning based on usage patterns
- [ ] Caching for frequently-accessed entities

---

## Testing Gaps

### By Feature Area

#### ✅ Well-Tested

- [x] Transaction CRUD (20 tests)
- [x] Recurrence CRUD (12 tests)
- [x] Authentication (9 tests)
- [x] Hash chain operations

#### ❌ Missing Tests

**Soil Layer:**
- [ ] Item CRUD operations
- [ ] SystemRelation CRUD operations
- [ ] Item integrity hash verification
- [ ] Fidelity state transitions
- [ ] Email threading (replies_to relations)

**Core Layer:**
- [ ] Generic Entity CRUD
- [ ] User Relation operations
- [ ] Time horizon computation
- [ ] ContextFrame operations
- [ ] View stream operations
- [ ] Optimistic locking conflicts

**Semantic API:**
- [ ] All 17 verbs
- [ ] Request/response envelope validation
- [ ] Actor tracking
- [ ] Error handling

**Context Mechanism:**
- [ ] All 26 invariants from RFC-003
- [ ] Fork/merge behavior
- [ ] LRU-N eviction
- [ ] Scope transitions
- [ ] Context capture on mutations

**Fossilization:**
- [ ] Time horizon decay
- [ ] Item compression
- [ ] Storage pressure eviction
- [ ] Relation fossilization
- [ ] Resurrection on access

**Cross-Database Coordination:**
- [ ] Atomic commits across Soil and Core
- [ ] Failure detection and rollback
- [ ] Orphaned EntityDelta detection
- [ ] Recovery procedures

**Integration Tests:**
- [ ] End-to-end workflows
- [ ] Multi-step operations
- [ ] Concurrent access patterns
- [ ] Error recovery scenarios

**Performance Tests:**
- [ ] Large dataset handling
- [ ] Query performance benchmarks
- [ ] Fossilization sweep efficiency
- [ ] Memory usage profiling

---

## Implementation Roadmap

**Design Principles:**

1. **Session-Sized Chunks:** Each session is completable in ~20k tokens (2-4 hours)
2. **Working State:** Every session leaves the system in a working, testable state
3. **Incremental Value:** Each session delivers usable functionality
4. **Test-Driven:** Tests written alongside implementation
5. **Documentation:** Code is documented as it's written

### Session Status

| Session | Name | Status | Date | Tests |
|---------|------|--------|------|-------|
| 1 | Semantic API - Core Bundle Verbs | ✅ Completed | 2026-02-07 | 22/22 passing |
| 2 | Semantic API - Soil Bundle Verbs | ✅ Completed | 2026-02-07 | 21/21 passing |
| 3 | User Relations | ✅ Completed | 2026-02-08 | 25/25 passing |
| 4 | Context Framework - Basic | ✅ Completed | 2026-02-08 | 26/26 passing |
| 5 | Context Verbs and Capture | ✅ Completed | 2026-02-08 | 48/48 passing |
| 6 | Audit Facts | ✅ Completed | 2026-02-08 | 8/8 passing |
| 6.5 | Connection Lifecycle Refactor | ✅ Completed | 2026-02-08 | 159/159 passing |
| 6.6 | ActionResult Schema Enhancement | ✅ Completed | 2026-02-09 | 167/167 passing |
| 7 | Relations Bundle Verbs | ✅ Completed | 2026-02-09 | 185/185 passing |
| 7.5 | Code Review Fixes | ✅ Completed | 2026-02-09 | 185/185 passing |
| 8 | Track Verb | ✅ Completed | 2026-02-09 | 192/192 passing |
| 9 | Search Verb | ✅ Completed | 2026-02-09 | 200/200 passing |
| 9.1 | Code Review Fixes | ✅ Completed | 2026-02-09 | 200/200 passing |
| 10 | Config-Based Path Resolution | ✅ Completed | 2026-02-09 | 215/215 passing |
| 11 | Schema Access Utilities | ✅ Completed | 2026-02-09 | 19/19 passing |
| 12 | REST API - Generic Entities | ⏳ Not Started | - | 0/0 |
| 13 | Cross-Database Transactions | ⏳ Not Started | - | 0/0 |
| 14 | Fossilization - Basic Sweep | ⏳ Not Started | - | 0/0 |

---

### ✅ Session 1: Semantic API - Core Bundle (Completed 2026-02-07)

**Tests:** 22/22 passing

**Deliverables:**
- `/mg` endpoint dispatcher with request/response envelope (ok, actor, timestamp, result/error)
- Core verbs: `create`, `get`, `edit`, `forget`, `query` for entities
- Authentication middleware for all Semantic API requests
- UUID prefix handling (accepts both prefixed and non-prefixed)
- Baseline entity type validation (Transaction, Recurrence, Artifact, Label, Operator, Agent, Entity)

**Key Files:**
- `api/semantic.py`, `api/handlers/core.py`, `api/schemas/semantic.py`
- `tests/test_semantic_api.py`

**Deferred:** `register` verb, full query DSL operators, domain-specific table updates

### ✅ Session 2: Semantic API - Soil Bundle (Completed 2026-02-07)

**Tests:** 15/15 passing (37 total: 22 Core + 15 Soil)

**Deliverables:**
- Soil verbs: `add` (bring external data in), `amend` (create superseding fact)
- Extended `query` to support fact queries (type, start, end, filters)
- `integrity_hash` computed on all fact creation
- `_type` validated against registered schemas

**Key Files:**
- `api/handlers/soil.py`, `api/schemas/semantic.py` (AddRequest, AmendRequest)

**RFC-002 Invariants:** Facts immutable, amend creates new fact with `supersedes` link

### ✅ Session 3: User Relations (Completed 2026-02-08)

**Tests:** 25/25 passing

**Deliverables:**
- `link` verb for creating user relations with time_horizon
- Relation operations: create, list_inbound/list_outbound, update_time_horizon, expire, fact_time_horizon, is_alive
- `time` utility module with current_day() and day_to_date()
- Fact significance computation from inbound relations

**Key Files:**
- `system/core/relation.py`, `system/utils/time.py`
- `tests/test_user_relations.py`

**RFC-002 Invariants:**
- `time_horizon += delta * SAFETY_COEFFICIENT` (1.2)
- `relation_is_alive()` ⇔ `time_horizon >= current_day()`
- Orphaned facts have None significance

### ✅ Session 4: Context Framework - Basic (Completed 2026-02-08)

**Tests:** 26/26 passing (132 total across all suites)

**Deliverables:**
- ContextFrame operations: get_context_frame, update_containers, create_view, append_view
- LRU-N eviction (N=7 initially)
- Substantive vs primitive type classification
- JSON schemas for View, ViewMerge, ContextFrame entity types

**Key Files:**
- `system/core/context.py`, `schemas/types/entities/view.schema.json`

**RFC-003 Invariants Enforced:**
- INV-1: Unique View UUID (core_ prefix)
- INV-12: LRU-N limit
- INV-17/18/19: Type-based classification
- INV-20: One ContextFrame per owner
- INV-26: No shared ContextFrame

**Known Limitations (fixed in Session 5):** view_timeline in-memory only

### ✅ Session 5: Context Verbs and Capture (Completed 2026-02-08)

**Tests:** 48/48 passing (151 total)

**Deliverables:**
- Context verbs: `enter_scope`, `leave_scope`, `focus_scope`
- `active_scopes` and `primary_scope` columns in context_frame table
- Migration 002: Added context scope columns
- Fixed database locking (in-memory database for tests)

**Key Files:**
- `api/handlers/core.py` (context verb handlers), `api/schemas/semantic.py`
- `tests/conftest.py` (in-memory database fix)

**RFC-003 Invariants Enforced:**
- INV-11/11a/11b: Explicit scope control, focus separation, implied focus
- INV-8: Stream suspension on leave
- INV-20: One ContextFrame per owner

**Deferred:** `rejoin` verb, context capture decorator, `visit_entity`, fork/merge logic

### ✅ Session 6: Audit Facts (Completed 2026-02-08)

**Tests:** 8/8 passing (159 total)

**Deliverables:**
- Action/ActionResult fact schemas in `schemas/types/items/`
- `@with_audit()` decorator for Semantic API operations
- `result_of` system relation (ActionResult → Action)
- `bypass_semantic_api` flag to prevent recursion
- Request ID correlation, duration tracking, error capture
- Migration 003: Added audit fact types

**Key Files:**
- `schemas/types/items/action.schema.json`, `schemas/types/items/actionresult.schema.json`
- `api/handlers/decorators.py`, `tests/test_audit_facts.py`

**RFC-005 v7 Invariants Enforced:**
- Action fact created on operation start
- ActionResult fact created on completion (success/failure)
- System relation links ActionResult → Action
- Unique request_id, duration tracking, error capture

---

### ✅ Session 6.5: Connection Lifecycle Refactor (Completed 2026-02-08)

**Tests:** 159/159 passing (all tests)

**Architectural Improvement:** Eliminated "autocommit lie", enforced context manager usage

**Deliverables:**
- Core/Soil MUST be used with `with` statement (runtime enforcement)
- Removed `atomic` parameter from `get_core()`
- Removed `@with_core_cleanup` and `@with_soil_cleanup` decorators
- All operations use context manager pattern: `with get_core() as core:`
- Enhanced ActionResult with error_type, error_traceback, error_context

**Key Files:**
- `system/core/__init__.py` - Core class with `_in_context` flag, `_get_conn()` enforcement
- `system/soil/database.py` - Soil class with same context manager pattern
- `api/handlers/*.py` - All handlers use explicit context managers
- `tests/*.py` - All tests migrated to context manager pattern

**Benefits:**
- Prevents connection leaks (context manager ensures cleanup)
- Consistent patterns between Core and Soil
- Enforced correctness (runtime exceptions prevent misuse)
- Better error diagnostics with stack traces

**Technical Details:** See module docstrings in `system/core/__init__.py` and `system/soil/database.py`

---

### ✅ Session 6.6: ActionResult Schema Enhancement (Completed 2026-02-09)

**Tests:** 167/167 passing (8 new tests for structured error capture)

**Deliverables:**
- ActionResult schema updated with structured error format (code, message, details)
- Audit decorator captures exception type for `error.code` (validation_error, not_found, lock_conflict, permission_denied, internal_error)
- `error.message` contains human-readable error description
- `error.details` contains optional structured error context
- `error_type` and `error_traceback` stored in ActionResult.data for debugging
- Schema synced between `/schemas/types/items/` and `/memogarden-system/system/schemas/types/items/`

**Key Files:**
- `schemas/types/items/actionresult.schema.json`, `memogarden-system/system/schemas/types/items/actionresult.schema.json`
- `api/handlers/decorators.py` (_get_error_code, _extract_error_details)
- `tests/test_audit_facts.py` (TestStructuredErrorCapture class - 8 new tests)

**RFC-005 v7.1 Alignment:**
- error.code: Machine-readable error classification
- error.message: Human-readable error description
- error.details: Optional structured error context
- error_type: Full exception class name
- error_traceback: Full Python traceback

**Benefits:**
- Better error diagnostics for debugging
- Structured error codes for programmatic handling
- Enables error aggregation and analysis
- Aligns with RFC-005 v7.1 specification

---

### ✅ Session 7: Relations Bundle Verbs (Completed 2026-02-09)

**Tests:** 185/185 passing (18 new tests for Relations bundle)

**Deliverables:**
- `unlink` verb - Remove user relation
- `edit_relation` verb - Edit relation attributes (time_horizon, metadata, evidence)
- `get_relation` verb - Get relation by UUID
- `query_relation` verb - Query relations with filters (source, target, kind, type, alive_only, limit)
- `explore` verb - Graph expansion from anchor (BFS traversal with direction, radius, kind, limit controls)
- RelationOperations methods: `delete()`, `edit()`, `query()`

**Key Files:**
- `memogarden-system/system/core/relation.py` (delete, edit, query methods)
- `memogarden-api/api/handlers/core.py` (handle_unlink, handle_edit_relation, handle_get_relation, handle_query_relation, handle_explore)
- `memogarden-api/api/schemas/semantic.py` (UnlinkRequest, QueryRelationRequest, ExploreRequest)
- `memogarden-api/api/semantic.py` (request validation, HANDLERS dict)
- `memogarden-api/tests/test_relations_bundle.py` (18 new tests)

**RFC-002 v5 Alignment:**
- unlink: Remove user relations (system relations remain immutable)
- edit_relation: Update time_horizon, metadata, evidence
- query_relation: Filter by source, target, kind, source_type, target_type, alive_only
- explore: Graph traversal with direction (outgoing, incoming, both), radius limit, kind filter, node limit
- BFS traversal algorithm with visited tracking to avoid cycles

**Invariants Enforced:**
- INV-TH-009: System relation kinds are immutable
- INV-TH-010: User relation kinds can be edited and removed
- Graph traversal respects direction and radius limits
- Node count limit enforced during BFS

**Dependencies:** Session 3 (user relations), Session 6 (audit facts)

---

### ✅ Session 7.5: Code Review Fixes (Completed 2026-02-09)

**Tests:** 185/185 passing (all existing tests continue to pass)

**Deliverables:**
- Fixed datetime import violation - replaced `from datetime import datetime` with ISO string types
- Added public Core API methods to avoid private connection access
- Fixed bare except clauses with specific exception types and logging
- Documented security limitation in handle_unlink with TODO for future authorization

**Key Files:**
- `memogarden-api/api/schemas/semantic.py` - Replaced datetime types with str (ISO 8601 strings)
- `memogarden-system/system/core/entity.py` - Added `query_with_filters()` and `exists()` public methods
- `memogarden-api/api/handlers/core.py` - Updated handle_query and handle_explore to use public APIs

**Must-Fix Violations Addressed:**
1. ✅ **VIOLATION #1: Direct datetime import** - Replaced with ISO string types (canonical_at: str, timestamp: str)
2. ✅ **VIOLATION #2: Handler accessing private connection** - Added `core.entity.query_with_filters()` and `core.entity.exists()` public methods
3. ✅ **VIOLATION #3: Bare except clauses** - Replaced with specific exceptions (ResourceNotFound) and logging
4. ⚠️ **VIOLATION #4: Missing authorization checks** - Documented with TODO comment (requires schema change to add created_by field)

**Architectural Compliance Improvements:**
- All handlers now use public Core API methods instead of accessing `core._conn`
- Exception handling uses specific types (ResourceNotFound) with logging instead of bare except
- Type annotations use ISO string format for timestamps, consistent with isodatetime utility

**Remaining Should-Fix Improvements (Documented for Future):**
- [HIGH] ISSUE #10: N+1 query problem in handle_explore - batch fetch entities instead of individual queries
- [MEDIUM] ISSUE #4: handle_explore complexity (143 lines) - extract into helper functions
- [MEDIUM] ISSUE #5: Inconsistent UUID prefix handling in responses
- [LOW] ISSUE #6: Test data management - use fixtures instead of duplicating entity creation
- [LOW] ISSUE #7: Hardcoded UUIDs in tests - create entities in test setup
- [MEDIUM] ISSUE #8: Add maximum radius limit to explore verb (DoS prevention)
- [MEDIUM] ISSUE #9: Add created_by field to user_relation table for authorization

**RFC Alignment:**
- Maintains RFC-005 v7.1 and RFC-002 v5 compliance
- Improves architectural consistency with memogarden-development patterns

---

### ✅ Session 8: Track Verb (Completed 2026-02-09)

**Tests:** 192/192 passing (7 new tests for track verb)

**Deliverables:**
- `track` verb for tracing causal chain from entity back to originating facts
- TrackRequest schema with `target` (entity UUID) and `depth` (hop limit, default: unlimited)
- Recursive tree traversal following `derived_from` links
- Response format with tree structure and `kind` markers (entity)
- Depth limit parameter to prevent runaway traversal
- Handles diamond ancestry naturally (same entity referenced multiple times)
- Cycle detection to avoid infinite loops

**Key Files:**
- `api/handlers/core.py` (handle_track with recursive build_tree function)
- `api/schemas/semantic.py` (TrackRequest schema)
- `api/semantic.py` (added "track" to HANDLERS and request_schemas)
- `tests/test_track.py` (7 tests covering various scenarios)

**RFC-005 v7.1 Alignment:**
- track: Trace entity lineage through derived_from links
- Response format: Tree structure with kind markers
- Depth limit parameter prevents runaway traversal
- Handles diamond ancestry (same source referenced multiple times)

**Implementation Notes:**
- Initial implementation tracks derived_from chain (entity-to-entity derivation)
- Future enhancement: Track through EntityDelta items for fact-level lineage
- Uses sqlite3.Row direct column access (not dict.get() due to architectural constraints)
- **Enhancement:** Response includes `type` field for better debugging and client-side filtering

**Future Enhancements (Code Review Recommendations):**
1. **Extract Cycle Detection Logic** - Make cycle detection reusable for other traversal operations (explore, search)
2. **Add Maximum Depth Safety Limit** - Consider `Field(le=1000)` in TrackRequest for defense-in-depth
3. **Performance Optimization** - Consider batch loading or caching for deep chains (N+1 query pattern)
4. **Document Type Field in RFC-005** - Add `type` field to RFC response format specification

**Code Review Status:** ✅ APPROVED (Zero violations, excellent architectural compliance)

**Dependencies:** Session 1 (Core bundle verbs), Session 3 (user relations)

---

### ✅ Session 9: Search Verb (Completed 2026-02-09)

**Tests:** 200/200 passing (8 new tests for search verb)

**Deliverables:**
- `search` verb for semantic search and discovery
- Fuzzy text search strategy (SQLite LIKE with wildcards)
- Coverage levels: names (type only), content (type + data), full (all searchable fields)
- Effort modes: quick, standard, deep (framework in place, implementation simplified for Session 9)
- Target types: entity, fact, all
- Limit parameter for pagination

**Key Files:**
- `api/handlers/core.py` (handle_search with fuzzy matching across entities and facts)
- `api/schemas/semantic.py` (SearchRequest schema)
- `api/semantic.py` (added "search" to HANDLERS and request_schemas)
- `tests/test_search.py` (8 new tests covering search scenarios)

**RFC-005 v7.1 Alignment:**
- search: Semantic search and discovery
- Coverage: names (fast), content (names+body), full (all fields)
- Strategy: fuzzy (text matching with LIKE), auto (system choice)
- Target types: entity, fact, all
- Continuation token framework (deferred to future session)

**Implementation Notes:**
- Fuzzy matching uses SQLite LIKE with wildcards (%query%)
- Searches across entity.type, entity.data fields
- Searches across item._type, item.data, item.metadata fields
- Results include "kind" marker ("entity" or "fact") for disambiguation
- Effort modes and continuation tokens are framework-ready but simplified in this session

**Future Enhancements:**
- Semantic search with embeddings (vector DB or external service)
- Continuation token implementation for deep pagination
- Cached results for "quick" effort mode
- Threshold filtering for similarity scores

**Dependencies:** Session 1 (Semantic API), Session 2 (Soil bundle)

---

### ✅ Session 9.1: Code Review Fixes (Completed 2026-02-09)

**Tests:** 200/200 passing (all existing tests continue to pass)

**Deliverables:**
- Fixed architectural violation: Removed direct `_conn` access from handler
- Added public `EntityOperations.search()` method for entity search
- Added public `Soil.search_items()` method for fact/item search
- Updated `handle_search` to use public APIs instead of private connections
- Removed unnecessary PRAGMA calls
- Added clear TODO comments for all deferred features

**Key Files:**
- `system/core/entity.py` - Added `search()` method with coverage level support
- `system/soil/database.py` - Added `search_items()` method with coverage level support
- `api/handlers/core.py` - Refactored `handle_search` to use public APIs, added TODO comments

**Fixed Violations:**
1. ✅ **VIOLATION #1: Direct _conn access** - Added public search methods to Core/Soil, updated handler to call them
2. ✅ **VIOLATION #2: Missing continuation token** - Added clear TODO with implementation specification

**Documented Deferred Features:**
- **Continuation tokens**: Added TODO with base64 encoding spec for offset/limit/timestamp
- **Strategy parameter**: Added TODO for "auto" strategy selection and "semantic" implementation
- **Effort modes**: Added TODO for "quick" caching and "deep" exhaustive search
- **Threshold filtering**: Added TODO for similarity score filtering (requires semantic search)

**Architectural Improvements:**
- All handlers now use public Core/Soil APIs (no private connection access)
- Search logic encapsulated in Core/Soil layers (proper separation of concerns)
- Clear documentation of deferred features with implementation specifications

**RFC Alignment:**
- Maintains RFC-005 v7.1 compliance
- Deferred features properly documented for future implementation

**Code Quality Improvements:**
- Removed unnecessary PRAGMA synchronous calls (connection setup responsibility)
- Improved code maintainability (public API interfaces)

**Dependencies:** Session 9 (Search Verb)

---

### ✅ Session 10: Config-Based Path Resolution (Completed 2026-02-09)

**Tests:** 215/215 passing (15 new tests for path resolution)

**Deliverables:**
- `get_db_path(layer)` function in `system/host/environment.py`
- `MEMOGARDEN_SOIL_DB` environment variable support
- `MEMOGARDEN_CORE_DB` environment variable support
- `MEMOGARDEN_DATA_DIR` environment variable support
- Core updated to use config-based paths (when database_path=None)
- Soil updated to use config-based paths (when db_path=None)
- Backward compatible with explicit path parameters

**Key Files:**
- `memogarden-system/system/host/environment.py` (get_db_path function)
- `memogarden-system/system/config.py` (Settings with database_path=None support)
- `memogarden-system/system/core/__init__.py` (_create_connection, init_db updated)
- `memogarden-system/system/soil/database.py` (get_soil updated)
- `memogarden-api/tests/test_path_resolution.py` (15 new tests)

**RFC-004 Invariants Enforced:**
- INV-PKG-001: Resolution order: layer-specific override → shared data dir → current directory
- INV-PKG-002: Backward compatible - explicit paths still work
- INV-PKG-003: Default paths: `./{layer}.db`

**Path Resolution Examples:**
```python
# Layer-specific override (highest priority)
os.environ['MEMOGARDEN_SOIL_DB'] = '/custom/soil.db'
get_db_path('soil')  # → Path('/custom/soil.db')

# Shared data directory
os.environ['MEMOGARDEN_DATA_DIR'] = '/data'
get_db_path('core')  # → Path('/data/core.db')

# Default (current directory, backward compatible)
get_db_path('soil')  # → Path('./soil.db')
```

**Dependencies:** None (standalone utility)

---

### Session 11: Schema Access Utilities (1-2 hours)

**Goal:** RFC-004 schema bundling and runtime access

**Tasks:**
1. Create `system/schemas.py` module
2. Implement `get_sql_schema(layer)` - Return soil.sql or core.sql
3. Implement `get_type_schema(category, type_name)` - Return JSON schema
4. Implement `list_type_schemas(category)` - List available schemas
5. Update Soil/Core to use `get_sql_schema()`
6. Add schema bundling to pyproject.toml
7. Add tests

**Invariants to Enforce (RFC-004):**
- Try importlib.resources first (bundled package)
- Fall back to file reading (development mode)
- Raise FileNotFoundError if schema not found

**Deliverables:** Schema access utilities, testable

**Dependencies:** None (standalone utility)

---

### ✅ Session 11: Schema Access Utilities (Completed 2026-02-09)

**Tests:** 19/19 passing (system package tests)

**Deliverables:**
- `system/schemas.py` module with schema access utilities
- `get_sql_schema(layer)` - Return soil.sql or core.sql content
- `get_type_schema(category, type_name)` - Return JSON schema as Python dict
- `list_type_schemas(category)` - List available type schemas by category
- Updated `Soil.init_schema()` to use `get_sql_schema('soil')`
- Updated `Core.init_db()` to use `get_sql_schema('core')`
- Schema bundling in `pyproject.toml` (includes `system/schemas/**/*.sql` and `**/*.json`)

**Key Files:**
- `system/schemas.py` - Schema access utilities
- `system/soil/database.py` - Updated init_schema() method
- `system/core/__init__.py` - Updated init_db() function
- `pyproject.toml` - Added include directive for schema files
- `tests/test_schemas.py` - 19 tests for schema access utilities

**RFC-004 v2 Alignment:**
- INV-PKG-004: Try importlib.resources first (bundled package)
- INV-PKG-005: Fall back to file reading (development mode)
- INV-PKG-006: Raise FileNotFoundError if schema not found in either location

**Implementation Details:**
- Schema access uses importlib.resources (Python 3.13) for bundled packages
- Falls back to Path-based file reading for development mode
- Searches multiple locations: `system/schemas/` and root `schemas/` directories
- Type name extraction reads JSON schema 'title' field for accurate names
- Handles multi-word type names correctly (e.g., "ActionResult" not "Actionresult")

**Benefits:**
- Decouples schema location from code (no hardcoded paths)
- Enables schema bundling in production packages
- Supports both installed packages and development mode
- Single source of truth for schema access

**Dependencies:** None (standalone utility)

---

### Session 12: REST API - Generic Entities (2-3 hours)

**Goal:** Entity CRUD for external apps

**Tasks:**
1. Implement `POST /api/v1/entities` - Create entity
2. Implement `GET /api/v1/entities` - List with filters
3. Implement `GET /api/v1/entities/{uuid}` - Get single
4. Implement `PATCH /api/v1/entities/{uuid}` - Edit (set/unset)
5. Implement `DELETE /api/v1/entities/{uuid}` - Forget
6. Add Pydantic schemas
7. Add tests

**Note:** REST API is Entity-only for external CRUD apps. Full capabilities (Facts, Relations, Context) accessed via Semantic API.

**Deliverables:** Complete Entity REST API, testable

**Dependencies:** Session 1 (Semantic API patterns)

### Session 13: Cross-Database Transactions (2-3 hours)

**Goal:** RFC-008 transaction semantics

**Tasks:**
1. Implement `begin_transaction()` - EXCLUSIVE locks on both databases
2. Implement `commit_transaction()` - Soil first, then Core
3. Implement `rollback_transaction()` - Best-effort rollback
4. Implement transaction context manager
5. Add startup consistency checks (orphaned deltas, broken chains)
6. Implement `update_entity()` with cross-DB coordination
7. Add tests for all commit scenarios

**Invariants to Enforce (RFC-008):**
- EXCLUSIVE locks on both databases for cross-DB operations
- Commit ordering: **Soil first** (source of truth), then Core
- Single-DB operations: Standard SQLite ACID
- System status modes: NORMAL, INCONSISTENT, READ_ONLY, SAFE_MODE
- Startup checks for orphaned EntityDeltas and broken hash chains
- Optimistic locking: Update requires matching based_on_hash

**Failure Modes:**
- Both succeed → NORMAL
- Both fail → NORMAL (rolled back)
- Soil commits, Core fails → INCONSISTENT (requires repair)
- Process killed between commits → INCONSISTENT (detected on startup)

**Deliverables:** Robust cross-DB transactions, testable

**Dependencies:** Session 6 (audit facts), Session 4 (context)

### Session 14: Fossilization - Basic Sweep (2-3 hours)

**Goal:** RFC-002 automatic storage management

**Tasks:**
1. Implement `fossilization_sweep()` - Background task
2. Implement `query_fossilization_candidates()` - Find expired items
3. Implement `should_fossilize_item()` - Check time_horizon
4. Implement `fossilize_item()` - Compress to summary
5. Add extractive summary generation
6. Implement SweepMetrics collection
7. Add tests

**Invariants to Enforce (RFC-002):**
- Item fossilizes when `max(time_horizon of inbound relations) < current_day()`
- Orphaned items (no relations) fossilize immediately
- Fidelity states: full → summary → stub → tombstone
- System relations persist (immutable)
- User relations move from Core to Soil (prefix change: core_ → soil_)

**Deliverables:** Working fossilization sweep, testable

**Dependencies:** Session 3 (user relations), Session 4 (context capture)

### Remaining Sessions (Future Work)

**Provider Plugins:** Email import (Gmail, mbox), provider registry

**App Framework (RFC-009):** IPC protocol, app SDKs, reference app

**Encryption (RFC-001):** SQLCipher integration, key management

**System Agent (RFC-007):** Background tasks, health monitoring

---

## Critical Invariants

This section consolidates all invariants from RFCs that must be enforced via implementation and testing.

### RFC-002: Relation Time Horizon & Fossilization

**Time Horizon Computation:**
- **INV-TH-001:** `time_horizon += delta * SAFETY_COEFFICIENT` on each access (SAFETY_COEFFICIENT = 1.2)
- **INV-TH-002:** `relation_is_alive() ⇔ time_horizon >= current_day()`
- **INV-TH-003:** Fact significance = `max(inbound_user_relations.time_horizon)` (None if orphaned)
- **INV-TH-004:** Orphaned facts (no inbound relations) fossilize immediately on sweep

**Fidelity States:**
- **INV-TH-005:** Fidelity progression: full → summary → stub → tombstone
- **INV-TH-006:** `fossilized_at` timestamp set when fidelity changes from full
- **INV-TH-007:** System relations persist unchanged (not subject to fossilization)
- **INV-TH-008:** User relations move from Core to Soil (UUID prefix: core_ → soil_)

**System vs User Relations:**
- **INV-TH-009:** System relation kinds are immutable (triggers, cites, replies_to, derives_from, contains, continues, supersedes, result_of)
- **INV-TH-010:** User relation kinds decay over time (currently: explicit_link only)

### RFC-003: Context Mechanism (26 Invariants)

**View Identity (INV-1):**
- Each View has exactly ONE UUID
- Same View UUID appended to user and all active scope ContextFrames (synchronized)

**Context Update (INV-2, INV-3, INV-4):**
- INV-2: Synchronized Append - one View UUID to all ContextFrames atomically
- INV-3: Primary Context Capture - scope's context if entity in scope, else user's
- INV-4: Automatic Capture - snapshot happens without caller intervention

**Fork and Merge (INV-5, INV-6, INV-7):**
- INV-5: Fork Inheritance - subordinate gets copy of parent's containers at fork time
- INV-6: Merge Termination - ViewMerge appended to both, subordinate ContextFrame destroyed
- INV-7: No Automatic Context Inheritance - parent does NOT absorb subordinate's context after merge

**Scope Suspension (INV-8):**
- User's view-stream continues on leave, scope's view-stream suspends (no appends)

**View Chaining (INV-9, INV-10):**
- INV-9: Linked List via `prev` pointer
- INV-10: ViewMerge has `prev` + `metadata.merged_views` array

**Scope Activation (INV-11, INV-11a, INV-11b):**
- INV-11: Explicit scope control (enter ≠ focus, requires confirmation for multi-scope objects)
- INV-11a: Focus Separation - entering scope does NOT auto-focus
- INV-11b: Implied Focus - subagent with one scope, user first registered

**Context Size (INV-12, INV-13):**
- INV-12: LRU-N Limit - containers ≤ N (N=7 initially)
- INV-13: Tunable N - subject to empirical adjustment

**Context Persistence (INV-14, INV-15, INV-16):**
- INV-14: Cross-Session Persistence - context persists across logout/login
- INV-15: Persistent Users Only - operators and primary agents, NOT subagents
- INV-16: Explicit Context Break - temporal boundary in view-stream

**Visit Filtering (INV-17, INV-18, INV-19):**
- INV-17: Substantive vs Primitive - not all accesses update context
- INV-18: Type-Based Classification - substantive/primitive is type property
- INV-19: Hardcoded Initial Classification - Artifact=substantive, Schema=primitive

**Scope Ownership (INV-20, INV-21):**
- INV-20: One ContextFrame Per Owner
- INV-21: Subordinate Context Ownership - owned by agent, not scope

**View Coalescence (INV-22, INV-23):**
- INV-22: Action Grouping - multiple actions coalesce into single View
- INV-23: Coalescence Boundaries - explicit break, inactivity timeout (5s), mutation to different scope

**Fossilization Integration (INV-24, INV-25):**
- INV-24: View Stream Compression - old Views subject to fossilization
- INV-25: Context Preservation - delta `context` field preserved during fossilization

**Concurrent Access (INV-26):**
- No Shared ContextFrame - same scope, different users → each has own ContextFrame

### RFC-005: Semantic API

**Verb Semantics:**
- **INV-API-001:** Facts use `add` (bring external data in) / `amend` (correct/rectify)
- **INV-API-002:** Entities use `create` (bring into being) / `edit` (revise and publish)
- **INV-API-003:** `forget` marks entity inactive but traces remain in Soil
- **INV-API-004:** `query` filter operators: bare value (=), `{"any": [...]}` (OR), `{"not": value}` (negation)

**Null Semantics:**
- **INV-API-005:** `null` = "not yet known" (Unknown), not "intentionally empty"

**Response Envelope:**
- **INV-API-006:** All responses include `ok`, `actor`, `timestamp`, `result`/`error`

**Audit Facts (Section 7):**
- **INV-API-007:** Action fact created immediately when operation starts
- **INV-API-008:** ActionResult fact created when operation completes
- **INV-API-009:** System relation `result_of` links ActionResult → Action
- **INV-API-010:** Use `bypass_semantic_api=True` to prevent audit recursion
- **INV-API-011:** Fossilization: high-frequency (search) → +7d, mutations → +30d, security → +1y

### RFC-008: Transaction Semantics

**Transaction Scope:**
- **INV-TX-001:** Single-DB operations: Standard SQLite ACID
- **INV-TX-002:** Cross-DB operations: Best-effort atomicity with app-level coordination
- **INV-TX-003:** Split operations: Item commits independently, relation retries on failure

**Isolation and Locking:**
- **INV-TX-004:** SERIALIZABLE via `BEGIN EXCLUSIVE` on both databases
- **INV-TX-005:** One transaction per handle (no nesting, no SAVEPOINTs)
- **INV-TX-006:** Other handles block on `busy_timeout` (5s default)

**Commit Ordering:**
- **INV-TX-007:** Commit ordering: Soil first, then Core (Soil is source of truth)
- **INV-TX-008:** If Soil commits but Core fails → system marked INCONSISTENT
- **INV-TX-009:** Process killed between commits → INCONSISTENT (detected on next startup)

**Rollback:**
- **INV-TX-010:** Best-effort rollback (if one DB committed, rollback is no-op on that DB)

**Optimistic Locking:**
- **INV-TX-011:** `entity.hash = SHA256(JSON(state) + entity.previous_hash)`
- **INV-TX-012:** Update requires `based_on_hash` to match current hash
- **INV-TX-013:** Hash mismatch → OptimisticLockError (application provides resolution)

**System Status:**
- **INV-TX-014:** Modes: NORMAL, INCONSISTENT, READ_ONLY, SAFE_MODE
- **INV-TX-015:** No issues → NORMAL
- **INV-TX-016:** Orphaned deltas → INCONSISTENT
- **INV-TX-017:** Database corruption → SAFE_MODE

**Startup Consistency Check:**
- **INV-TX-018:** Check for orphaned EntityDeltas (Soil committed, Core did not)
- **INV-TX-019:** Check for broken hash chains (previous_hash doesn't match)
- **INV-TX-020:** System starts regardless of state (always-available startup)

**Undo vs Rollback:**
- **INV-TX-021:** Transaction rollback: uncommitted changes discarded (immediate, before commit)
- **INV-TX-022:** Undo operation: compensating ToolCall within 5 minutes (committed operations)

### RFC-004: Package Deployment

**Path Resolution:**
- **INV-PKG-001:** Resolution order: layer-specific env var → shared data dir → current dir
- **INV-PKG-002:** Backward compatible - explicit paths still work
- **INV-PKG-003:** Default paths: `./{layer}.db`

**Schema Access:**
- **INV-PKG-004:** Try importlib.resources first (bundled package)
- **INV-PKG-005:** Fall back to file reading (development mode)
- **INV-PKG-006:** Raise FileNotFoundError if schema not found in either location

### General Invariants

**UUID Prefixes:**
- **INV-GEN-001:** Soil UUIDs use `soil_` prefix
- **INV-GEN-002:** Core UUIDs use `core_` prefix
- **INV-GEN-003:** APIs accept both prefixed and non-prefixed UUIDs
- **INV-GEN-004:** Responses always include prefix

**Hash Chains:**
- **INV-GEN-005:** Entity `hash` = SHA256(data + type + created_at + previous_hash)
- **INV-GEN-006:** `previous_hash` is NULL for initial entities
- **INV-GEN-007:** `version` monotonically increases on each update

**Fact Immutability:**
- **INV-GEN-008:** Fact `realized_at` never changes after creation
- **INV-GEN-009:** Fact `canonical_at` is user-controllable but immutable once set
- **INV-GEN-010:** Fact modifications create new Facts with `supersedes` links

---

## Open Questions

### Design Decisions Needed

1. **Search Implementation:**
   - Q: Use external vector DB (e.g., Qdrant) or built-in embeddings?
   - A: Recommendations needed from performance requirements

2. **Summary Generation:**
   - Q: LLM-based or extractive only?
   - A: Start with extractive, add LLM as optional plugin

3. **Context Size (N):**
   - Q: Is N=7 optimal for LRU-N context?
   - A: Start with 7, tune based on usage data

4. **Fossilization Schedule:**
   - Q: How often to run sweep?
   - A: Daily initially, make configurable

5. **Encryption:**
   - Q: Required for MVP or defer?
   - A: Defer to post-MVP unless regulatory requirements

### Technical Debt to Address

1. **Database Paths:**
   - Current: Hardcoded relative paths
   - Needed: Config-based path resolution per RFC-004
   - **Session:** 10 ✅ Completed

2. **Schema Access:**
   - Current: Direct file reading
   - Needed: Bundled schemas with importlib.resources
   - **Session:** 11 ✅ Completed

3. **Error Messages:**
   - Current: Generic error messages
   - Needed: Detailed, actionable error messages per RFC-006
   - **Progress:** Session 6.6 added structured error capture (error.code, error.message, error.details) ✅

4. **Test Coverage:**
   - Current: 234 tests passing (Session 11 complete)
   - Breakdown: 215 API tests (20 transactions, 12 recurrences, 9 auth, 37 context, 25 user relations, 48 semantic api, 8 audit facts, 18 relations bundle, 7 track, 8 search, 15 path resolution) + 19 system tests (schema access utilities)
   - Needed: Comprehensive tests for all features

5. **Code Quality Improvements (Session 8 Code Review):**
   - **Cycle Detection Logic** - Extract for reusability in explore/search operations
   - **Track Verb Safety** - Add `Field(le=1000)` maximum depth limit
   - **Performance** - Batch loading or caching for deep chains (N+1 query pattern)
   - **RFC Documentation** - Document `type` field in RFC-005 response format

**Resolved:**
- ✅ **Session 6.5:** Connection lifecycle: Context manager pattern enforced
- ✅ **Session 6.5:** Core/Soil consistency: Unified patterns, no autocommit lie
- ✅ **Session 7.5:** Architectural violations: Fixed datetime import, private connection access, bare except clauses
- ✅ **Session 8:** Track verb: Zero violations, excellent architectural compliance
- ✅ **Session 10:** Database paths: RFC-004 config-based path resolution
- ✅ **Session 11:** Schema access: RFC-004 schema bundling and runtime access

---

## References

### Related Documents

- **PRD v0.11.1:** Complete platform requirements
- **RFC-001 v4:** Security & Operations Architecture
- **RFC-002 v5:** Relation Time Horizon & Fossilization
- **RFC-003 v4:** Context Mechanism (26 invariants)
- **RFC-004 v2:** Package Structure & Deployment
- **RFC-005 v7.1:** API Design (Semantic verbs, audit facts)
- **RFC-006 v1:** Error Handling & Diagnostics
- **RFC-007 v2:** Runtime Operations
- **RFC-008 v1.2:** Transaction Semantics (cross-DB coordination)
- **RFC-009 v1:** Application Model
- **RFC Alignment Analysis:** See `plan/rfc_alignment_analysis.md` for detailed RFC comparison

### Codebases

- **memogarden-system:** Core system library
- **memogarden-api:** Flask REST + Semantic API
- **providers:** Data import providers (future)
- **schemas:** SQL and JSON schema definitions

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.16 | 2026-02-09 | Mark Session 11 complete (Schema Access Utilities with 19 tests), update test count to 234 |
| 1.15 | 2026-02-09 | Mark Session 10 complete (Config-Based Path Resolution with 15 tests), update test count to 215 |
| 1.14 | 2026-02-09 | Mark Session 9.1 complete (code review fixes), added public search APIs |
| 1.13 | 2026-02-09 | Mark Session 9 complete (Search verb with 8 tests), update test count to 200 |
| 1.12 | 2026-02-09 | Mark Session 8 complete (Track verb with 7 tests), update test count to 192 |
| 1.11 | 2026-02-09 | Mark Session 7.5 complete (code review fixes), add should-fix improvements to implementation plan |
| 1.10 | 2026-02-09 | Mark Session 7 complete (Relations bundle verbs), update test count to 185 |
| 1.9 | 2026-02-09 | Mark Session 6.6 complete (structured error capture), update test count to 167 |
| 1.8 | 2026-02-08 | Add Session 6.6 (ActionResult schema) and Session 8 (Track verb), update RFC versions to v7.1/v1.2 |
| 1.7 | 2026-02-08 | Compact completed sessions (1-6.5) to summary format, reduce context bloat |
| 1.6 | 2026-02-08 | Add Session 6 completion (Audit Facts with Action/ActionResult schemas and decorator) |
| 1.5 | 2026-02-08 | Add Session 5 database locking fix, document type checking fix in core.py |
| 1.4 | 2026-02-08 | Update Session 5 status to completed |
| 1.3 | 2026-02-08 | Update Session 4 status to completed |
| 1.2 | 2026-02-08 | Update Session 2 and Session 3 status to completed |
| 1.1 | 2026-02-07 | Update Session 1 status to completed, add session status table |
| 1.0 | 2026-02-07 | Initial implementation plan, consolidates rfc-004-implementation-plan.md |

---

**Status:** Active Development - Session 11 Complete, 234 tests passing

**Document Structure:**
- Completed sessions (1-11): Summary format with key deliverables and test counts
- Future sessions (12-14): Full detail for implementation planning
- Technical implementation details: See module docstrings and git commit history

**RFC Alignment:**
- RFC-004 v2: 90% complete (Session 11: Schema bundling and runtime access complete. Missing: full package distribution testing)
- RFC-005 v7.1: 85% complete (Sessions 1-2, audit facts, structured error capture, Relations bundle, code review fixes, track verb, search verb complete)
- RFC-002 v5: 65% complete (User relations, Relations bundle verbs complete. Missing: fossilization engine, authorization for unlink)
- RFC-008 v1.2: 90% complete (Session 6.5 aligned, recovery tools pending)
- See `plan/rfc_alignment_analysis.md` for detailed comparison

**Code Quality Improvements (Session 7.5, 9.1, 10, 11):**
- Fixed all must-fix violations from code review (datetime import, private connection access, bare except clauses)
- Added public APIs (search methods) to avoid private connection access
- Implemented RFC-004 environment variable support with backward compatibility
- Implemented RFC-004 schema bundling and runtime access (importlib.resources + file fallback)

**Next Steps:**
1. ⏳ **Session 12: REST API - Generic Entities** (Entity CRUD for external apps)
2. ⏳ **Session 13: Cross-Database Transactions** (RFC-008 transaction semantics)
3. Continue implementing remaining Semantic API features
4. Write tests alongside implementation

---

**END OF DOCUMENT**
