# MemoGarden Personal Information System - Product Requirements Document

**Version:** 0.7.0  
**Status:** Draft  
**Last Updated:** 2025-01-29

## Overview

MemoGarden is a personal information substrate designed for long-term data preservation with human-AI collaboration. It provides a two-layer storage architecture separating immutable facts (Soil) from mutable beliefs (Core), with relations between objects that carry significance decaying over time.

MemoGarden serves as the **data substrate**; agent runtimes like Letta serve as the **execution layer**. Agent memory blocks are projections (views) into MemoGarden data, not authoritative storage. All agent writes go through tools and are recorded in Soil, ensuring complete audit trails.

## Core Principles

1. **Immutable Timeline**: Items in Soil cannot be retroactively changed (short undo window excepted)
2. **Mutable Beliefs**: Entities in Core evolve via tracked deltas
3. **UUID-Based Identity**: Stable identifiers enable relabeling without breaking references
4. **Joint Cognitive System**: User and agent share tools, observe each other's work, and coordinate as a single cognitive unit
5. **Explicit Causation**: Relations enable audit trails and retrace capabilities
6. **Time-Based Significance**: Relations decay naturally; items fossilize when significance expires
7. **Store Everything, Decay Most Things**: Comprehensive capture; access patterns determine persistence

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

---

## Storage Architecture

MemoGarden uses a two-layer storage model separating immutable facts from mutable state.

### UUID Systems

MemoGarden uses **two separate UUID namespaces** by storage origin:

| System | UUID Prefix | Database | Mutability | Examples |
|--------|-------------|----------|------------|----------|
| **Soil** | `soil_` | Soil DB | Immutable | `soil_abc123...`, `soil_def456...` |
| **Core** | `core_` | Core DB | Mutable | `core_xyz789...`, `core_uvw012...` |

**UUID Format:**
```
soil_<uuid4>    # e.g., soil_a1b2c3d4-e5f6-7890-abcd-ef1234567890
core_<uuid4>    # e.g., core_fedcba98-7654-3210-fedc-ba9876543210
```

### Soil (Immutable Facts)

**Purpose:** Ground truth timeline of what happened

**Contents:**
- All Items (Notes, Messages, ToolCalls, EntityDeltas, etc.)
- System Relations (immutable structural facts)
- Fossilized User Relations (append-only once fossilized)

**Properties:**
- **Immutable**: Once realized, Items cannot be modified (5-minute undo window for mistakes)
- **Append-only**: New facts add to history, never replace
- **Timestamped**: Both `realized_at` (system time) and `canonical_at` (user-controlled time)
- **Supersession**: Items may be superseded by newer Items, but the original remains

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

---

## Items and Entities

MemoGarden distinguishes between two fundamental object types:

| Property | Item | Entity |
|----------|------|--------|
| **Storage** | Soil | Core |
| **Mutability** | Immutable | Mutable |
| **Change mechanism** | Supersession (new Item replaces old) | Delta (tracked modifications) |
| **UUID prefix** | `soil_` | `core_` |
| **Examples** | Note, Message, ToolCall, EntityDelta | Artifact, Label, Tag |
| **Timeline presence** | Yes (appears at a point in time) | No (spans time; deltas appear in timeline) |

### Item (Base Type)

**Purpose:** Base type for all timeline entries in Soil

**Schema:**
```python
@dataclass
class Item:
    uuid: str               # Stable identifier (soil_ prefix)
    _type: str              # CamelCase, system-managed (e.g., 'Note', 'Message', 'ToolCall')
    realized_at: datetime   # When system recorded this item (immutable)
    canonical_at: datetime  # When user says it happened (user-controllable)
    integrity_hash: str | None  # SHA256 of content fields, verified on access
    fidelity: str           # 'full' | 'summary' | 'stub' | 'tombstone'
    superseded_by: str | None   # UUID of superseding Item, if any
    superseded_at: datetime | None  # When supersession occurred
```

