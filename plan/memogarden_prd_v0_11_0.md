# MemoGarden Product Requirements Document

**Version:** 0.11.1  
**Date:** 2026-02-06  
**Status:** Active Development

---

## Overview

MemoGarden is a personal information management system designed as a data substrate for human-AI collaboration. It provides an "immortal" system that can run indefinitely on resource-constrained hardware while maintaining usefulness over decades.

### Core Principles

- **Store everything, decay most things**: Append-only timeline with fossilization mechanisms
- **AI legibility**: Structured data optimized for machine collaboration
- **Temporal validity**: Track when information is true in the real world, not just when it was recorded
- **Explicit coordination**: Prefer explicit handover over implicit delegation
- **Zero private state for agents**: Transparency through shared tool access
- **Local-first architecture**: Strong privacy defaults, personal-scale deployment

---

## Architecture Overview

MemoGarden uses a two-layer storage model:

| Layer | Purpose | Mutability | Storage |
|-------|---------|------------|---------|
| **Soil** | Immutable timeline of facts | Append-only | soil.db (SQLite) |
| **Core** | Mutable state and entities | Delta-tracked | core.db (SQLite) |

**Schema files:**
- SQL schemas: `soil-schema.sql`, `core-schema.sql`
- Type schemas: `fact_schemas.json`, `entity_schemas.json`
- Relation specification: RFC-002
- Context mechanism: RFC-003
- Deployment: RFC-004

---

## Consistency Guarantees

MemoGarden provides the following guarantees for decade-long survivability:

### Always-Available Startup

**System starts regardless of database state.** Even with corrupted databases or detected inconsistencies, MemoGarden starts in an appropriate operating mode:

- **NORMAL**: Healthy operation, full read/write capabilities
- **READ-ONLY**: Maintenance/recovery mode, queries only
- **SAFE MODE**: Degraded/inconsistent state, limited operations with diagnostics enabled

The system never refuses to start due to data issues. Operator investigates and resolves problems while system remains available.

### Crash Recovery

**System detects and reports inconsistencies on startup.** MemoGarden performs quick consistency checks during startup:
- Orphaned EntityDeltas (Soil committed, Core did not)
- Broken Entity hash chains
- Dangling relation references
- Database integrity violations

**No guarantee of zero data loss on power failure.** The system prioritizes survivability over preventing rare data loss (~0.01% per year vulnerability window). Operator uses short-term memory to recreate any unwritten data if needed.

### Transaction Atomicity

**Operations within explicit transactions are atomic with best-effort cross-database coordination.** MemoGarden coordinates commits across Soil and Core databases:

- Single-database operations: Standard SQLite ACID guarantees
- Cross-database operations: Best-effort atomicity via application-level coordination
- Rare failures (~0.01%/year) logged and flagged for operator intervention

**Transaction failure modes:**
- Both databases commit successfully: Normal operation
- Both databases fail: Transaction rolled back cleanly
- Soil commits, Core fails: System marked INCONSISTENT, requires `memogarden repair`

See RFC-008 for detailed transaction semantics.

### Data Integrity

**Fact integrity_hash and Entity hash chains detect corruption:**

- **Facts**: SHA256 hash of content fields verified on access
- **Entities**: Cryptographic hash chain enables tamper detection and lineage reconstruction
- **System checks**: `memogarden diagnose` reports all detected integrity issues

**SSD health monitoring:** System agent tracks mission-essential metrics including SSD wear level, reallocated sectors, and temperature. Statistical Process Control (SPC) techniques detect degradation trends before catastrophic failure. Metrics stored in-memory and journald; significant operational events create SystemEvent facts.

### Audit Trail

**All Semantic API operations create Action facts:**
- Unified audit trail for human operators and AI agents
- Captures: actor, operation, parameters, success/failure, timestamp, context
- Includes read operations (searches, queries) and write operations (edits, mutations)
- Failed operations captured alongside successful ones
- Queryable via Semantic API like any other fact

**Three-layer observability:**
1. **MemoGarden facts** (semantic data): Action, EntityDelta, SystemEvent facts
2. **Internal logs** (technical troubleshooting): journald/stderr for stack traces and diagnostics
3. **OS logs** (infrastructure): systemd journal for service lifecycle

**Query examples:**
```python
# Find failed operations
mg.search(filters={"type": "Action", "result": "failure"})

# Trace agent behavior
mg.search(filters={"actor": agent_uuid})
```

See RFC-005 v7 for Action fact schema, RFC-007 v2.1 for system agent architecture.

