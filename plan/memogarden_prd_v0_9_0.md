# MemoGarden Personal Information System - Product Requirements Document

**Version:** 0.9.0  
**Status:** Draft  
**Last Updated:** 2025-01-30

## Overview

MemoGarden is a personal information substrate designed for long-term data preservation with human-AI collaboration. It provides a two-layer storage architecture separating immutable facts (Soil) from mutable beliefs (Core), with relations between objects carrying significance that decays over time.

MemoGarden serves as the **data substrate**; agent runtimes like Letta serve as the **execution layer**. Agent memory blocks are projections (views) into MemoGarden data, not authoritative storage. All agent writes go through tools and are recorded in Soil, ensuring complete audit trails.

**Provider plugins** integrate external data sources (Gmail, Outlook, file systems) by translating source schemas to MemoGarden's standard schemas and creating appropriate Items and Relations.

---

## Core Principles

1. **Immutable Timeline**: Items in Soil cannot be retroactively changed (short undo window excepted)
2. **Mutable Beliefs**: Entities in Core evolve via tracked deltas
3. **UUID-Based Identity**: Stable identifiers enable relabeling without breaking references
4. **Joint Cognitive System**: User and agent share tools, observe each other's work, coordinate as single cognitive unit
5. **Explicit Causation**: Relations enable audit trails and retrace capabilities
6. **Time-Based Significance**: Relations decay naturally; items fossilize when significance expires
7. **Store Everything, Decay Most Things**: Comprehensive capture; access patterns determine persistence
8. **Provider Plugin Architecture**: External sources translate to standard schemas; Core remains source-agnostic
9. **Indexes as Derived Data**: Always rebuildable from Item content; enables schema-driven index generation

---

## Architectural Context

### Letta ↔ MemoGarden Relationship

| Layer | Role | Responsibility |
|-------|------|----------------|
| **Letta** | Execution runtime | Agent inference, memory block management, tool execution |
| **MemoGarden** | Data substrate | Persistent storage, audit trail, fossilization, relations |

**Key implications:**
- Memory blocks are **projections** into MemoGarden data, not authoritative storage
- Agent writes go through tools → recorded as Items in Soil
- Agents have minimal private state; work products feed back into MemoGarden
- "Personal memory" for agents = MemoGarden data with ACL (agent+operator write, others read)
- Memory blocks are bounded; tools provided for browsing/scrolling beyond block limits

### Provider Plugin Architecture

**Providers** integrate external data sources by:
1. **Fetching** data from source (Gmail API, mbox files, filesystem)
2. **Translating** source schema to MemoGarden standard schema (RFC 5322 for Email)
3. **Creating** Items via MemoGarden API
4. **Establishing** System Relations from source metadata (threading, references)

**MemoGarden Core**:
- Defines standard schemas (Email, Message, Note)
- Validates Items against schemas
- Stores Items and Relations
- Does NOT know provider-specific schemas (Gmail thread IDs, Outlook categories)

---

## Storage Architecture

MemoGarden uses a two-layer storage model separating immutable facts from mutable state.

### UUID Systems

MemoGarden uses **two separate UUID namespaces** by storage origin:

| System | UUID Prefix | Database | Mutability | Examples |
|--------|-------------|----------|------------|----------|
| **Soil** | `soil_` | Soil DB | Immutable | `soil_abc123...`, `soil_def456...` |
| **Core** | `core_` | Core DB | Mutable | `core_xyz789...`, `core_uvw012...` |

### Soil (Immutable Facts)

**Purpose:** Ground truth timeline of what happened

**Contents:**
- All Items (Notes, Messages, Emails, ToolCalls, EntityDeltas, etc.)
- System Relations (immutable structural facts)
- Fossilized User Relations (append-only once fossilized)

**Properties:**
- **Immutable**: Once realized, Items cannot be modified (5-minute undo window for mistakes)
- **Append-only**: New facts add to history, never replace
- **Timestamped**: Both `realized_at` (system time) and `canonical_at` (user-controlled time)
- **Supersession**: Items may be superseded by newer Items, but the original remains
- **Timeline-first**: Single polymorphic `item` table preserves chronological coherence

**Implementation:** See `soil-schema.sql` for complete schema specification.

### Core (Mutable State)

**Purpose:** User-controlled belief layer and evolving objects

**Contents:**
- Entities (mutable objects with delta-tracked changes)
- Active User Relations (mutable until fossilized)
- ContextFrames (attention tracking, per RFC-003)
- User belief overrides about Soil items
- Relation time horizons and last access timestamps
- Labels and organizational metadata