**Properties:**
- **UUID identity**: Each Item has a unique, stable identifier with `soil_` prefix
- **Explicit typing**: `_type` field uses underscore prefix to reserve non-prefixed attributes for user use
- **Dual timestamps**: System records both objective and subjective time
- **Immutable in Soil**: Once realized, Items are permanent (modulo short undo window)
- **Integrity verification**: `integrity_hash` enables on-access corruption detection
- **Fidelity tracking**: Indicates compression state for degraded items
- **Supersession**: Items can be logically replaced while preserving history

**Fidelity States:**

| State | Content | References | Notes |
|-------|---------|------------|-------|
| `full` | Complete original | Intact | Default for new items |
| `summary` | Compressed representation | Intact | LLM or extractive summary |
| `stub` | Minimal metadata only | Intact | UUID, timestamps, type preserved |
| `tombstone` | Deleted marker | May be broken | For deletion under storage pressure |

**Type Naming Convention:**
- Use CamelCase for `_type` values (e.g., `Note`, `Message`, `ToolCall`, `EntityDelta`)
- Same representation in UI and backend for consistency

**Reserved Attribute Names:**

```python
RESERVED_ITEM_ATTRIBUTES = [
    # Relation denormalization (future)
    'triggered_by', 'superseded_by', 'replies_to', 'derived_from',
    'continues_from', 'contained_by',
    # System fields
    'integrity_hash', 'fidelity', 'fossilized_at', 'agent_authored', 'evidence',
]
```

### Entity (Base Type)

**Purpose:** Base type for all mutable objects in Core

**Schema:**
```python
@dataclass
class Entity:
    uuid: str                       # Stable identifier (core_ prefix, never changes)
    _type: str                      # Entity type (e.g., 'Artifact', 'Label')
    hash: str                       # Current state hash (SHA256)
    previous_hash: str | None       # Previous state hash (None for initial)
    version: int                    # Monotonically increasing (for ordering/display)
    created_at: datetime            # Entity creation timestamp
    updated_at: datetime            # Last update timestamp
    
    # Common metadata
    group_id: str | None            # Optional grouping
    superseded_by: str | None       # Reclassification to another Entity
    superseded_at: datetime | None
    derived_from: str | None        # Provenance
```

**Properties:**
- **UUID identity**: Each Entity has a unique, stable identifier with `core_` prefix
- **Hash chain**: Current state hash links to previous, enabling full lineage reconstruction
- **Delta-tracked**: Every modification creates an EntityDelta Item in Soil
- **Conflict detection**: Optimistic locking via hash comparison

**Hash Chain Pattern:**

Every Entity maintains a cryptographic hash chain:

```
Entity.hash = SHA256(content + previous_hash)
Entity.previous_hash = hash of prior state (None for initial Entity)
```

**Conflict Detection:**

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

### Note

**Purpose:** General-purpose text item

**Schema:**
```python
@dataclass
class Note(Item):
    # Inherited: uuid, _type='Note', realized_at, canonical_at, integrity_hash, 
    #            fidelity, superseded_by, superseded_at
    description: str        # Main content
    summary: str | None     # Optional, for agent use
    title: str | None       # Optional title
```

---

### Message

**Purpose:** Communication between participants

**Schema:**
```python
@dataclass
class Message(Note):
    # Inherited: uuid, _type='Message', realized_at, canonical_at, integrity_hash, 
    #            fidelity, superseded_by, superseded_at, description, summary, title
    sender: str             # 'user' | 'agent' | participant identifier
    recipient: str | None   # Optional recipient
    subject: str | None     # Optional (or reuse title)
```

---

### Email

**Purpose:** Email message imported from external provider (GMail, Outlook, etc.)