### Recovery Tools

**Operator-in-the-loop recovery:**

```bash
# Detect issues
memogarden diagnose

# Automated repairs
memogarden repair

# Manual investigation
memogarden debug consistency
```

System provides diagnostic tools and clear error reporting. Operator makes final decisions on recovery actions.

---

## Facts and Entities

MemoGarden distinguishes between two fundamental object types:

| Property | Fact | Entity |
|----------|------|--------|
| **Storage** | Soil | Core |
| **Mutability** | Immutable | Mutable |
| **Change mechanism** | Supersession (new Fact replaces old) | Delta (tracked modifications) |
| **UUID prefix** | `soil_` | `core_` |
| **Examples** | Note, Message, Email, ToolCall, EntityDelta | Artifact, Label, Transaction |
| **Timeline presence** | Yes (appears at a point in time) | No (spans time; deltas appear in timeline) |

### Fact (Base Type)

Facts represent immutable, unchangeable ground truth in the timeline. All changes to Facts create new Facts with supersession links.

**Core properties:**
- **uuid**: Unique identifier with `soil_` prefix
- **_type**: Type discriminator (CamelCase, underscore prefix reserves non-prefixed attributes for user data)
- **realized_at**: When system recorded this (immutable, system time)
- **canonical_at**: When user says it happened (user-controllable, subjective time)
- **integrity_hash**: SHA256 hash for corruption detection
- **fidelity**: Compression state (`full` | `summary` | `stub` | `tombstone`)
- **superseded_by**: UUID of Fact that replaces this one
- **data**: Type-specific fields following standard schemas
- **metadata**: Provider-specific extensions (not validated, rarely indexed)

**Fidelity mechanism** (RFC-002):

| State | Content | Use Case |
|-------|---------|----------|
| `full` | Complete original | Default for new facts |
| `summary` | Compressed representation | LLM or extractive summary |
| `stub` | Minimal metadata only | UUID, timestamps, type preserved |
| `tombstone` | Deleted marker | Deletion under storage pressure |

**Data vs Metadata separation:**

Facts separate standard schema fields (`data`) from provider-specific extensions (`metadata`). This enables:
- Provider plugins without core schema changes
- Clean standard schemas for interoperability
- Debugging data (original headers) without polluting core

### Entity (Base Type)

Entities represent mutable objects with hash-chained version control. All Entity mutations create `EntityDelta` Facts in Soil.

**Core properties:**
- **uuid**: Stable identifier with `core_` prefix
- **_type**: Type discriminator
- **hash**: Current state hash (SHA256 of content + previous_hash)
- **previous_hash**: Hash of prior state (null for initial Entity)
- **version**: Monotonically increasing version number
- **created_at**, **updated_at**: Timestamps
- **group_id**: Optional grouping (references another Entity)
- **superseded_by**: Reclassification to another Entity (soft delete/replacement)
- **derived_from**: Provenance (references Fact or Entity UUID)

**Hash chain properties:**
- Enables full lineage reconstruction
- Optimistic locking via hash comparison
- Tamper detection (recompute chain, verify hashes)

**Example conflict detection:**

```python
def update_entity(uuid: str, new_data: dict, based_on_hash: str) -> Result:
    current = get_entity(uuid)
    
    if current.hash != based_on_hash:
        return Conflict(
            current_hash=current.hash,
            current_version=current.version,
            client_hash=based_on_hash
        )
    
    new_hash = compute_entity_hash(new_data, current.hash)
    update_entity_fields(
        hash=new_hash,
        previous_hash=current.hash,
        version=current.version + 1,
        **new_data
    )
    
    # Record delta in Soil
    create_entity_delta(uuid, new_hash, current.hash, new_data)
    
    return Success(hash=new_hash, version=current.version + 1)
```

---

## Fact Types

All Fact types are defined in `fact_schemas.json`. This section provides usage guidance and examples.

### Note

General-purpose text fact with optional title and summary. Used for capturing thoughts, observations, and unstructured information.

**Key fields:** `description`, `summary`, `title`

### Message

Communication between participants. Extends Note with sender/recipient tracking.

**Key fields:** `description`, `sender`, `recipient`, `subject`

**Usage:** Conversation logs, chat messages, direct communications.

### Email

Email imported from external providers (Gmail, Outlook, mbox). Follows RFC 5322 standard schema.

