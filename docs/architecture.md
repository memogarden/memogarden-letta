# MemoGarden Architecture Overview

**Last Updated:** 2026-02-14
**Version:** 0.1.0

Complete architectural reference for MemoGarden platform.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Diagram](#component-diagram)
3. [Database Architecture](#database-architecture)
4. [API Layer](#api-layer)
5. [Data Flow](#data-flow)
6. [Core Concepts](#core-concepts)

---

## System Overview

MemoGarden is a **belief-based transaction capture and reconciliation system** designed for both human users and AI agents.

### Core Philosophy

1. **Transactions Are Beliefs** - A transaction represents your understanding at the time of payment, not the bank's ledger
2. **Single Source of Truth** - All transactions flow through MemoGarden Core API
3. **Mutable Snapshot, Immutable Memory** - Current state can change, but all changes are logged via deltas
4. **Document-Centric Traceability** - Transactions link to immutable artifacts in Soil (emails, invoices, receipts)
5. **Agent-First Design** - Humans and agents use the same APIs

### Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MemoGarden Platform                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Client Apps  │  │  AI Agents     │  │   Web UI    │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘ │
│           │                    │                    │           │
│           └────────────────────┴────────────────────┴───────────┘   │
│                                │                                │
├────────────────────────────────┬────────────────────────────────────────┤
│                                │                                │
│                    ┌───────────▼────────────────────┐            │
│                    │      API Layer                │            │
│                    │  ┌────────────────────────┐   │            │
│                    │  │  Flask REST API      │   │            │
│                    │  │  /api/v1/*           │   │            │
│                    │  ├────────────────────────┤   │            │
│                    │  │  Semantic API        │   │            │
│                    │  │  /mg                 │   │            │
│                    │  └────────────────────────┘   │            │
│                    └───────────┬────────────────────┘            │
│                                │                                │
├────────────────────────────────┬────────────────────────────────────────┤
│                                │                                │
│           ┌────────────────────┴────────────────────┐           │
│           │         System Layer                   │           │
│           │  ┌─────────────┬──────────────────┐   │           │
│           │  │   Core       │  Soil            │   │           │
│           │  │  (Mutable)   │  (Immutable)      │   │           │
│           │  │  ┌─────────┐ │  ┌──────────┐ │   │           │
│           │  │  │Entity    │ │  │Fact     │ │   │           │
│           │  │  │Transaction│ │  │Email    │ │   │           │
│           │  │  │Relation  │ │  │Message  │ │   │           │
│           │  │  │Context   │ │  │Note     │ │   │           │
│           │  │  │Artifact  │ │  │ToolCall │ │   │           │
│           │  │  └─────────┘ │  └──────────┘ │   │           │
│           │  └─────────────┴──────────────────┘   │           │
│           │                                       │           │
│           └───────────────────────────────────────┘           │
│                                                           │
│  ┌─────────────────────────────────────────────────┐           │
│  │        SQLite Databases                  │           │
│  │  ┌─────────────────┬─────────────────┐   │           │
│  │  │  core.db         │  soil.db         │   │           │
│  │  │  • Entities      │  • Facts         │   │           │
│  │  │  • Transactions  │  • Emails        │   │           │
│  │  │  • Relations     │  • Messages       │   │           │
│  │  │  • Context       │  • Artifacts      │   │           │
│  │  └─────────────────┴─────────────────┘   │           │
│  └─────────────────────────────────────────────────┘           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram

### Repository Structure

MemoGarden consists of **three separate git repositories**:

```
memogarden/                    # Root repository
├── plan/                      # Planning documents
│   ├── memogarden_prd_v0_11_0.md
│   ├── memogarden-implementation-plan.md
│   └── rfc_*.md              # RFC-001 through RFC-009
├── docs/                      # Documentation
├── scripts/                    # Automation scripts
└── .claude/                    # Agent configuration

memogarden-system/               # System library (Soil + Core)
└── system/
    ├── core/                    # Core database operations
    │   ├── entity.py
    │   ├── transaction.py
    │   ├── recurrence.py
    │   ├── relation.py
    │   └── context.py
    ├── soil/                    # Soil database operations
    │   ├── fact.py
    │   ├── artifact.py
    │   └── relation.py
    ├── schemas/
    │   └── sql/
    │       ├── core.sql
    │       └── soil.sql
    └── host/
        └── environment.py         # RFC-004 path resolution

memogarden-api/                  # Flask REST + Semantic API
└── api/
    ├── main.py                  # Flask app factory
    ├── semantic.py               # /mg endpoint (RFC-005)
    ├── v1/                      # /api/v1/* REST endpoints
    ├── handlers/                 # Semantic API handlers
    ├── middleware/               # Auth, decorators
    └── schemas/                  # Pydantic schemas
```

---

## Database Architecture

MemoGarden uses **two separate SQLite databases** with distinct responsibilities:

### Core Database (`core.db`)

**Purpose:** Mutable entities with version history

**Tables:**

| Table | Purpose | Key Fields |
|-------|---------|-------------|
| `entity` | Global registry with hash chain | uuid, type, hash, previous_hash, version, data (JSON) |
| `user_relation` | Engagement signals with time horizon | uuid, kind, source, target, time_horizon |
| `context_frame` | Attention tracking (LRU-N) | uuid, containers, active_scopes, primary_scope |

**Entity Types:**
- `Transaction` - Financial transactions
- `Recurrence` - Recurring transaction patterns
- `Contact` - Contact information
- `Account` - Financial accounts
- `Artifact` - Project Studio artifacts
- `Scope` - Project Studio scopes (RFC-003)
- `ConversationLog` - Project Studio conversations

### Soil Database (`soil.db`)

**Purpose:** Immutable facts and structural relations

**Tables:**

| Table | Purpose | Key Fields |
|-------|---------|-------------|
| `item` | Polymorphic timeline with JSON data | uuid, _type, realized_at, canonical_at, data (JSON) |
| `system_relation` | Immutable structural facts | uuid, kind, source, target |

**Fact Types:**
- `Message` - Conversation messages
- `Email` - Imported emails
- `Note` - User notes
- `ToolCall` - Agent tool invocations
- `ArtifactDelta` - Artifact change records

### Cross-Database Coordination (RFC-008)

The **TransactionCoordinator** manages operations across both databases:

```
┌─────────────────────────────────────────────────────────────┐
│              TransactionCoordinator                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Acquire EXCLUSIVE locks on both databases  │   │
│  │ 2. Begin transactions on both connections        │   │
│  │ 3. Execute coordinated operations               │   │
│  │ 4. Commit soil.db FIRST (RFC-008 ordering)    │   │
│  │ 5. Commit core.db SECOND                       │   │
│  │ 6. Release locks                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                          │
│  System States:                                          │
│  • NORMAL - No issues detected                        │
│  • INCONSISTENT - Cross-DB integrity issue         │
│  • READ_ONLY - Safe mode, no writes allowed          │
│  • SAFE_MODE - Recovery mode                         │
└─────────────────────────────────────────────────────────────┘
```

---

## API Layer

### Semantic API (`/mg`)

**Design:** Single endpoint with operation-based dispatch (RFC-005 v7)

```
POST /mg
{
  "op": "operation_name",
  "param1": "value1"
}

Response:
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-14T10:30:00Z",
  "result": { ... }
}
```

**Operation Bundles:**

| Bundle | Operations | Purpose |
|--------|-------------|---------|
| **Core** | create, get, edit, forget, query | Entity CRUD |
| **Soil** | add, amend, get, query | Fact operations |
| **Relations** | link, unlink, edit_relation, query_relation, explore | Graph operations |
| **Context** | enter, leave, focus | RFC-003 context management |
| **Advanced** | track, search | Tracing and search |

### REST API (`/api/v1/`)

**Design:** Traditional resource-based endpoints

```
GET    /api/v1/transactions           # List
POST   /api/v1/transactions           # Create
GET    /api/v1/transactions/{uuid}   # Get one
PATCH  /api/v1/transactions/{uuid}   # Update
DELETE /api/v1/transactions/{uuid}   # Delete
```

---

## Data Flow

### Creating a Transaction

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   Client   │────▶│   API Layer  │────▶│  System Layer       │
│  (Web/App) │     │  Flask App   │     │  Core + Soil        │
└─────────────┘     └──────┬───────┘     └──────┬──────────────┘
                            │                      │
                            │ POST /mg             │ 1. Acquire locks
                            │ {                     │ 2. Begin transactions
                            │   "op": "create",    │    │
                            │   "type": "Transaction",│    │
                            │   "data": {...}       │    │
                            │                      │ 3. Create entity record
                            │                      │    in core.entity
                            │                      │ 4. Create entry facts
                            │◀───────────────────────│    in soil.item
                            │                      │ 5. Link facts to entity
                            │                      │    in soil.system_relation
                            │                      │ 6. Commit soil.db
                            │                      │ 7. Commit core.db
                            │                      │ 8. Release locks
                            │                      │
                            │◀───────────────────────│
                            │                      │
                            │{                     │
                            │  "ok": true,            │
                            │  "result": {             │
                            │    "uuid": "core_xxx",  │
                            │    ...                   │
                            │  }                      │
└──────────────────────────────┘
```

### Tracking Transaction History

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   Client   │────▶│   API Layer  │────▶│  System Layer       │
│            │     │              │     │                     │
│ POST /mg   │     │              │     │ 1. Get entity         │
│ {          │     │              │     │ 2. Follow derived_from │
│   "op":    │     │              │     │    links backward     │
│   "track", │     │              │     │ 3. Load source facts │
│   "target": │     │              │     │ 4. Build causal tree │
│   "core_xxx"│     │              │     │ 5. Return tree      │
│ }          │     │              │     │                     │
│            │     │              │     │  Result:            │
│            │◀───────────────────│     │  {                   │
│            │{                    │     │    "entity": {...}, │
│            │  "ok": true,         │     │    "sources": [     │
│            │  "result": {          │     │      {             │
│            │    "entity": {...},  │     │        "kind":   │
│            │    "sources": [      │     │          "fact", │
│            │      {               │     │        "uuid":   │
│            │        "kind": "fact",│     │          "soil_xxx"│
│            │        "uuid": "soil_xxx"│     │      }             │
│            │      }                │     │    ]                 │
│            │    ]                   │     │  }                     │
└──────────────────────────────┘     └─────────────────────┘
```

---

## Core Concepts

### UUID Prefixes

All UUIDs use a prefix to indicate their layer:

| Prefix | Layer | Example |
|--------|-------|---------|
| `core_` | Core entities | `core_550e8400-e29b-41d4-a716-446655440000` |
| `soil_` | Soil facts | `soil_550e8400-e29b-41d4-a716-446655440000` |
| `rel_` | Relations | `rel_550e8400-e29b-41d4-a716-446655440000` |
| `usr_` | Users | `usr_550e8400-e29b-41d4-a716-446655440000` |

### Context Management (RFC-003)

Context tracks what the user/agent is currently working on:

```
┌─────────────────────────────────────────────────────┐
│              ContextFrame                         │
│  ┌─────────────────────────────────────────────┐   │
│  │  containers: [Scope A, Scope B, Scope C]  │   │
│  │  primary_scope: Scope A                   │   │
│  │  active_scopes: [Scope A, Scope B]       │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  • LRU-N eviction (N=7)                             │
│  • View stream with automatic coalescence             │
│  • enter/leave/focus operations                     │
└─────────────────────────────────────────────────────┘
```

### Time Horizon (RFC-002)

Relations have a time horizon that determines when they expire:

```
time_horizon = current_time + (duration * SAFETY_COEFFICIENT)

SAFETY_COEFFICIENT = 1.2  # 20% buffer
```

When a relation expires, fossilization may reduce fidelity.

---

## See Also

- [API Documentation](api.md)
- [Quickstart Guide](quickstart.md)
- [Deployment Guide](deployment.md)
- [Configuration Reference](configuration.md)
- RFC-005 v7: API Design
- RFC-008 v1.2: Transaction Semantics