**Properties:**
- **Mutable**: Entity content can be edited
- **Delta-tracked**: All Entity changes recorded as EntityDelta Items in Soil
- **User-sovereign**: User beliefs override inferred/imported facts
- **Lifecycle-aware**: User relations fossilize from Core to Soil when time horizon expires (per RFC-002)
- **Hash chains**: Entities maintain cryptographic hash chains for version tracking and conflict detection

**Implementation:** See `core-schema.sql` for complete schema specification.

---

## Items and Entities

MemoGarden distinguishes between two fundamental object types:

| Property | Item | Entity |
|----------|------|--------|
| **Storage** | Soil | Core |
| **Mutability** | Immutable | Mutable |
| **Change mechanism** | Supersession (new Item replaces old) | Delta (tracked modifications) |
| **UUID prefix** | `soil_` | `core_` |
| **Examples** | Note, Message, Email, ToolCall, EntityDelta | Artifact, Label, Tag |
| **Timeline presence** | Yes (appears at a point in time) | No (spans time; deltas appear in timeline) |

### Item (Base Type)

**Purpose:** Base type for all timeline entries in Soil

**Core fields:**
```python
@dataclass
class Item:
    uuid: str                   # soil_ + uuid4
    _type: str                  # 'Note', 'Message', 'Email', 'ToolCall', 'EntityDelta', etc.
    realized_at: datetime       # When system recorded this
    canonical_at: datetime      # When user says it happened
    integrity_hash: str | None  # SHA256 for corruption detection
    fidelity: str               # 'full' | 'summary' | 'stub' | 'tombstone'
    superseded_by: str | None   # UUID of superseding Item
    superseded_at: datetime | None
    data: dict                  # Type-specific fields (standard schema)
    metadata: dict              # Provider-specific extensions
```

**Fidelity States:**

| State | Content | Use Case |
|-------|---------|----------|
| `full` | Complete original | Default for new items |
| `summary` | Compressed representation | LLM or extractive summary |
| `stub` | Minimal metadata only | UUID, timestamps, type preserved |
| `tombstone` | Deleted marker | Deletion under storage pressure |

**Data vs Metadata Separation:**

| Field | Purpose | Validated | Indexed |
|-------|---------|-----------|---------|
| **data** | Standard schema fields (RFC 5322 for Email) | Yes | Yes (functional indexes) |
| **metadata** | Provider-specific extensions (Gmail thread ID) | No | Rarely |

This separation enables:
- Provider plugins without core schema changes
- Clean standard schemas for interoperability
- Debugging data (original headers) without polluting core

### Entity (Base Type)

**Purpose:** Base type for all mutable objects in Core

**Core fields:**
```python
@dataclass
class Entity:
    uuid: str                   # core_ + uuid4
    _type: str                  # 'Artifact', 'Label', 'Tag', etc.
    hash: str                   # SHA256(content + previous_hash)
    previous_hash: str | None   # Hash of prior state (None for initial)
    version: int                # Monotonically increasing
    created_at: datetime
    updated_at: datetime
    group_id: str | None        # Optional grouping
    superseded_by: str | None   # Reclassification to another Entity
    superseded_at: datetime | None
    derived_from: str | None    # Provenance
```

**Hash Chain Properties:**
- Enables full lineage reconstruction
- Optimistic locking via hash comparison
- Tamper detection (recompute chain, verify hashes)

---

## Item Types

### Note
General-purpose text item with `description`, optional `summary`, optional `title`.

### Message
Communication between participants. Extends Note with `sender`, `recipient`, `subject`.

### Email
Email imported from external provider (Gmail, Outlook, mbox).

**Standard Schema (RFC 5322):**
- **data**: `rfc_message_id` (deduplication key), `from_address`, `to_addresses`, `subject`, `sent_at`, `description` (body), `in_reply_to`, `references` (threading), `has_attachments`, `attachment_filenames`
- **metadata**: Provider-specific (`gmail_thread_id`, `labels`, `html_body`, `original_headers`)

**System Relations:** `replies_to` relations created automatically from `in_reply_to` header during import.

**See Email Import Review (2025-01-30) for implementation details.**

### ToolCall
Record of tool invocation by user or agent. Fields: `tool`, `operation`, `params`, `result`, `caller`, `context`.

**Search events** create ToolCall items that serve as relation signals.