**Standard schema (data):**
- Message identification: `rfc_message_id` (deduplication key)
- Addresses: `from_address`, `to_addresses`, `cc_addresses`, `bcc_addresses`
- Content: `title` (subject line), `description` (body)
- Timestamps: `sent_at`, `received_at`
- Threading: `in_reply_to`, `references` (RFC 5322 threading)
- Attachments: `has_attachments`, `attachment_count`, `attachment_filenames`

**Provider extensions (metadata):**
- Gmail: `gmail_thread_id`, `gmail_labels`
- Outlook: `outlook_conversation_id`
- Debugging: `html_body`, `original_headers`

**System Relations:** Email import automatically creates `replies_to` relations from `in_reply_to` header.

### ToolCall

Records tool invocations by user or agent. Captures operational history for context and debugging.

**Key fields:** `tool`, `operation`, `params`, `result`, `caller`, `context`

**Usage:** Search events create ToolCall facts that serve as relation signals. Tool execution history enables debugging and provenance tracking.

### EntityDelta

Audit trail for Entity mutations. Records what changed, when, and in what context.

**Key fields:**
- `entity_uuid`: Which Entity this changes (core_ prefix)
- `entity_type`: Type of the Entity
- `commit`: Hash of resulting Entity state after this delta
- `parent`: Parent commit hash(es); null for creation, array for merge
- `ops`: Change description (format depends on entity type)
- `context`: Snapshot of ContextFrame.containers at mutation time (RFC-003)

**Properties:**
- EntityDeltas appear in timeline; Entities do not
- Hash chain enables full history reconstruction
- Context capture links mutations to attention state

### SystemEvent

System-generated notifications and state changes.

**Key fields:** `event_type`, `payload`

**Event types:**
- `entity_created`: Entity creation notification
- `fossilization_sweep`: Background compression cycle
- `fact_fossilized`: Fact compression complete
- `fossilized_fact_accessed`: Access to compressed content
- `integrity_check_failed`: Corruption detection

---

## Entity Types

All Entity types are defined in `entity_schemas.json`. This section provides usage guidance and examples.

### Artifact

Structured document or content object. Lives in Core (mutable, user-controlled).

**Key fields:** `label`, `content`, `content_type`, `label_history`

**Properties:**
- Not in timeline (only EntityDeltas appear in timeline)
- Content types: `text/plain`, `text/markdown`, `application/json`, `text/html`
- Label history enables backward compatibility when names change

**Usage:** Documents, notes, code snippets, structured content that evolves over time.

### Label

Named reference to Facts or Entities. User-created organizational structure.

**Key fields:** `name`, `target_uuid`, `target_type`

**Usage:** Tags, bookmarks, custom categorization. Labels are themselves Entities so their creation/modification is tracked.

### Transaction

Budget/financial transaction entity. Already implemented in `core-schema.sql`.

**Key fields:** `amount`, `currency`, `transaction_date`, `description`, `account`, `category`, `author`, `recurrence_id`, `notes`

**Usage:** Personal finance tracking, budget management, recurring payments.

---

## Relations

Relations represent connections between Facts and Entities. MemoGarden distinguishes between **system relations** (immutable structural facts) and **user relations** (engagement signals that decay over time).

**Full specification in RFC-002.** This section provides an overview only.

### System Relations (Immutable Facts)

System relations encode structural facts. Stored in Soil, never modified, no time-horizon decay.

**Relation kinds:**

| Kind | Meaning | Example |
|------|---------|---------|
| `triggers` | Causal chain | Message ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ EntityDelta |
| `cites` | Reference/quotation | Artifact A ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Artifact B |
| `replies_to` | Email threading | Email A ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Email B (from In-Reply-To) |
| `derives_from` | Synthesis provenance | Summary ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ source documents |
| `contains` | Structural containment | Project ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Artifact |
| `continues` | Branch continuation | ConversationLog ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ parent |
| `supersedes` | Replacement/update | Fact B  Fact A |

**Properties:**
- Created by system (providers, parsers, agents)
- UUID prefix: `soil_`
- Evidence tracking via `Evidence` object
- Culling them would be changing history

### User Relations (Engagement Signals)

User relations encode engagement and attention. Active relations stored in Core, fossilized to Soil when time-horizon expires.

**Relation kinds:**
- `explicit_link`: User-created associations (extensible)

**Time-horizon mechanism:** Each relation has a `time_horizon` (days since epoch) representing estimated relevance endpoint. Relations decay based on Anderson & Schooler's power law of forgetting. See RFC-002 for lifecycle management.

