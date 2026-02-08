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

**Current Compliance:** ~35% of PRD v0.11.1 requirements implemented

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
| **RFC-003 v4** | Context Mechanism | ❌ 0% | Schema exists (context_frame table). No operations, no view stream. |
| **RFC-004 v2** | Package Deployment | ⚠️ 50% | Structure correct. Missing: get_db_path(), schema bundling. |
| **RFC-005 v7** | API Design | ⚠️ 30% | REST endpoints for Transaction only. Semantic API missing entirely. |
| **RFC-006 v1** | Error Handling | ✅ 80% | Exception hierarchy complete. Diagnostics tools missing. |
| **RFC-007 v2** | Runtime Operations | ❌ 0% | No system agent, no background tasks. |
| **RFC-008 v1** | Transaction Semantics | ⚠️ 40% | Cross-DB coordination defined but not enforced. |
| **RFC-009 v1** | App Model | ❌ 0% | No IPC, no SDKs, no app registry. |

---

## Completed Work

### ✅ Core Schema (v20260130)

**Location:** `/schemas/sql/soil.sql`, `/schemas/sql/core.sql`

- [x] Polymorphic `item` table with JSON `data` field
- [x] Polymorphic `entity` table with JSON `data` field
- [x] Hash chain fields (hash, previous_hash, version)
- [x] `system_relation` table for immutable structural facts
- [x] `user_relation` table for engagement signals (time_horizon)
- [x] `context_frame` table for attention tracking
- [x] Schema metadata table for version tracking
- [x] All indexes for timeline queries

### ✅ Type Schemas

**Location:** `/schemas/types/items/`, `/schemas/types/entities/`

Item types (Fact schemas):
- [x] `item.schema.json` - Base Fact type
- [x] `email.schema.json` - RFC 5322 email with threading
- [x] `note.schema.json` - Text note
- [x] `message.schema.json` - Communication between participants
- [x] `entitydelta.schema.json` - Entity mutation audit
- [x] `systemevent.schema.json` - System notifications
- [x] `toolcall.schema.json` - Tool invocation records

Entity types:
- [x] `entity.schema.json` - Base Entity type
- [x] `transaction.schema.json` - Financial transaction
- [x] `artifact.schema.json` - Structured document
- [x] `label.schema.json` - Named reference
- [x] `operator.schema.json` - Human user
- [x] `agent.schema.json` - AI agent

### ✅ memogarden-system

**Location:** `/memogarden-system/system/`

**Soil Layer:**
- [x] `soil/database.py` - Soil database class
  - [x] `create_item()` - Create items
  - [x] `get_item()` - Retrieve by UUID
  - [x] `find_item_by_rfc_message_id()` - Email deduplication
  - [x] `list_items()` - List with filtering
  - [x] `create_relation()` - SystemRelation CRUD
  - [x] `create_replies_to_relation()` - Email threading
  - [x] `get_relations()` - Query relations
- [x] `soil/item.py` - Item dataclass with hash computation
- [x] `soil/relation.py` - SystemRelation dataclass
- [x] `soil/__init__.py` - Package exports

**Core Layer:**
- [x] `core/entity.py` - EntityOperations class
  - [x] `create()` - Create entity with auto-UUID and hash
  - [x] `get_by_id()` - Retrieve with error handling
  - [x] `supersede()` - Mark as superseded
  - [x] `update_hash()` - Maintain hash chain
  - [x] `check_conflict()` - Optimistic locking
- [x] `core/transaction.py` - Transaction CRUD with JSON data
  - [x] `create()` - Create transaction
  - [x] `get_by_id()` - Retrieve transaction
  - [x] `list()` - Filter by date/account/category
  - [x] `update()` - Partial updates with hash chain
  - [x] `get_accounts()` - Distinct account labels
  - [x] `get_categories()` - Distinct category labels
- [x] `core/recurrence.py` - Recurrence CRUD
- [x] `core/seed.py` - Seed data helpers
- [x] `core/query.py` - Query builders
- [x] `core/types.py` - Type definitions
- [x] `core/__init__.py` - Core facade with get_core()