**Schema:**
```python
@dataclass
class Email(Note):
    # Inherited: uuid, _type='Email', realized_at, canonical_at, integrity_hash,
    #            fidelity, superseded_by, superseded_at
    # Note: description stores email body (plain text), title stores subject

    # Standard email fields (provider-agnostic)
    rfc_message_id: str              # RFC 822 Message-ID header (deduplication key)
    from_address: str                # From header (parsed)
    to_addresses: list[str]          # To header (parsed, multiple recipients)
    cc_addresses: list[str] | None   # Cc header (parsed)
    bcc_addresses: list[str] | None  # Bcc header (rarely available in exports)
    sent_at: datetime                # Date header (sent timestamp)
    received_at: datetime | None     # Delivery timestamp (when available)

    # Threading (RFC 5322)
    references: list[str] | None     # References header (thread ancestors)
    in_reply_to: str | None          # In-Reply-To header (direct parent)

    # Attachments
    has_attachments: bool
    attachment_count: int

    # Provider-specific data (stored in Item.metadata, not data):
    # GMail: {"provider": "google", "gmail_thread_id": "...", "labels": [...]}
    # Outlook: {"provider": "outlook", "conversation_id": "..."}
```

**Properties:**
- **Provider-agnostic**: Core fields work with any email provider
- **Threading**: Uses standard RFC 5322 headers (References, In-Reply-To)
- **Deduplication**: `rfc_message_id` is globally unique per email
- **Metadata**: Provider-specific fields (GMail thread ID, labels) stored in `Item.metadata`
- **Body storage**: Plain text in `description`, HTML in `metadata` if needed

**Threading Relations:**
Emails in a conversation chain are connected via `replies_to` system relations:
- `source`: reply email UUID
- `target`: parent email UUID
- `evidence.source`: `"system_inferred"`
- `evidence.method`: `"rfc_5322_in_reply_to"` or `"rfc_5322_references"`

---

### ToolCall

**Purpose:** Record of tool invocation by user or agent

**Schema:**
```python
@dataclass
class ToolCall(Item):
    # Inherited: uuid, _type='ToolCall', realized_at, canonical_at, integrity_hash,
    #            fidelity, superseded_by, superseded_at
    tool: str               # Tool name (e.g., 'artifact_reader', 'scratchpad')
    operation: str          # Specific operation (e.g., 'semantic_search', 'scroll_to')
    params: dict            # Operation parameters
    result: ToolResult | None  # Output, if completed
    caller: str             # 'user' | 'agent'
    context: str | None     # Human-readable intent/explanation

@dataclass
class ToolResult:
    status: str         # 'success' | 'error' | 'cancelled'
    output: Any         # Tool-specific output
    timestamp: datetime
```

---

### EntityDelta

**Purpose:** Records a change to an Entity (audit trail for Core mutations)

**Schema:**
```python
@dataclass
class EntityDelta(Item):
    # Inherited: uuid, _type='EntityDelta', realized_at, canonical_at, integrity_hash,
    #            fidelity, superseded_by, superseded_at
    entity_uuid: str            # Which Entity this changes (core_ prefix)
    entity_type: str            # Type of the Entity (e.g., 'Artifact')
    commit: str                 # Hash of resulting Entity state after this delta
    parent: str | list[str] | None  # Parent commit hash(es); None for creation
    ops: dict | str             # Change description (format depends on entity type)
    context: list[str]          # Snapshot of ContextFrame.containers at mutation time
```

**Properties:**
- **Timeline Item**: EntityDeltas appear in the timeline; Entities do not
- **Hash chain**: `commit` is hash of resulting Entity state
- **Context capture**: `context` field captures what was in focus when change was made (per RFC-003)

---

### SystemEvent

**Purpose:** System-generated notifications and state changes

**Schema:**
```python
@dataclass
class SystemEvent(Item):
    # Inherited: uuid, _type='SystemEvent', realized_at, canonical_at, integrity_hash,
    #            fidelity, superseded_by, superseded_at
    event_type: str         # 'entity_created' | 'fossilization_sweep' | ...
    payload: dict | None    # Event-specific data
```

---

## Entity Types

### Artifact

**Purpose:** Structured document or content object