### EntityDelta
Records change to an Entity (audit trail for Core mutations). Fields: `entity_uuid`, `entity_type`, `commit`, `parent`, `ops`, `context` (ContextFrame snapshot).

### SystemEvent
System-generated notifications. Fields: `event_type`, `payload`.

---

## Entity Types

### Artifact
Structured document or content object. Fields: `label`, `content`, `content_type`, `label_history`.

Lives in Core (mutable). Not in timeline; only EntityDeltas appear in timeline.

### Label
Named reference to Items or Entities. Fields: `name`, `target_uuid`, `target_type`.

---

## Relations

Relations represent connections between Items and Entities. MemoGarden distinguishes between **system relations** (immutable structural facts) and **user relations** (engagement signals that decay over time).

**Full specification in RFC-002.**

### System Relations (Immutable Facts)

```python
@dataclass
class SystemRelation:
    uuid: str               # soil_ prefix
    kind: str               # 'triggers' | 'cites' | 'replies_to' | 'derives_from' | 'contains' | 'continues' | 'supersedes'
    source: str
    source_type: str        # 'item' | 'entity'
    target: str
    target_type: str
    created_at: int         # Days since epoch (2020-01-01)
    evidence: Evidence | None
    metadata: dict | None
```

**Kinds:**
- **triggers**: Causal chain (Message → ArtifactDelta)
- **cites**: Reference/quotation (Artifact A → Artifact B)
- **replies_to**: Email threading (Email A → Email B from In-Reply-To header)
- **derives_from**: Synthesis provenance (Summary → sources)
- **contains**: Structural containment (Project → Artifact)
- **continues**: Branch continuation (ConversationLog → parent)
- **supersedes**: Replacement/update (Item B → Item A)

### User Relations (Engagement Signals)

```python
@dataclass
class UserRelation:
    uuid: str               # core_ prefix (becomes soil_ on fossilization)
    kind: str               # 'explicit_link' (extensible)
    source: str
    source_type: str
    target: str
    target_type: str
    time_horizon: int       # Days since epoch
    last_access_at: int     # Days since epoch
    created_at: int
    evidence: Evidence | None
    metadata: dict | None
```

**Time horizon mechanism:** See RFC-002 for fossilization rules and lifecycle management.

### Evidence Object

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

**Full specification in RFC-003.**

### Overview

| Stream | What it captures | Storage | Retention |
|--------|-----------------|---------|-----------|
| **Delta-stream** | State mutations | Soil (permanent) | Indefinite |
| **View-stream** | Attention events | Core (ephemeral) | ~24hr or N entries |

### Key Concepts

- **ContextFrame**: LRU set of containers representing current attention state (max 20, configurable)
- **View-stream**: Ephemeral ringbuffer capturing what was observed
- **Context capture on mutation**: `EntityDelta.context` captures ContextFrame snapshot at mutation time

This enables answering "what was I looking at when I made this change?" for retrospective co-access analysis.

---

## Search and Indexing

### Search as Relation Signal

Search queries reveal missing relations. When a user searches and selects a result:

1. **ToolCall created**: Records query, selected item
2. **Relation created**: Current focus → selected item (`explicit_link`)
3. **Significance boost**: Update time horizon for selected item
4. **Pattern learning**: High semantic similarity may trigger auto-relation creation

### Indexing Strategy

**Current approach:** SQLite functional indexes on JSON fields for critical queries.

**Future approach:** Separate index layer (possibly Rust) with schema-driven generation:
- Hash tables for exact match (rfc_message_id → uuid)
- Tries for prefix search (sender autocomplete)
- Inverted indexes for full-text search
- Vector indexes (sqlite-vec) for semantic search

**Key principle:** Indexes are **derived data**, always rebuildable from Item content.

**Migration path:** Functional indexes → separate index layer without schema changes.

### Progressive Enhancement

1. **Phase 1**: Linear scan (sufficient for 10k items)
2. **Phase 2**: Hash indexes (sender/recipient lookups)
3. **Phase 3**: Vector search (semantic body search via sqlite-vec)
4. **Phase 4**: Full-text indexes (subject/body inverted index)