**Utilities:**
- [x] `utils/uid.py` - UUID generation, prefix handling
- [x] `utils/hash_chain.py` - SHA256 hash computation
- [x] `utils/isodatetime.py` - ISO 8601 timestamps
- [x] `utils/recurrence.py` - Recurrence rules
- [x] `utils/secret.py` - Secret management

**Host Interface:**
- [x] `host/filesystem.py` - Path resolution, directory operations
- [x] `host/environment.py` - Environment variable access
- [x] `host/time.py` - UTC time utilities

**Exceptions:**
- [x] `exceptions.py` - MemoGardenError hierarchy
  - [x] ResourceNotFound
  - [x] ValidationError
  - [x] AuthenticationError
  - [x] ConflictError

### ✅ memogarden-api

**Location:** `/memogarden-api/api/`

**HTTP Server:**
- [x] Flask app with CORS
- [x] Error handlers for all exception types
- [x] Health check endpoint
- [x] Database initialization on startup

**Semantic API (Session 1 - Core Bundle Complete):**
- [x] `semantic.py` - `/mg` endpoint dispatcher
- [x] `handlers/core.py` - Core bundle verb handlers (create, get, edit, forget, query)
- [x] `schemas/semantic.py` - Pydantic request/response schemas
- [x] Response envelope with ok, actor, timestamp, result/error
- [x] UUID prefix handling (accept both prefixed and non-prefixed)
- [x] Authentication middleware for all Semantic API requests
- [x] Baseline entity type validation (Transaction, Recurrence, Artifact, Label, Operator, Agent, Entity)

**Authentication (RFC-001 v4):**
- [x] `middleware/service.py` - User and API key CRUD
- [x] `middleware/token.py` - JWT token generation/validation
- [x] `middleware/api_keys.py` - API key management
- [x] `middleware/decorators.py` - @authenticate, @localhost_only
- [x] `middleware/schemas/auth.py` - Pydantic schemas
- [x] Routes:
  - [x] `POST /auth/register` - Admin registration (localhost only)
  - [x] `POST /auth/login` - User login (JWT)
  - [x] `GET /auth/me` - Current user info
  - [x] `POST /auth/api_keys` - Create API key
  - [x] `GET /auth/api_keys` - List API keys
  - [x] `DELETE /auth/api_keys/{id}` - Revoke API key

**REST API (RFC-005 v7):**
- [x] `v1/core/transactions.py` - Transaction endpoints
  - [x] `POST /api/v1/transactions` - Create
  - [x] `GET /api/v1/transactions` - List with filters
  - [x] `GET /api/v1/transactions/{id}` - Get single
  - [x] `PUT /api/v1/transactions/{id}` - Update with conflict detection
  - [x] `DELETE /api/v1/transactions/{id}` - Soft delete
  - [x] `GET /api/v1/transactions/accounts` - List accounts
  - [x] `GET /api/v1/transactions/categories` - List categories
- [x] `v1/core/recurrences.py` - Recurrence endpoints (similar pattern)

**Validation:**
- [x] `validation.py` - @validate_request decorator
- [x] `schemas/transaction.py` - Pydantic request/response schemas
- [x] `schemas/recurrence.py` - Recurrence schemas

### ✅ Test Infrastructure

**Location:** `/memogarden-api/tests/`

- [x] `conftest.py` - Pytest fixtures
  - [x] Test database with schema initialization
  - [x] Authentication fixtures (JWT + API key)
  - [x] SHA256 function registration
- [x] `test_transactions.py` - 20 tests for transaction CRUD
- [x] `test_recurrences.py` - 12 tests for recurrence CRUD
- [x] `test_auth.py` - 9 tests for authentication
- [x] `test_semantic_api.py` - 22 tests for Semantic API Core bundle (Session 1)
- [x] **All 66 tests passing (100%)**

### ✅ Documentation