**Schema:**
```python
@dataclass
class Artifact(Entity):
    # Inherited: uuid, _type='Artifact', hash, previous_hash, version,
    #            created_at, updated_at, group_id, superseded_by, superseded_at, derived_from
    label: str                      # User-facing name
    content: str                    # Current content
    content_type: str               # 'text/plain' | 'text/markdown' | etc.
    label_history: list[str]        # Past labels for backward compatibility
```

**Properties:**
- **Lives in Core**: Mutable, user-controlled
- **Not in timeline**: Artifacts span time ranges; only their EntityDeltas appear in timeline
- **Content hash**: Current content hash equals latest EntityDelta.commit

---

### Label

**Purpose:** Named reference to Items or Entities

**Schema:**
```python
@dataclass
class Label(Entity):
    # Inherited: uuid, _type='Label', hash, previous_hash, version,
    #            created_at, updated_at, group_id, superseded_by, superseded_at, derived_from
    name: str                       # Label text
    target_uuid: str                # What this label points to
    target_type: str                # 'item' | 'entity'
```

---

## Relations

Relations represent connections between Items and Entities. MemoGarden distinguishes between **system relations** (immutable structural facts) and **user relations** (engagement signals that decay over time).

**Full specification in RFC-002.** This section provides an overview only.

### Design Rationale

- **System relations**: Encode structural facts (causation, containment, citations). Culling them would be changing history.
- **User relations**: Encode engagement and attention, which naturally fades over time. Should decay and fossilize.

### Evidence Object

Relations can carry provenance information:

```python
@dataclass
class Evidence:
    source: str              # 'soil_stated' | 'user_stated' | 'agent_inferred' | 'system_inferred'
    confidence: float | None # For inferred only (0.0-1.0); stated facts implicit 1.0
    basis: list[str] | None  # UUIDs of supporting items/entities
    method: str | None       # For inferred: 'nlp_extraction' | 'pattern_match' | etc.
```

### System Relations (Immutable Facts)

**Schema:**
```python
@dataclass
class SystemRelation:
    uuid: str               # Stable identifier (soil_ prefix)
    kind: str               # 'triggers' | 'cites' | 'derives_from' | 'contains' | ...
    source: str             # UUID of source
    source_type: str        # 'item' | 'entity'
    target: str             # UUID of target
    target_type: str        # 'item' | 'entity'
    created_at: int         # Days since epoch
    evidence: Evidence | None
    metadata: dict | None
```

**Kinds:**
```python
SYSTEM_RELATION_KINDS = {
    'triggers',      # Causal chain (A caused B)
    'cites',         # Reference/quotation  
    'derives_from',  # Synthesis provenance
    'contains',      # Structural containment
    'replies_to',    # Message threading
    'continues',     # Branch continuation
    'supersedes',    # Replacement/update
}
```

### User Relations (Engagement Signals)

**Schema:**
```python
@dataclass
class UserRelation:
    uuid: str               # Stable identifier (core_ prefix when active)
    kind: str               # 'explicit_link'
    source: str             # UUID of source
    source_type: str        # 'item' | 'entity'
    target: str             # UUID of target
    target_type: str        # 'item' | 'entity'
    time_horizon: int       # Future timestamp (days since epoch)
    last_access_at: int     # Timestamp of most recent access (days since epoch)
    created_at: int         # Days since epoch
    evidence: Evidence | None
    metadata: dict | None
```

**Time horizon mechanism, fossilization, and lifecycle management are fully specified in RFC-002.**

---

## Context Capture

MemoGarden maintains mechanisms for tracking attention patterns. **Full specification in RFC-003.** This section provides an overview only.

### Overview

| Stream | What it captures | Storage | Retention |
|--------|-----------------|---------|-----------|
| **Delta-stream** | State mutations | Soil (permanent) | Indefinite |
| **View-stream** | Attention events | Core (ephemeral) | ~24hr or N entries |

### Key Concepts

- **ContextFrame**: LRU set of containers representing current attention state
- **View-stream**: Ephemeral ringbuffer capturing what was observed
- **Context capture on mutation**: EntityDelta.context captures ContextFrame snapshot