**Deferred until search is implemented.** Current schema supports all approaches without modification.

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
```

---

## Design Rationale

### Single Polymorphic Item Table

**Decision:** All Item types share one table with JSON `data` field.

**Rationale:**
- Soil is **timeline-oriented**, not relational database
- Provider plugins shouldn't require core schema migrations
- Item inheritance is semantic (Python dataclasses), not physical (SQL tables)
- Timeline coherence: chronological queries span all types
- JSON extraction acceptable at personal scale (10k-1M items)

**Alternative rejected:** Separate tables per type (`item_email`, `item_note`) would break timeline coherence and require schema migrations for new providers.

### Data/Metadata Separation

**Decision:** Standard schema fields in `data`, provider-specific in `metadata`.

**Rationale:**
- Clear boundary between "what MemoGarden knows" and "what providers know"
- Standard schemas enable interoperability (RFC 5322 for Email works everywhere)
- Provider extensions don't pollute core
- Debugging data (original headers, raw responses) has natural home
- Validation applies only to standard schema

### Indexes as Derived Data

**Decision:** Indexes are rebuildable from Item content; start with functional indexes, migrate to separate layer when needed.

**Rationale:**
- Functional indexes: simple, automatically maintained, SQLite built-in
- Separate index layer: more control, better performance at scale (>1M items)
- Either approach works; schema unchanged
- Defer optimization until performance requires it
- Schema-driven index generation enables rebuilds without manual specification

### Provider Plugin Architecture

**Decision:** Providers translate external schemas to MemoGarden standard schemas; Core is provider-agnostic.

**Rationale:**
- MemoGarden shouldn't know Gmail API vs Outlook API
- Standard schemas (RFC 5322) enable cross-provider compatibility
- Email from Gmail and mbox import have identical structure
- Providers handle source-specific quirks (pagination, rate limits, auth)
- New providers don't require Core changes

---

## Identified Gaps

### Gap 1: Explicit Linking UX
How operator creates explicit user relations. **Status:** Unresolved.

### Gap 2: Relation Inheritance on Item Edit
When item B references item A, does system relation (cites) get created automatically? **Status:** Unresolved.

### Gap 3: Cascading Effects
When item A is deleted, what happens to relations where A is source/target? **Status:** Unresolved.

### Gap 4: Bulk Import Initial Significance
How to set initial time horizons for bulk imported items. **Status:** Partially resolved (start cold, prove worth through access; provider labels may influence initial horizon).

### Gap 5: Resurrection Depth
When fossilized item is accessed, should it be fully restored or remain compressed? **Status:** Partially resolved (remain compressed; new user relations accumulate).

### Gap 6: HTML-Only Email Handling
Strategy for emails with no plain text body. **Status:** Options identified (store HTML with content_type flag, or convert to plain text).

### Gap 7: Email Significance by Type
Should sent emails (from=operator) have different decay than received? **Status:** Deferred (treat equally initially).

---

## Open Questions

1. **Initial time horizon for new user relations:** What value? `current_day() + 7`?
2. **Relation pruning:** Delete user relations far past horizon, or keep indefinitely in Soil?
3. **Orphan handling:** Items with no relations. Fossilize immediately, or wait?
4. **Summary quality:** Extractive (fast) vs LLM-generated (better but costly)? Hybrid by item type?
5. **Per-type decay rates:** Should emails decay faster than documents? Uniform treatment?
6. **Search result selection threshold:** When does search selection warrant automatic relation creation? Semantic similarity > 0.7?
7. **Attachment storage:** Store binaries as separate items with `contained_by` relations, or metadata only?

---

## Implementation References

| Document | Scope |
|----------|-------|
| **soil-schema.sql** | Soil database schema (Items, System Relations, indexes, queries) |
| **core-schema.sql** | Core database schema (Entities, User Relations, ContextFrames) |
| **RFC-001 v4** | Security architecture, deployment profiles, encryption |
| **RFC-002 v5** | Time horizon mechanism, fossilization, relation lifecycle |
| **RFC-003 v2** | Context capture, View-stream, ContextFrame |
| **JCE Whitepaper v1.0** | Interaction model, utilities, studios |
| **Project Studio Spec v0.4.0** | Project-specific structures and workflows |
| **Email Import Review (2025-01-30)** | Email schema, threading, provider architecture |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 - 0.7.0 | 2025-12-26 to 2025-01-29 | [Previous revisions, see v0.7.0] |
| 0.8.0 | 2025-01-30 | Email architecture, provider plugins, indexing strategy |
| 0.9.0 | 2025-01-30 | **Streamlined**: Moved SQL schemas to separate files; condensed to architecture and design decisions; ~50% shorter; added design rationale section |

---

**Status:** Draft  
**Next Steps:** 
1. Implement email import with data/metadata separation
2. Create threading relations from RFC 5322 headers
3. Define initial time horizon policy for imported items

---

**END OF DOCUMENT**