- [x] `/plan/memogarden_prd_v0_11_0.md` - Complete PRD with latest terminology
- [x] `/plan/rfc-005_memogarden_api_design_v7.md` - API design with audit facts
- [x] `/plan/rfc-002_relation_time_horizon_v5.md` - Fossilization specification
- [x] `/plan/rfc-003_context_mechanism_v4.md` - Context mechanism
- [x] `/plan/rfc-009_memogarden_apps_v1.md` - Application model
- [x] AGENTS.md - AI agent guide

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

**Status:** ❌ Not Implemented

**Required Components:**

1. **`system.schemas` Module:**
   - [ ] Create `/memogarden-system/system/schemas.py`
   - [ ] `get_sql_schema(layer)` - Return soil.sql or core.sql content
   - [ ] `get_type_schema(category, type_name)` - Return JSON schema
   - [ ] `list_type_schemas(category)` - List available schemas

2. **Resource Bundling:**
   - [ ] Bundle schemas in package (pyproject.toml configuration)
   - [ ] Use importlib.resources for package access
   - [ ] Fallback to file reading in development mode

3. **Update Init Logic:**
   - [ ] Soil/Core use `get_sql_schema()` instead of hardcoded paths
   - [ ] Remove hardcoded `../schemas/sql/` paths

**Dependencies:** None (can start immediately)

#### 2.2 Config-Based Path Resolution (RFC-004 v2)

**Status:** ❌ Not Implemented

**Required Components:**

1. **Environment Variable Support:**
   - [ ] `MEMOGARDEN_SOIL_DB` - Explicit Soil database path
   - [ ] `MEMOGARDEN_CORE_DB` - Explicit Core database path
   - [ ] `MEMOGARDEN_DATA_DIR` - Shared data directory

2. **`get_db_path()` Function:**
   - [ ] Add to `/memogarden-system/system/host/environment.py`
   - [ ] Resolution order: env var → data dir → current directory
   - [ ] Layer parameter: 'soil' or 'core'

3. **Update Soil/Core Initialization:**
   - [ ] Default db_path to `None` in __init__
   - [ ] Call `get_db_path()` when db_path is None
   - [ ] Maintain backward compatibility (explicit paths still work)

**Dependencies:** None (can start immediately)

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
| 6 | Audit Facts | ⏳ Not Started | - | 0/0 |
| 7 | Relations Bundle Verbs | ⏳ Not Started | - | 0/0 |
| 8 | Search Verb | ⏳ Not Started | - | 0/0 |
| 9 | Config-Based Path Resolution | ⏳ Not Started | - | 0/0 |
| 10 | Schema Access Utilities | ⏳ Not Started | - | 0/0 |
| 11 | REST API - Generic Entities | ⏳ Not Started | - | 0/0 |
| 12 | Cross-Database Transactions | ⏳ Not Started | - | 0/0 |
| 13 | Fossilization - Basic Sweep | ⏳ Not Started | - | 0/0 |

---

### Session 1: Semantic API - Core Bundle Verbs ✅ COMPLETED

**Goal:** Basic Entity CRUD via Semantic API

**Status:** ✅ Completed 2026-02-07

**Completed Tasks:**
1. ✅ Implement `/mg` endpoint dispatcher (request envelope → handler → response envelope)
2. ✅ Implement `create` verb - Create entity (baseline types)
3. ✅ Implement `get` verb - Get entity by UUID
4. ✅ Implement `edit` verb - Edit entity (set/unset semantics)
5. ✅ Implement `forget` verb - Soft delete entity
6. ✅ Implement `query` verb - Query entities with basic filters
7. ✅ Add tests for Core bundle verbs (22 tests passing)

**Deferred Tasks:**
- ❌ `register` verb - Custom schema registration (deferred to future session)
- ❌ Full query DSL with operators (any, not, etc.) - basic equality only
- ❌ Domain-specific table updates in `edit` - only entity.data updated

