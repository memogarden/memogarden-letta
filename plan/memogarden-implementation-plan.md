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
| **REST API** | ⚠️ Partial | 40% | Transaction/Recurrence endpoints only. Missing: Soil, Relations, Context |
| **Semantic API** | ❌ Not Implemented | 0% | /mg endpoint, all 17 verbs |
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
- [x] **All 44 tests passing (100%)**

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

**Status:** ❌ Not Implemented

**Required Components:**

1. **`/mg` Endpoint** - Message-passing interface for apps
   - [ ] Request envelope parsing (op, params)
   - [ ] Response envelope (ok, actor, timestamp, result/error)
   - [ ] Actor tracking (user vs agent)

2. **Core Bundle Verbs:**
   - [ ] `create` - Create entity
   - [ ] `edit` - Edit entity (set/unset semantics)
   - [ ] `forget` - Soft delete entity
   - [ ] `get` - Get entity/fact/relation by UUID
   - [ ] `query` - Query with filters, linked queries, pagination
   - [ ] `register` - Register custom schema

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

**Files to Create:**
- `/memogarden-api/api/semantic.py` - Semantic API dispatcher
- `/memogarden-api/api/handlers/core.py` - Core verb handlers
- `/memogarden-api/api/handlers/soil.py` - Soil verb handlers
- `/memogarden-api/api/handlers/relations.py` - Relation verb handlers
- `/memogarden-api/api/handlers/semantic.py` - Search verb handler
- `/memogarden-api/api/handlers/context.py` - Context verb handlers

**Dependencies:** None (can start immediately)

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

### Phase 1: Semantic API Foundation (2-3 weeks)

**Goal:** Enable all MemoGarden operations via Semantic API

**Tasks:**
1. Implement `/mg` endpoint dispatcher
2. Implement Core bundle verbs (create, edit, forget, get, query, register)
3. Implement Soil bundle verbs (add, amend, get, query)
4. Implement Relations bundle verbs (link, unlink, edit, get, query, explore)
5. Implement Context bundle verbs (enter, leave, focus, rejoin)
6. Add comprehensive tests for all verbs

**Deliverables:**
- Working Semantic API with all 17 verbs
- Test suite for Semantic API
- API documentation

**Dependencies:** None

### Phase 2: Core Platform Features (3-4 weeks)

**Goal:** Implement context, user relations, and audit trail

**Tasks:**
1. Implement UserRelation operations (time horizon logic)
2. Implement Context mechanism (ContextFrame, View stream)
3. Implement Audit facts (Action, ActionResult)
4. Add context capture to all entity mutations
5. Test all RFC-003 invariants

**Deliverables:**
- Complete context mechanism
- User relations with time horizon
- Full audit trail

**Dependencies:** Phase 1

### Phase 3: REST API Completion (2 weeks)

**Goal:** Complete REST API for all resources

**Tasks:**
1. Implement Soil Item endpoints
2. Implement generic Entity endpoints
3. Implement SystemRelation endpoints
4. Add Pydantic schemas for all resources

**Deliverables:**
- Complete REST API
- REST API documentation

**Dependencies:** Phase 1

### Phase 4: Search and Discovery (2-3 weeks)

**Goal:** Enable semantic search and graph exploration

**Tasks:**
1. Implement search verb (semantic, fuzzy, auto)
2. Implement explore verb (graph traversal)
3. Add embedding generation (if using semantic search)
4. Implement continuation token pagination
5. Performance testing

**Deliverables:**
- Working search and explore verbs
- Search performance benchmarks

**Dependencies:** Phase 1, Phase 3

### Phase 5: Fossilization (3-4 weeks)

**Goal:** Implement automatic storage management

**Tasks:**
1. Implement fossilization sweep
2. Implement summary generation
3. Implement fidelity state transitions
4. Implement storage pressure eviction
5. Implement relation fossilization
6. Add metrics collection

**Deliverables:**
- Complete fossilization engine
- Fossilization tests
- Configuration tuning guide

**Dependencies:** Phase 2 (context, user relations)

### Phase 6: Provider Plugins (2-3 weeks)

**Goal:** Enable data import from external sources

**Tasks:**
1. Define Provider protocol
2. Implement Gmail provider
3. Implement mbox provider
4. Implement provider registry
5. Add provider tests

**Deliverables:**
- Working email import
- Provider framework documentation

**Dependencies:** Phase 3 (Soil Item API)

### Phase 7: Cross-Database Coordination (1-2 weeks)

**Goal:** Enforce transaction semantics across Soil and Core

**Tasks:**
1. Implement atomic cross-DB transactions
2. Implement inconsistency detection
3. Implement recovery tools (diagnose, repair)
4. Add failure logging

**Deliverables:**
- Robust cross-DB operations
- Recovery tools

**Dependencies:** Phase 2 (audit facts)

### Phase 8: App Framework (4-5 weeks)

**Goal:** Enable third-party apps

**Tasks:**
1. Implement IPC protocol
2. Implement app registry
3. Implement Python SDK
4. Implement TypeScript SDK
5. Create reference app
6. Add app documentation

**Deliverables:**
- Complete app framework
- SDKs for Python and TypeScript
- Reference app

**Dependencies:** Phase 4 (search)

### Phase 9: Advanced Features (ongoing)

**Tasks:**
1. Encryption at rest
2. System agent
3. Performance optimization
4. Additional SDKs (Dart, Java)
5. Graph visualization

**Dependencies:** Various

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
   - Current: 44 tests for transactions/recurrences/auth
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
| 1.0 | 2026-02-07 | Initial implementation plan, consolidates rfc-004-implementation-plan.md |

---

**Status:** Active Development

**Next Steps:**
1. Review and prioritize Phase 1 tasks
2. Set up Semantic API development environment
3. Implement Core bundle verbs first (highest value)
4. Write tests alongside implementation

---

**END OF DOCUMENT**