**See RFC-003 for complete specification of View, ContextFrame, and context capture rules.**

---

## Data Storage Schema

### Soil Database Schema (SQLite)

```sql
-- Items table
CREATE TABLE item (
    uuid TEXT PRIMARY KEY,
    _type TEXT NOT NULL,
    realized_at TEXT NOT NULL,  -- ISO 8601
    canonical_at TEXT NOT NULL, -- ISO 8601
    integrity_hash TEXT,        -- SHA256 of content fields
    fidelity TEXT NOT NULL DEFAULT 'full',
    superseded_by TEXT,
    superseded_at TEXT,
    data JSON NOT NULL          -- Type-specific fields
);

CREATE INDEX idx_item_type ON item(_type);
CREATE INDEX idx_item_realized ON item(realized_at);
CREATE INDEX idx_item_canonical ON item(canonical_at);
CREATE INDEX idx_item_fidelity ON item(fidelity);

-- System relations (immutable facts)
CREATE TABLE system_relation (
    uuid TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target TEXT NOT NULL,
    target_type TEXT NOT NULL,
    created_at INTEGER NOT NULL,  -- Days since epoch
    evidence JSON,
    metadata JSON,
    
    UNIQUE(kind, source, target)
);

CREATE INDEX idx_sysrel_source ON system_relation(source);
CREATE INDEX idx_sysrel_target ON system_relation(target);
CREATE INDEX idx_sysrel_kind ON system_relation(kind);
```

### Core Database Schema (SQLite)

```sql
-- Entities table (with hash chain)
CREATE TABLE entity (
    uuid TEXT PRIMARY KEY,
    _type TEXT NOT NULL,
    hash TEXT NOT NULL,
    previous_hash TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    
    group_id TEXT,
    superseded_by TEXT,
    superseded_at TEXT,
    derived_from TEXT,
    
    data JSON NOT NULL          -- Type-specific fields
);

CREATE INDEX idx_entity_type ON entity(_type);
CREATE INDEX idx_entity_hash ON entity(hash);
CREATE INDEX idx_entity_previous_hash ON entity(previous_hash);

-- User relations (engagement signals, active only)
CREATE TABLE user_relation (
    uuid TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target TEXT NOT NULL,
    target_type TEXT NOT NULL,
    time_horizon INTEGER NOT NULL,
    last_access_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    evidence JSON,
    metadata JSON,
    
    UNIQUE(kind, source, target)
);

CREATE INDEX idx_userrel_source ON user_relation(source);
CREATE INDEX idx_userrel_target ON user_relation(target);
CREATE INDEX idx_userrel_horizon ON user_relation(time_horizon);

-- Context frames (see RFC-003 for full specification)
CREATE TABLE context_frame (
    uuid TEXT PRIMARY KEY,
    participant TEXT NOT NULL,
    containers JSON NOT NULL,
    created_at TEXT NOT NULL,
    parent_frame_uuid TEXT
);

CREATE INDEX idx_context_frame_participant ON context_frame(participant);
```

### Days Since Epoch

```python
from datetime import date, timedelta

EPOCH = date(2020, 1, 1)

def current_day() -> int:
    return (date.today() - EPOCH).days

def day_to_date(day: int) -> date:
    return EPOCH + timedelta(days=day)
```

Using days (not seconds) keeps integers small and matches the granularity needed for keep/fossilize decisions.

---

## Configuration