**Implemented Files:**
- `/memogarden-api/api/semantic.py` - `/mg` endpoint dispatcher
- `/memogarden-api/api/handlers/core.py` - Core verb handlers (create, get, edit, forget, query)
- `/memogarden-api/api/schemas/semantic.py` - Pydantic request/response schemas
- `/memogarden-api/tests/test_semantic_api.py` - 22 tests, all passing

**Invariants Enforced:**
- ✅ Response envelope includes `ok`, `actor`, `timestamp`, `result`/`error`
- ✅ UUID prefix handling (accept both prefixed and non-prefixed)
- ✅ Null semantics (null = "Unknown", not "intentionally empty")
- ✅ Authentication required for all `/mg` endpoints
- ✅ Baseline entity types supported (Transaction, Recurrence, Artifact, Label, Operator, Agent, Entity)

**Dependencies:** None

### ✅ Session 2: Semantic API - Soil Bundle Verbs (COMPLETED)

**Completed:** 2026-02-07

**Goal:** Fact operations via Semantic API

**Tasks:**
1. ✅ Implement `add` verb - Add fact (bring external data into MemoGarden)
2. ✅ Implement `amend` verb - Amend fact (create superseding fact)
3. ✅ Extend `query` verb - Support fact queries (type, start, end, filters)
4. ✅ Add tests for Soil bundle verbs

**Implementation:**
- Created `api/handlers/soil.py` with Soil verb handlers (add, amend, get, query)
- Added `AddRequest` and `AmendRequest` schemas to `api/schemas/semantic.py`
- Updated `api/semantic.py` dispatcher to route get/query based on UUID prefix and target_type
- Added 15 new tests for Soil bundle verbs (all passing)
- Added Soil database initialization to test fixtures

**Invariants Enforced:**
- ✅ Facts are immutable (amend creates new fact with `supersedes` link)
- ✅ `integrity_hash` computed on all fact creation
- ✅ `_type` validated against registered schemas

**Deliverables:** Complete Soil bundle with 37 tests passing (22 Core + 15 Soil)

**Commit:** 6dcdd57 "feat: implement Semantic API Soil bundle verbs (Session 2)"

**Dependencies:** Session 1 ✅

### Session 3: User Relations ✅ COMPLETED

**Completed:** 2026-02-08

**Goal:** Engagement signals with time horizon (RFC-002)

**Tasks:**
1. ✅ Create `system/core/relation.py` - UserRelation operations
2. ✅ Implement `create()` - Create user relation with initial time_horizon
3. ✅ Implement `update_time_horizon()` - Apply SAFETY_COEFFICIENT on access
4. ✅ Implement `expire()` - Mark relation for fossilization
5. ✅ Implement `list_inbound()`/`list_outbound()` - Query relations
6. ✅ Add `link` verb to Semantic API
7. ✅ Add tests for time horizon computation

**Implementation:**
- Created `system/core/relation.py` with RelationOperations class
- Implemented all operations: create, get_by_id, update_time_horizon, list_inbound, list_outbound, expire, fact_time_horizon, is_alive
- Added `time` utility module with current_day() and day_to_date() functions
- Added `link` verb to Semantic API (handler in api/handlers/core.py)
- Added LinkRequest schema to api/schemas/semantic.py
- Created comprehensive tests (19 tests passing)

**Invariants Enforced (RFC-002):**
- ✅ `time_horizon += delta * SAFETY_COEFFICIENT` (default: 1.2)
- ✅ `relation_is_alive()` ⇔ `time_horizon >= current_day()`
- ✅ Fact significance = max(inbound_relation.time_horizons)
- ✅ Orphaned facts (no relations) have None significance

**Deliverables:** Complete user relations with time horizon, all tests passing

**Test Results:**
- test_user_relations.py: 19 tests passing
- test_semantic_api.py (link verb): 6 tests passing

**Dependencies:** Session 1 (Semantic API foundation) ✅

### Session 4: Context Framework - Basic Operations ✅ COMPLETED

**Completed:** 2026-02-08

**Goal:** ContextFrame and View stream foundation (RFC-003)

