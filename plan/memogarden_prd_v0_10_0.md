# MemoGarden Product Requirements Document

**Version:** 0.10.0  
**Date:** 2025-01-31  
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
- Type schemas: `item_schemas.json`, `entity_schemas.json`
- Relation specification: RFC-002
- Context mechanism: RFC-003
- Deployment: RFC-004

---

## Items and Entities

MemoGarden distinguishes between two fundamental object types:

| Property | Item | Entity |
|----------|------|--------|
| **Storage** | Soil | Core |
| **Mutability** | Immutable | Mutable |
| **Change mechanism** | Supersession (new Item replaces old) | Delta (tracked modifications) |
| **UUID prefix** | `soil_` | `core_` |
| **Examples** | Note, Message, Email, ToolCall, EntityDelta | Artifact, Label, Transaction |
| **Timeline presence** | Yes (appears at a point in time) | No (spans time; deltas appear in timeline) |

### Item (Base Type)

Items represent immutable facts in the timeline. All changes to Items create new Items with supersession links.

**Core properties:**
- **uuid**: Unique identifier with `soil_` prefix
- **_type**: Type discriminator (CamelCase, underscore prefix reserves non-prefixed attributes for user data)
- **realized_at**: When system recorded this (immutable, system time)
- **canonical_at**: When user says it happened (user-controllable, subjective time)
- **integrity_hash**: SHA256 hash for corruption detection
- **fidelity**: Compression state (`full` | `summary` | `stub` | `tombstone`)
- **superseded_by**: UUID of Item that replaces this one
- **data**: Type-specific fields following standard schemas
- **metadata**: Provider-specific extensions (not validated, rarely indexed)

**Fidelity mechanism** (RFC-002):

| State | Content | Use Case |
|-------|---------|----------|
| `full` | Complete original | Default for new items |
| `summary` | Compressed representation | LLM or extractive summary |
| `stub` | Minimal metadata only | UUID, timestamps, type preserved |
| `tombstone` | Deleted marker | Deletion under storage pressure |

**Data vs Metadata separation:**

Items separate standard schema fields (`data`) from provider-specific extensions (`metadata`). This enables:
- Provider plugins without core schema changes
- Clean standard schemas for interoperability
- Debugging data (original headers) without polluting core

### Entity (Base Type)

Entities represent mutable objects with hash-chained version control. All Entity mutations create `EntityDelta` Items in Soil.

**Core properties:**
- **uuid**: Stable identifier with `core_` prefix
- **_type**: Type discriminator
- **hash**: Current state hash (SHA256 of content + previous_hash)
- **previous_hash**: Hash of prior state (null for initial Entity)
- **version**: Monotonically increasing version number
- **created_at**, **updated_at**: Timestamps
- **group_id**: Optional grouping (references another Entity)
- **superseded_by**: Reclassification to another Entity (soft delete/replacement)
- **derived_from**: Provenance (references Item or Entity UUID)

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

## Item Types

All Item types are defined in `item_schemas.json`. This section provides usage guidance and examples.

### Note

General-purpose text item with optional title and summary. Used for capturing thoughts, observations, and unstructured information.

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

**Usage:** Search events create ToolCall items that serve as relation signals. Tool execution history enables debugging and provenance tracking.

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
- `item_fossilized`: Item compression complete
- `fossilized_item_accessed`: Access to compressed content
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

Named reference to Items or Entities. User-created organizational structure.

**Key fields:** `name`, `target_uuid`, `target_type`

**Usage:** Tags, bookmarks, custom categorization. Labels are themselves Entities so their creation/modification is tracked.

### Transaction

Budget/financial transaction entity. Already implemented in `core-schema.sql`.

**Key fields:** `amount`, `currency`, `transaction_date`, `description`, `account`, `category`, `author`, `recurrence_id`, `notes`

**Usage:** Personal finance tracking, budget management, recurring payments.

---

## Relations

Relations represent connections between Items and Entities. MemoGarden distinguishes between **system relations** (immutable structural facts) and **user relations** (engagement signals that decay over time).

**Full specification in RFC-002.** This section provides an overview only.

### System Relations (Immutable Facts)

System relations encode structural facts. Stored in Soil, never modified, no time-horizon decay.

**Relation kinds:**