```python
@dataclass
class MemoGardenConfig:
    # Storage
    soil_db_path: str = 'soil.db'
    core_db_path: str = 'core.db'
    
    # Integrity
    verify_hash_on_read: bool = True
    
    # Undo window
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

## Identified Gaps

This PRD intentionally does not address the following areas:

### Gap 1: Explicit Linking UX

**What's missing:** How operator creates explicit user relations.

**Status:** Unresolved. No UI or tool defined for explicit linking.

### Gap 2: Relation Inheritance on Item Edit

**What's missing:** When item B is edited to reference item A, does a system relation (cites) get created automatically?

**Status:** Unresolved. Reference parsing behavior not specified.

### Gap 3: Cascading Effects

**What's missing:** When item A is deleted, what happens to relations where A is source or target?

**Status:** Unresolved.

### Gap 4: Bulk Import Handling

**What's missing:** 500 emails arrive at once. How are their initial user relations (if any) and time horizons set?

**Status:** Partially resolved by RFC-002. Each starts cold with no user relations; fossilizes if not accessed. Initial time horizon policy still TBD.

### Gap 5: Resurrection Depth

**What's missing:** When fossilized item is accessed, should it be fully restored or remain compressed?

**Status:** Partially resolved by RFC-002. Item remains compressed; new user relations accumulate. Full restore policy still TBD.

### Gap 6: Multi-Hop Significance Propagation

**What's missing:** Should high-significance items boost connected items?

**Status:** Deferred. RFC-002 notes this may add complexity without proportionate benefit.

### Gap 7: Focus Tracking Mechanism

**What's missing:** How system determines container "has focus" for View session boundaries.

**Status:** Addressed in RFC-003. Infer from mutation target + timeout fallback.

### Gap 8: Coalescence Behavior Validation

**What's missing:** Timeout fallback value if focus not explicitly tracked.

**Status:** Addressed in RFC-003. Default 5 minutes (FOCUS_TIMEOUT_SECONDS).

### Gap 9: Eviction Score Formula

**What's missing:** Empirical validation of deletion priority weights.

**Status:** Identified in RFC-002. Formula proposed but needs tuning.

---

## Open Questions

1. **Initial time horizon for new user relations:** What value? `current_day() + 7`?

2. **Relation pruning:** Should user relations with horizon far in the past be deleted entirely, or kept indefinitely in Soil?

3. **Orphan handling:** Items with no relations at all. Fossilize immediately, or wait for some access window?

4. **Summary quality:** Extractive (fast, predictable) vs LLM-generated (better, costly)? Hybrid based on item type?

5. **Per-type decay rates:** Should emails decay faster than documents? Or uniform treatment?

---

## Related Documents

| Document | Scope |
|----------|-------|
| RFC-001 v4 | Security architecture, deployment profiles, encryption |
| RFC-002 v5 | Time horizon mechanism, fossilization, relation lifecycle |
| RFC-003 v2 | Context capture, View-stream, ContextFrame |
| JCE Whitepaper v1.0 | Interaction model, utilities, studios |
| Project Studio Specification v0.4.0 | Project-specific structures and workflows |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-12-26 | Initial draft with complete ontology |
| 0.2.0 | 2025-12-27 | Added ToolCall entity, Frame entity, clarified stack semantics |
| 0.3.0 | 2025-12-29 | Storage layer split (Soil/Core); Item base type with hierarchy; dual timestamps |
| 0.4.0 | 2025-12-29 | Generalized relations model |
| 0.4.1 | 2025-12-31 | Added Entity Change Tracking section with hash chain pattern |
| 0.4.2 | 2025-01-07 | Added integrity_hash to Item; Evidence object for provenance tracking |
| 0.5.0 | 2025-01-16 | Separated system vs user relations; time horizon mechanism; fossilization |
| 0.6.0 | 2025-01-20 | Design review integration: UUID prefixes, ContextFrame, fidelity states |
| 0.7.0 | 2025-01-29 | **Refactoring:** Renamed to "Personal Information System"; clarified Item vs Entity distinction (Items immutable in Soil with supersession, Entities mutable in Core with delta tracking); removed project-specific features to Project Studio Specification; deferred relation details to RFC-002, context details to RFC-003; American English spelling; updated gap status |

---

**Status:** Draft  
**Next Steps:** 
1. Resolve Gap 2 (automatic relation creation from references)
2. Define initial time horizon policy for new relations
3. Implement and validate eviction score formula

---

**END OF DOCUMENT**