**Tasks:**
1. ✅ Create `system/core/context.py` - Context operations
2. ✅ Implement `get_context_frame()` - Get by owner (user or scope)
3. ✅ Implement `update_containers()` - LRU-N eviction (N=7 initially)
4. ✅ Implement `create_view()` - Create View with actions
5. ✅ Implement `append_view()` - Append to ContextFrame's view timeline
6. ✅ Define substantive vs primitive types (hardcoded initially)
7. ✅ Add comprehensive tests (26 tests passing)

**Implementation:**
- Created `system/core/context.py` with ContextOperations class
- Implemented all operations: get_context_frame, _create_context_frame, get_context_frame_by_uuid, update_containers, create_view, append_view
- Added substantive vs primitive type classification (SUBSTANTIVE_TYPES, PRIMITIVE_TYPES)
- Created JSON schemas for View, ViewMerge, and ContextFrame entity types
- Registered context operations with Core class (core.context property)
- Added 26 comprehensive tests covering all RFC-003 invariants

**Invariants Enforced (RFC-003):**
- ✅ INV-1: Unique View UUID (core_ prefix added to all View UUIDs)
- ✅ INV-12: LRU-N limit (containers ≤ N, N=7 initially)
- ✅ INV-17: Substantive vs primitive classification (type-based)
- ✅ INV-18: Type-Based Classification
- ✅ INV-19: Hardcoded Initial Classification
- ✅ INV-20: One ContextFrame per owner
- ✅ INV-26: No shared ContextFrame (even for same scope)

**Deliverables:** Complete context tracking foundation, all tests passing

**Test Results:**
- test_context.py: 26 tests passing
- All 132 tests passing across entire test suite

**Dependencies:** Session 3 (user relations for linking) ✅

**Code Review Fixes Applied:**
- ✅ C1: Removed unused `datetime`, `timezone` imports
- ✅ C2: Fixed database query logic for proper INV-20 compliance (operators use NULL, agents/scopes use owner_type)
- ✅ L2: Added runtime validation for `owner_type` parameter
- ✅ H2: Added `ViewAction.to_dict()` method to handle `visited: None` properly (converts to empty array)
- ✅ H3: Added `context_frame_uuid` validation in `create_view()` to prevent orphaned Views
- ✅ H1: Consistent UUID prefix handling using `uid.add_core_prefix()` helper
- ✅ M3: Added `append_view_to_contexts()` helper for atomic multi-context append
- ✅ M1: Documented `view_timeline` limitation (in-memory only, deferred to Session 5)

**Known Limitations (Deferred to Session 5):**
- `view_timeline` is tracked in-memory only, not persisted to database
- ContextFrame.view_timeline is always empty when loaded from database
- This violates INV-14 (Cross-Session Persistence) - will be fixed in Session 5
- Implementation will require: add view_timeline column to context_frame table, query Views from entity table

### Session 5: Context Verbs and Capture ✅ COMPLETED

**Completed:** 2026-02-08

**Goal:** Context verbs and automatic capture (RFC-003)

**Completed Tasks:**
1. ✅ Added `active_scopes` and `primary_scope` columns to `context_frame` table
2. ✅ Updated `ContextFrame` dataclass with new fields
3. ✅ Implemented `enter_scope()` - Add scope to active set
4. ✅ Implemented `leave_scope()` - Remove from active set
5. ✅ Implemented `focus_scope()` - Switch primary scope
6. ✅ Added request schemas (EnterRequest, LeaveRequest, FocusRequest)
7. ✅ Added handlers for context verbs in `api/handlers/core.py`
8. ✅ Updated `api/semantic.py` dispatcher to route context verbs
9. ✅ Added tests for RFC-003 context invariants (37 tests passing)

**Implementation:**
- Updated `system/schemas/sql/core.sql` with `active_scopes` and `primary_scope` columns
- Created migration `migrations/002_add_context_scope_columns.sql`
- Implemented context verb operations in `system/core/context.py`
- Added Semantic API request schemas in `api/schemas/semantic.py`
- Added verb handlers in `api/handlers/core.py` (handle_enter, handle_leave, handle_focus)
- Updated dispatcher in `api/semantic.py` to route context verbs
- Created comprehensive tests (37 tests in test_context.py)