| Kind | Meaning | Example |
|------|---------|---------|
| `triggers` | Causal chain | Message → EntityDelta |
| `cites` | Reference/quotation | Artifact A → Artifact B |
| `replies_to` | Email threading | Email A → Email B (from In-Reply-To) |
| `derives_from` | Synthesis provenance | Summary → source documents |
| `contains` | Structural containment | Project → Artifact |
| `continues` | Branch continuation | ConversationLog → parent |
| `supersedes` | Replacement/update | Item B → Item A |

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
- UUID prefix: `core_` (active) → `soil_` (fossilized)
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
    basis: list[str] | None  # UUIDs of supporting items/entities
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
- `item` table: All Item types with polymorphic JSON data field
- `system_relation` table: Immutable structural connections
- Indexes optimized for timeline queries

**Core Database** (`core-schema.sql`):
- `entity` table: All Entity types with polymorphic JSON data field
- `user_relation` table: Active engagement signals (time-horizon tracked)
- Type-specific tables where needed (e.g., `transaction` for financial data)
- Indexes optimized for hash verification and version queries

### Design Rationale

**Single polymorphic tables:**

MemoGarden uses one table per storage layer (Item table in Soil, Entity table in Core) with JSON `data` fields rather than separate tables per type.

**Rationale:**
- Soil is timeline-oriented, not relational
- Provider plugins don't require schema migrations
- Type inheritance is semantic (Python/JSON schemas), not physical (SQL)
- Timeline coherence: chronological queries span all types
- JSON extraction acceptable at personal scale (10k-1M items)

**Alternative rejected:** Separate tables per type (`item_email`, `item_note`) would break timeline coherence and require schema migrations for new providers.

**Data/Metadata separation:**

Items separate standard schema fields (`data`) from provider-specific extensions (`metadata`).

**Rationale:**
- Clean standard schemas for interoperability
- Validation boundaries (data is validated, metadata is not)
- Provider plugins can add features without core changes
- Debugging information doesn't pollute core queries

### JSON Schema Validation

JSON schemas in `item_schemas.json` and `entity_schemas.json` serve as authoritative type definitions. Application code should validate against these schemas before writing to database.

**Schema locations:**
- Item types: `item_schemas.json` (definitions for Note, Message, Email, ToolCall, EntityDelta, SystemEvent)
- Entity types: `entity_schemas.json` (definitions for Artifact, Label, Transaction)

---

## Provider Plugin Interface

**Conceptual design** (not yet implemented):

```python
class Provider(Protocol):
    """External data source integration."""
    
    def sync(self, since: datetime = None) -> Iterator[Item]:
        """Fetch items from source, yield MemoGarden Items.
        
        Provider translates source_schema → standard_schema → Item.
        MemoGarden validates and inserts.
        """
        
    def create_relations(self, item: Item) -> list[SystemRelation]:
        """Optional: create system relations from provider metadata.
        
        Example: Email provider reads in_reply_to from item.data,
        creates replies_to relations between emails.
        """
```

**Provider responsibilities:**
- Populate Item base fields (uuid, _type, realized_at, canonical_at)
- Conform to standard schema for known types (Email = RFC 5322)
- Separate standard fields (`data`) from provider-specific (`metadata`)
- Create system relations for semantic links (threading, references)

**MemoGarden Core responsibilities:**
- Define and validate standard schemas
- Store Items and Relations
- Does NOT know provider-specific schemas

---

## Fossilization

MemoGarden implements background compression of old Items to manage storage on resource-constrained hardware.

**Full specification in RFC-002.** Key concepts:

### Mechanism

Items transition through fidelity states:
```
full → summary → stub → tombstone
```

### Triggers

1. **Storage pressure**: Disk usage exceeds threshold
2. **Time-based decay**: Anderson & Schooler power law of forgetting
3. **Manual override**: Operator can force compression/protection

### Access patterns

- **Fossilized item accessed**: Creates SystemEvent, may reverse compression
- **Protected items**: Operators can mark items as permanent full fidelity

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
  - `item_schemas.json`: JSON schemas for all Item types
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
| `soil_` | Soil (timeline) | Immutable | Items, fossilized relations |
| `core_` | Core (state) | Mutable | Entities, active relations |

**Format:** `{prefix}_{uuid4}`

**Examples:**
- `soil_a1b2c3d4-e5f6-7890-abcd-ef1234567890` (Item)
- `core_f9e8d7c6-b5a4-3210-fedc-ba9876543210` (Entity)

This prefix scheme enables:
- Type identification from UUID alone
- Storage layer determination
- Collision prevention across layers
- Clear documentation of object lifecycle