**Properties:**
- UUID prefix: `core_` (active) ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ `soil_` (fossilized)
- Last access updates time-horizon
- Fossilization transfers to Soil when expired
- Operators can extend time-horizons explicitly

### Evidence Object

All relations can include evidence tracking:

```python
@dataclass
class Evidence:
    source: str              # 'soil_stated' | 'user_stated' | 'agent_inferred' | 'system_inferred'
    confidence: float | None # For inferred only (0.0-1.0)
    basis: list[str] | None  # UUIDs of supporting facts/entities
    method: str | None       # For inferred: 'rfc_5322_in_reply_to' | 'nlp_extraction' | etc.
```

---

## Context Capture

MemoGarden maintains mechanisms for tracking attention patterns to understand operator focus and enable effective coordination with AI agents.

**Full specification in RFC-003.** This section provides an overview only.

### Overview

| Stream | What it captures | Storage | Retention |
|--------|-----------------|---------|-----------|
| **Delta-stream** | State mutations | Soil (permanent) | Indefinite |
| **View-stream** | Attention events | Core (ephemeral) | ~24hr or N entries |

### Key Concepts

- **ContextFrame**: LRU set of containers representing current attention state (what's "in focus")
- **View-stream**: Ephemeral ringbuffer capturing what was observed
- **Context capture on mutation**: EntityDelta.context captures ContextFrame snapshot

**Properties:**
- Passive capture (no manual annotation)
- Mutation-time snapshots (not continuous)
- Enables "what was I working on when I changed X?"
- Foundation for relevance computation

**See RFC-003 for complete specification of View, ContextFrame, and context capture rules.**

---

## Data Storage Schema

### SQL Schemas

**Soil Database** (`soil-schema.sql`):
- `fact` table: All Fact types with polymorphic JSON data field
- `system_relation` table: Immutable structural connections
- Indexes optimized for timeline queries

**Core Database** (`core-schema.sql`):
- `entity` table: All Entity types with polymorphic JSON data field
- `user_relation` table: Active engagement signals (time-horizon tracked)
- Type-specific tables where needed (e.g., `transaction` for financial data)
- Indexes optimized for hash verification and version queries

### Design Rationale

**Single polymorphic tables:**

MemoGarden uses one table per storage layer (Fact table in Soil, Entity table in Core) with JSON `data` fields rather than separate tables per type.

**Rationale:**
- Soil is timeline-oriented, not relational
- Provider plugins don't require schema migrations
- Type inheritance is semantic (Python/JSON schemas), not physical (SQL)
- Timeline coherence: chronological queries span all types
- JSON extraction acceptable at personal scale (10k-1M facts)

**Alternative rejected:** Separate tables per type (`fact_email`, `fact_note`) would break timeline coherence and require schema migrations for new providers.

**Data/Metadata separation:**

Facts separate standard schema fields (`data`) from provider-specific extensions (`metadata`).

**Rationale:**
- Clean standard schemas for interoperability
- Validation boundaries (data is validated, metadata is not)
- Provider plugins can add features without core changes
- Debugging information doesn't pollute core queries

### JSON Schema Validation

JSON schemas in `fact_schemas.json` and `entity_schemas.json` serve as authoritative type definitions. Application code should validate against these schemas before writing to database.

**Schema locations:**
- Fact types: `fact_schemas.json` (definitions for Note, Message, Email, ToolCall, EntityDelta, SystemEvent)
- Entity types: `entity_schemas.json` (definitions for Artifact, Label, Transaction)

---

## Provider Plugin Interface

**Conceptual design** (not yet implemented):

```python
class Provider(Protocol):
    """External data source integration."""
    
    def sync(self, since: datetime = None) -> Iterator[Fact]:
        """Fetch facts from source, yield MemoGarden Facts.
        
        Provider translates source_schema ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ standard_schema ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Fact.
        MemoGarden validates and inserts.
        """
        
    def create_relations(self, fact: Fact) -> list[SystemRelation]:
        """Optional: create system relations from provider metadata.
        
        Example: Email provider reads in_reply_to from fact.data,
        creates replies_to relations between emails.
        """
```

**Provider responsibilities:**
- Populate Fact base fields (uuid, _type, realized_at, canonical_at)
- Conform to standard schema for known types (Email = RFC 5322)
- Separate standard fields (`data`) from provider-specific (`metadata`)
- Create system relations for semantic links (threading, references)

**MemoGarden Core responsibilities:**
- Define and validate standard schemas
- Store Facts and Relations
- Does NOT know provider-specific schemas

---

## Fossilization

MemoGarden implements background compression of old Facts to manage storage on resource-constrained hardware.

**Full specification in RFC-002.** Key concepts:

### Mechanism

Facts transition through fidelity states:
```
full ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ summary ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ stub ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ tombstone
```

### Triggers

1. **Storage pressure**: Disk usage exceeds threshold
2. **Time-based decay**: Anderson & Schooler power law of forgetting
3. **Manual override**: Operator can force compression/protection

### Access patterns

- **Fossilized fact accessed**: Creates SystemEvent, may reverse compression
- **Protected facts**: Operators can mark facts as permanent full fidelity

### Relation lifecycle

User relations fossilize when time-horizon expires, transferring from Core to Soil. System relations never fossilize.

---

## Configuration

```python
@dataclass
class MemoGardenConfig:
    soil_db_path: str = 'soil.db'
    core_db_path: str = 'core.db'
    verify_hash_on_read: bool = True
    undo_window_seconds: int = 300  # 5 minutes

@dataclass
class FossilizationConfig:
    """See RFC-002 for full specification."""
    safety_coefficient: float = 1.2
    sweep_interval_hours: int = 24
    summary_method: str = 'extractive'
    summary_max_tokens: int = 200
    storage_pressure_threshold_pct: float = 85.0
    eviction_target_free_pct: float = 20.0

@dataclass
class ContextConfig:
    """See RFC-003 for full specification."""
    max_containers_per_frame: int = 20
    view_ringbuffer_size: int = 1000
    view_retention_hours: int = 24

@dataclass
class EncryptionConfig:
    """See RFC-001 for full specification."""
    enabled: bool = False
    algorithm: str = 'AES-256-GCM'
```

---

## Security Model

**Full specification in RFC-001.** Key principles:

### Encryption at Rest

- SQLCipher for database encryption
- Shamir's Secret Sharing for key recovery (split among trusted parties)
- Hardware security module integration (optional)

### Agent Coordination

- Zero private state for agents (all operations through shared tools)
- Explicit control locks for human oversight
- Observe/Approve modes for sensitive operations

### Privacy

- Local-first: Data stays on operator's hardware by default
- Cloud sync optional, end-to-end encrypted
- No telemetry without explicit consent

---

## Implementation Status

**Completed:**
- Core schema design (v0.10.0)
- JSON type schemas
- SQL database schemas
- RFC-001 (Security Operations)
- RFC-002 (Relations and Time-Horizon)
- RFC-003 (Context Mechanism)
- RFC-004 (Package Deployment)

**In Progress:**
- Provider interface implementation
- Fossilization engine
- Context capture mechanism

**Planned:**
- Android app for comprehensive data capture
- Staging area architecture (external information processing)
- Protective agents (toxic/sensitive content handling)
- Project Studio integration

---

## References

### Related Documents

- **RFCs:**
  - RFC-001: Security Operations (encryption, access control, key management)
  - RFC-002: Relations and Time-Horizon (fossilization, lifecycle management)
  - RFC-003: Context Mechanism (attention tracking, ContextFrame)
  - RFC-004: Package Deployment (schema versioning, migration)

- **Schemas:**
  - `soil-schema.sql`: Soil database structure
  - `core-schema.sql`: Core database structure
  - `fact_schemas.json`: JSON schemas for all Fact types
  - `entity_schemas.json`: JSON schemas for all Entity types

- **Whitepapers:**
  - Time-Horizon Mechanism (cognitive science foundations)
  - Joint Cognitive Environments (human-AI collaboration model)

### Research Foundations

- Anderson & Schooler: "Reflections of the Environment in Memory" (power law of forgetting)
- Stafford Beer: Viable System Model (cybernetics principles)
- Alexander Obenauer: Personal computing concepts
- Human-factors research on automation handover failures

---

## Appendix: UUID Conventions

MemoGarden uses prefixed UUIDs to distinguish object types:

| Prefix | Storage | Mutability | Examples |
|--------|---------|------------|----------|
| `soil_` | Soil (timeline) | Immutable | Facts, fossilized relations |
| `core_` | Core (state) | Mutable | Entities, active relations |

**Format:** `{prefix}_{uuid4}`

**Examples:**
- `soil_a1b2c3d4-e5f6-7890-abcd-ef1234567890` (Fact)
- `core_f9e8d7c6-b5a4-3210-fedc-ba9876543210` (Entity)

This prefix scheme enables:
- Type identification from UUID alone
- Storage layer determination
- Collision prevention across layers
- Clear documentation of object lifecycle