**Invariants Enforced (RFC-003):**
- ✅ INV-11: Explicit scope control (enter ≠ focus, requires confirmation)
- ✅ INV-11a: Focus separation (enter does NOT auto-focus)
- ✅ INV-11b: Implied focus (first scope becomes primary automatically)
- ✅ INV-8: Stream suspension on leave (scope view-stream suspends)
- ✅ INV-20: One ContextFrame per owner

**Deliverables:** Complete context verb mechanism (enter/leave/focus), all tests passing

**Test Results:**
- test_context.py: 37 tests passing (26 original + 11 new for context verbs)
- test_semantic_api.py: Context verb tests pass individually

**Known Limitations (Deferred to future sessions):**
- `rejoin()` verb not implemented (requires ViewMerge and fork/merge logic)
- Context capture decorator for entity mutations not implemented
- `visit_entity()` not implemented (automatic container updates)
- INV-2: Synchronized Append not fully implemented (requires multi-context view updates)
- INV-3: Primary context capture not implemented
- INV-4: Automatic capture not implemented
- INV-5: Fork inheritance not fully implemented (subordinate contexts)

**Session 5 Fixes (2026-02-08):**
- ✅ Fixed database locking in concurrent test execution by switching from shared temp file to in-memory database (`:memory:`)
  - Updated `tests/conftest.py` to use shared cache in-memory database
  - All 151 tests now pass reliably without locking issues
  - Updated test documentation in `tests/README.md`

**Dependencies:** Session 4 (context framework) ✅

### Session 6: Audit Facts (2-3 hours)

**Goal:** Complete audit trail for all operations (RFC-005 v7 Section 7)

**Tasks:**
1. Create Action fact schema in `/schemas/types/items/action.schema.json`
2. Create ActionResult fact schema
3. Add `result_of` to SYSTEM_RELATION_KINDS
4. Implement audit decorator for Semantic API operations
5. Create Action fact on operation start
6. Create ActionResult fact on operation completion
7. Link via `result_of` relation
8. Add tests

**Invariants to Enforce (RFC-005 v7):**
- Action fact created immediately when operation begins
- ActionResult fact created when operation completes (success/failure/timeout/cancelled)
- System relation links ActionResult → Action (kind: `result_of`)
- Use `bypass_semantic_api=True` to prevent recursion
- Fossilization policy: search→+7d, mutations→+30d, security→+1y

**Deliverables:** Complete audit trail, testable

**Dependencies:** Session 1, 2, 5 (Semantic API + Context)

### Session 7: Relations Bundle Verbs (2-3 hours)

**Goal:** Complete relation management via Semantic API

**Tasks:**
1. Implement `unlink` verb - Remove relation
2. Implement `edit` verb - Edit relation attributes (time_horizon)
3. Extend `query` verb - Support relation queries
4. Implement `explore` verb - Graph expansion from anchor
5. Add tests for relation operations

**Invariants to Enforce (RFC-002):**
- System relations are immutable (cannot be edited/unlinked)
- User relations have time_horizon that decays
- `explore` respects direction (outgoing, incoming, both)
- Graph traversal respects radius limit

**Deliverables:** Complete Relations bundle, testable

**Dependencies:** Session 3 (user relations), Session 5 (context)

### Session 8: Search Verb (2-3 hours)

**Goal:** Semantic search and discovery

**Tasks:**
1. Implement `search` verb dispatcher
2. Implement fuzzy search strategy (text matching with typo tolerance)
3. Implement auto strategy (system chooses based on query)
4. Implement coverage levels (names, content, full)
5. Implement effort modes (quick, standard, deep)
6. Add continuation token pagination
7. Add tests

**Invariants to Enforce (RFC-005 v7):**
- Coverage: names (fast), content (names+body), full (all fields)
- Strategy: semantic (embeddings), fuzzy (text matching), auto (system choice)
- Effort: quick (cached), standard (full), deep (exhaustive)
- Continuation tokens for pagination
- Threshold filtering (minimum similarity score)

**Deliverables:** Working search, testable

**Dependencies:** Session 1 (Semantic API), Session 2 (Soil bundle)

### Session 9: Config-Based Path Resolution (1-2 hours)

**Goal:** RFC-004 environment variable support

**Tasks:**
1. Implement `get_db_path(layer)` in `system/host/environment.py`
2. Add `MEMOGARDEN_SOIL_DB` env var support
3. Add `MEMOGARDEN_CORE_DB` env var support
4. Add `MEMOGARDEN_DATA_DIR` env var support
5. Update Soil to use config-based paths
6. Update Core to use config-based paths
7. Add tests

**Invariants to Enforce (RFC-004):**
- Resolution order: layer-specific override → shared data dir → current directory
- Backward compatible (explicit paths still work)
- Default paths: `./{layer}.db`

**Deliverables:** Config-based path resolution, testable

**Dependencies:** None (standalone utility)

### Session 10: Schema Access Utilities (1-2 hours)

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

### Session 11: REST API - Generic Entities (2-3 hours)

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

### Session 12: Cross-Database Transactions (2-3 hours)

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

### Session 13: Fossilization - Basic Sweep (2-3 hours)

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

2. **Schema Access:**
   - Current: Direct file reading
   - Needed: Bundled schemas with importlib.resources

3. **Error Messages:**
   - Current: Generic error messages
   - Needed: Detailed, actionable error messages per RFC-006

4. **Test Coverage:**
   - Current: 66 tests (44 for transactions/recurrences/auth, 22 for Semantic API Core bundle)
   - Needed: Comprehensive tests for all features

---

## References

### Related Documents

- **PRD v0.11.1:** Complete platform requirements
- **RFC-001 v4:** Security & Operations Architecture
- **RFC-002 v5:** Relation Time Horizon & Fossilization
- **RFC-003 v4:** Context Mechanism (26 invariants)
- **RFC-004 v2:** Package Structure & Deployment
- **RFC-005 v7:** API Design (Semantic verbs)
- **RFC-006 v1:** Error Handling & Diagnostics
- **RFC-007 v2:** Runtime Operations
- **RFC-008 v1:** Transaction Semantics
- **RFC-009 v1:** Application Model

### Codebases

- **memogarden-system:** Core system library
- **memogarden-api:** Flask REST + Semantic API
- **providers:** Data import providers (future)
- **schemas:** SQL and JSON schema definitions

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.5 | 2026-02-08 | Add Session 5 database locking fix, document type checking fix in core.py |
| 1.4 | 2026-02-08 | Update Session 5 status to completed |
| 1.3 | 2026-02-08 | Update Session 4 status to completed |
| 1.2 | 2026-02-08 | Update Session 2 and Session 3 status to completed |
| 1.1 | 2026-02-07 | Update Session 1 status to completed, add session status table |
| 1.0 | 2026-02-07 | Initial implementation plan, consolidates rfc-004-implementation-plan.md |

---

**Status:** Active Development - Session 5 Complete

**Next Steps:**
1. ✅ ~~Review and prioritize Phase 1 tasks~~ (Completed - Session 1)
2. ✅ ~~Set up Semantic API development environment~~ (Completed)
3. ✅ ~~Implement Core bundle verbs first (highest value)~~ (Completed)
4. ✅ ~~Implement Soil bundle verbs (Session 2)~~ (Completed)
5. ✅ ~~Implement User Relations (Session 3)~~ (Completed)
6. ✅ ~~Implement Context Framework - Basic Operations (Session 4)~~ (Completed)
7. ✅ ~~Implement Context Verbs (Session 5)~~ (Completed)
8. ⏳ **Start Session 6: Audit Facts** (RFC-005 v7 Section 7)
9. Continue implementing remaining Semantic API bundles (Search, Relations)
10. Write tests alongside implementation

---

**END OF DOCUMENT**
