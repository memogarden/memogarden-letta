# MemoGarden Project System - Product Requirements Document

**Version:** 0.4.1
**Status:** Draft
**Last Updated:** 2025-12-31

## Overview

MemoGarden Project System provides an artifact-first collaborative workspace for design thinking and project development. Conversations and artifacts evolve together through a stack-based exploration model with git-inspired versioning.

## Core Principles

1. **Artifact-First**: Design artifacts are primary, conversations are context
2. **Immutable Timeline**: Items in Soil cannot be retroactively changed (short undo window excepted)
3. **Append-Only Logs**: Conversations grow through addition, not modification
4. **Git-Inspired Versioning**: Familiar commit semantics for artifact evolution
5. **Stack-Based Exploration**: Branch freely, collapse learnings back to main path
6. **Fragment Granularity**: Semantic units, not sentences or words
7. **Inline References**: Links parsed from natural language, not explicit fields
8. **UUID-Based Artifacts**: Stable identifiers enable relabeling without breaking references
9. **Joint Cognitive System**: User and agent share tools, observe each other's work, and coordinate as a single cognitive unit
10. **Explicit Causation**: Relations enable audit trails and retrace capabilities

---

## Storage Architecture

MemoGarden uses a two-layer storage model separating immutable facts from mutable state.

### UUID Systems

MemoGarden uses **two separate UUID namespaces** to prevent collisions between Soil and Core:

| System | UUID Prefix | Database | Mutability | Examples |
|--------|-------------|----------|------------|----------|
| **Core** | `entity_` | Core DB | Mutable | `entity_abc123...`, `entity_def456...` |
| **Soil** | `item_` | Soil DB | Immutable | `item_xyz789...`, `item_uvw012...` |

**Why separate prefixes?**
- **Separate databases**: Core and Soil use different SQLite databases
- **No collision risk**: Even if raw UUIDs collide, prefixed identifiers remain unique
- **Clear provenance**: `entity_` prefix immediately indicates mutable shared belief; `item_` indicates immutable fact
- **One-way bridge**: Agents create Entities based on Items, never the reverse

**UUID Format:**
```
entity_<uuid4>    # e.g., entity_a1b2c3d4-e5f6-7890-abcd-ef1234567890
item_<uuid4>      # e.g., item_fedcba98-7654-3210-fedc-ba9876543210
```

**Migration Direction:**
- Items (Soil) → Entities (Core): Agents create/update Entities based on immutable Items
- Entities (Core) → Items (Soil): Never migrate mutable Entities to Soil

### Soil (Immutable Facts)

**Purpose:** Ground truth timeline of what happened

**Contents:**
- All Items (Notes, Messages, ToolCalls, ArtifactDeltas, etc.)
- Fossilized Relations (append-only once in Soil)

**Properties:**
- **Immutable**: Once realized, Items cannot be modified (5-minute undo window for mistakes)
- **Append-only**: New facts add to history, never replace
- **Timestamped**: Both `realized_at` (system time) and `canonical_at` (user-controlled time)

### Core (Mutable State)

**Purpose:** User-controlled belief layer and evolving documents

**Contents:**
- Artifacts (mutable documents)
- Active Relations (mutable until fossilized)
- User belief overrides about Soil items
- Relation strength / fossilization state
- Labels and organizational metadata

**Properties:**
- **Mutable**: Content can be edited
- **User-sovereign**: User beliefs override inferred/imported facts
- **Evolving**: Artifacts change over time via Deltas
- **Lifecycle-aware**: Relations fossilize from Core to Soil when appropriate

---

## Entity Change Tracking

MemoGarden uses **hash-based change tracking** for all mutable entities in Core, enabling efficient synchronization, conflict detection, and historical reconstruction via EntityDeltas in Soil.

### Hash Chain Pattern

Every Entity in Core maintains a cryptographic hash chain, similar to git commits:

```
Entity.hash = SHA256(content + previous_hash)
Entity.previous_hash = hash of prior state (NULL for initial Entity)
```

**Properties:**
- **Content-addressable**: Hash uniquely identifies entity state
- **Tamper-evident**: Any change produces new hash, breaking the chain
- **Revert-safe**: Reverting to previous state creates new hash (e.g., `hash(rollback, hash_C) ≠ hash_A`)
- **Collision-resistant**: SHA256 prevents practical hash collisions
- **Provenance tracking**: `previous_hash` provides full lineage

**Schema:**
```python
@dataclass
class Entity:
    uuid: str                       # Unique identifier (never changes)
    type: str                       # Entity type: 'transaction', 'user', 'recurrence', etc.
    hash: str                       # Current state hash (SHA256)
    previous_hash: str | None       # Previous state hash (NULL for initial)
    version: int                    # Monotonically increasing (for ordering/display)
    created_at: datetime            # Entity creation timestamp
    updated_at: datetime            # Last update timestamp

    # Type-specific fields (transaction amount, username, etc.)
    # ...
```

### Hash Computation

```python
import hashlib
import json

def compute_entity_hash(entity_data: dict, previous_hash: str | None) -> str:
    """
    Compute hash for entity state.

    Args:
        entity_data: Dict of entity fields (excluding uuid, hash, previous_hash, version)
        previous_hash: Hash of previous state (None for initial entity)

    Returns:
        SHA256 hash string
    """
    # Canonical JSON representation (sorted keys, no whitespace)
    canonical = json.dumps(entity_data, sort_keys=True, separators=(',', ':'))

    # Include previous hash in hash computation (creates chain)
    content = f"{canonical}|{previous_hash or ''}"

    return hashlib.sha256(content.encode()).hexdigest()
```

**Example hash chain:**
```
Initial:  hash="a1b2c3...", previous_hash=None, version=1
Update 1: hash="d4e5f6...", previous_hash="a1b2c3...", version=2
Update 2: hash="g7h8i9...", previous_hash="d4e5f6...", version=3
Revert:   hash="j0k1l2...", previous_hash="g7h8i9...", version=4
          (content matches version 1, but hash is new due to different previous_hash)
```

### Conflict Detection

**Optimistic locking with hash chain:**

1. **Client reads entity**: `GET /api/v1/transactions/uuid`
   - Response: `{uuid, amount, hash: "abc", version: 5, ...}`

2. **Client updates entity**: `PUT /api/v1/transactions/uuid`
   - Request: `{amount: 10.50, based_on_hash: "abc", based_on_version: 5}`

3. **Server validates**:
   ```python
   current = get_entity(uuid)
   if current.hash != request.based_on_hash:
       # Conflict! Someone else changed it
       return 409 Conflict, {
           "current_hash": current.hash,
           "current_version": current.version,
           "client_hash": request.based_on_hash,
           "client_version": request.based_on_version,
           "error": "Entity was modified by another client"
       }

   # Compute new hash and update
   new_hash = compute_entity_hash(new_data, current.hash)
   update_entity(
       hash=new_hash,
       previous_hash=current.hash,
       version=current.version + 1,
       **new_data
   )
   ```

4. **Delta archival to Soil**:
   - EntityDelta stored in Soil with `(commit=new_hash, parent=current.hash)`
   - Enables historical reconstruction and audit trail

### Benefits Over Version Numbers Alone

| Aspect | Version Only | Hash Chain |
|--------|-------------|------------|
| **Change detection** | "This is v5" | "Content is {state}, derived from v4" |
| **Tamper evidence** | No (can increment without change) | Yes (content change → new hash) |
| **Revert handling** | Ambiguous (rollback to v4?) | Clear (new hash with different parent) |
| **Synchronization** | Fragile (clock skew) | Robust (cryptographic verification) |
| **Multi-app support** | Race conditions | Conflict detection via hash mismatch |
| **Historical query** | Scan all versions | Direct hash lookup in Soil |

### Storage in Core

**Entity table stores:**
- Current state (fields: amount, description, etc.)
- Change metadata (hash, previous_hash, version, timestamps)
- **Not full history** (that's what Soil EntityDeltas are for)

**Performance consideration:**
- Storing `hash` and `previous_hash` in Core avoids expensive recomputation
- Hash is computed once on update, stored for quick validation
- Enables fast conflict detection without scanning Soil

**Schema (entity table):**
```sql
CREATE TABLE entity (
    uuid TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    hash TEXT NOT NULL,              -- Current state hash
    previous_hash TEXT,              -- Previous state hash (NULL for initial)
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    -- Common metadata
    group_id TEXT,                   -- Optional grouping
    superseded_by TEXT,              -- Reclassification
    superseded_at TEXT,
    derived_from TEXT,               -- Provenance

    FOREIGN KEY (group_id) REFERENCES entity(uuid),
    FOREIGN KEY (superseded_by) REFERENCES entity(uuid),
    FOREIGN KEY (derived_from) REFERENCES entity(uuid)
);

CREATE INDEX idx_entity_hash ON entity(hash);
CREATE INDEX idx_entity_previous_hash ON entity(previous_hash);
```

### EntityDelta (Soil - Future)

**Purpose:** Immutable record of entity changes for historical reconstruction

**Schema:**
```python
@dataclass
class EntityDelta(Item):
    # Inherited: uuid, _type='EntityDelta', realized_at, canonical_at
    entity_uuid: str          # Which entity changed
    entity_type: str          # Type of entity (transaction, user, etc.)
    commit: str               # Hash of new state (matches Entity.hash)
    parent: str | None        # Hash of previous state (matches Entity.previous_hash)
    version: int              # Entity version after this change
    changes: dict             {"fields": {"amount": [10.0, 15.0]}, "reason": "..."}
```

**Relation to ArtifactDelta:**
- Same hash chain pattern
- `commit` = current state hash
- `parent` = previous state hash
- Enables git-like history navigation
- Different schema: EntityDelta tracks field changes, ArtifactDelta tracks line operations

**Use cases:**
- Audit trails (who changed what, when)
- Conflict resolution (compare divergent branches)
- Historical queries (what did this transaction look like on date X?)
- Agent analysis (detect patterns, anomalies)
- Rollback/revert (navigate to any prior state)

### Delta Notification Service (Future)

**Purpose:** Notify subscribed apps of entity changes

**Schema:**
```sql
CREATE TABLE delta_notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_uuid TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    old_hash TEXT NOT NULL,         -- Previous state hash
    new_hash TEXT NOT NULL,         -- New state hash
    version INTEGER NOT NULL,
    changed_at TEXT NOT NULL,       -- ISO 8601
    processed INTEGER DEFAULT 0     -- 0 = pending, 1 = processed
);

CREATE INDEX idx_delta_notification_entity ON delta_notification(entity_uuid);
CREATE INDEX idx_delta_notification_processed ON delta_notification(processed);
```

**Notification flow:**
1. Entity updated in Core (hash changes: A→B)
2. Delta notification recorded: `(entity_uuid, old_hash=A, new_hash=B, version=5)`
3. Subscribed apps poll or receive push notifications
4. Apps fetch updated entity, detect local conflicts via hash mismatch

**Benefits:**
- Apps don't need to poll entire entity set
- Efficient synchronization (only process changes)
- Multi-app support (Budget, Project System, future apps)
- Ordered notifications (version ensures correct sequence)

---

## Entity Definitions

### Item (Base Type)

**Purpose:** Base type for all timeline entities in Soil

**Schema:**
```python
@dataclass
class Item:
    uuid: str               # Stable identifier
    _type: str              # CamelCase, system-managed (e.g., 'Note', 'Message', 'ToolCall')
    realized_at: datetime   # When system recorded this item (immutable)
    canonical_at: datetime  # When user says it happened (user-controllable)
```

**Properties:**
- **UUID identity**: Each Item has a unique, stable identifier
- **Explicit typing**: `_type` field uses underscore prefix to reserve non-prefixed attributes for user use
- **Dual timestamps**: System records both objective and subjective time
- **Immutable in Soil**: Once realized, Items are permanent (modulo short undo window)

**Type Naming Convention:**
- Use CamelCase for `_type` values (e.g., `Note`, `Message`, `ToolCall`, `ArtifactDelta`)
- Same representation in UI and backend for consistency

**Reserved Attribute Names:**

The following attribute names are reserved for future relation denormalization. Extensions MUST NOT use these:

```python
RESERVED_ITEM_ATTRIBUTES = [
    'triggered_by',
    'superceded_by',
    'replies_to',
    'derived_from',
    'continues_from',
    'contained_by',
]
```

---

### Note

**Purpose:** General-purpose text item

**Schema:**
```python
@dataclass
class Note(Item):
    # Inherited: uuid, _type='Note', realized_at, canonical_at
    description: str        # Main content
    summary: str | None     # Optional, for agent use
    title: str | None       # Optional title
```

---

### Message

**Purpose:** Communication between participants, composed of fragments

**Schema:**
```python
@dataclass
class Message(Note):
    # Inherited: uuid, _type='Message', realized_at, canonical_at, description, summary, title
    sender: str             # 'user' | 'agent' | participant identifier
    recipient: str | None   # Optional recipient
    subject: str | None     # Optional (or reuse title)
    fragments: list[Fragment]  # Inline semantic units
```

**Properties:**
- **Extends Note**: Inherits description, summary, title
- **Contains Fragments**: Fragments are inline parts, not standalone Items
- **Sender/Recipient**: Track communication direction

---

### Fragment

**Purpose:** Atomic semantic unit within a Message (an idea/statement)

**Schema:**
```python
@dataclass
class Fragment:
    id: str         # ^a7f (content hash, 3-4 chars base36)
    content: str    # Natural language, may contain inline references
```

**Properties:**
- **Not an Item**: Fragments do not appear independently in the timeline
- **Inline within Messages**: They inherit timestamps from their containing Message
- **Hash-based ID**: Deterministic from content
- **Collision handling**: Disambiguate via (message_uuid, position)
- **Addressable for reference**: Can be referenced by ID from other Items using anchor notation: `item_uuid#^a7f` or `item_uuid#^a7f:^b2e` for ranges
- **Opaque to users**: Raw reference syntax renders as styled, interactive elements

**Reference Display:**
```
Internal:  "Use PostgreSQL instead - ^k3m shows SQLite won't scale"
Rendered:  "Use PostgreSQL instead - [scalability analysis] shows SQLite won't scale"
                                      └─ styled link, interactive
```

**Fragment Hash Generation:**
```python
import hashlib

def generate_fragment_id(content: str) -> str:
    """Generate 3-4 character base36 hash from content."""
    hash_bytes = hashlib.sha256(content.encode()).digest()
    hash_int = int.from_bytes(hash_bytes[:2], 'big')
    
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while hash_int > 0:
        result = chars[hash_int % 36] + result
        hash_int //= 36
    
    return f"^{result.zfill(3)}"
```

---

### ToolCall

**Purpose:** Record of tool invocation by user or agent

**Schema:**
```python
@dataclass
class ToolCall(Item):
    # Inherited: uuid, _type='ToolCall', realized_at, canonical_at
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

**Properties:**
- **First-class timeline Item**: ToolCalls appear in timeline alongside Messages
- **Caller tracking**: Distinguishes user-invoked from agent-invoked tools
- **Observable**: Enables user to follow or retrace agent actions
- **Context for humans**: The `context` field explains intent, not just parameters

**Examples:**
```python
ToolCall(
    uuid='tc_001',
    _type='ToolCall',
    realized_at=datetime.now(),
    canonical_at=datetime.now(),
    tool='artifact_reader',
    operation='semantic_search',
    params={'artifact': 'art_uuid1', 'query': 'authentication flow'},
    result=ToolResult(status='success', output={'matches': [(145, 162), (890, 920)]}),
    caller='agent',
    context='Finding authentication-related sections'
)
```

---

### ArtifactCreated

**Purpose:** Records the creation of a new Artifact

**Schema:**
```python
@dataclass
class ArtifactCreated(Item):
    # Inherited: uuid, _type='ArtifactCreated', realized_at, canonical_at
    artifact_uuid: str      # UUID of the created Artifact
    label: str              # Initial label assigned
```

**Properties:**
- **Distinct from first Delta**: Creation event and initial content are separate concerns
- **Links to Artifact**: References the Artifact in Core by UUID
- **Causation via Relation**: Link to triggering Item stored in `unique_relation` table

---

### ArtifactDelta

**Purpose:** Atomic unit of artifact change (git commit equivalent)

**Schema:**
```python
@dataclass
class ArtifactDelta(Item):
    # Inherited: uuid, _type='ArtifactDelta', realized_at, canonical_at
    artifact_uuid: str          # Which Artifact this changes
    commit: str                 # e8d9f3c (this commit hash)
    parent: str | list[str] | None  # c4f2a1b (single), [hash1, hash2] (merge), None (first)
    ops: str                    # "+15:^a7f -23 ~18:^b2e→^c3d"
    references: list[str]       # [^m8n, ^p4q] - fragment IDs that informed this change
```

**Properties:**
- **Timeline Item**: Deltas appear in the timeline; Artifacts do not
- **Artifact reference**: Links to Artifact in Core by UUID
- **Hash chain**: Same pattern as Entity change tracking (see [Entity Change Tracking](#entity-change-tracking))
- **Parent tracking**: Enables git-like history graph
- **Multiple parents**: Merge commits have `[hash1, hash2]`
- **Operation syntax**: `+add -remove ~replace >move` (line-based)
- **References fragments**: Links to the fragments that informed this change

**Relation to EntityDelta:**
- Both use hash chain pattern (`commit` = current hash, `parent` = previous hash)
- ArtifactDelta tracks line-based text operations
- EntityDelta tracks field-level changes
- Both enable git-like history navigation and conflict resolution

**Delta Operations:**
```
+15:^a7f              Add fragment a7f at line 15
-23                   Remove line 23
~18:^b2e→^c3d        Replace line 18: fragment b2e with c3d
>12@30               Move line 12 to position 30

Full delta example:
+4:^f9e -5 ~3:^a7f→^k3m
```

---

### SystemEvent

**Purpose:** System-generated notifications and state changes

**Schema:**
```python
@dataclass
class SystemEvent(Item):
    # Inherited: uuid, _type='SystemEvent', realized_at, canonical_at
    event_type: str         # 'artifact_update' | 'branch_created' | 'summary_generated' | ...
    payload: dict | None    # Event-specific data
```

**Properties:**
- **System-authored**: Generated by MemoGarden, not user or agent
- **Flexible payload**: Event-specific data structure
- **Timeline markers**: Provide navigation anchors

---

### Artifact (lives in Core)

**Purpose:** Structured project document (goals, mockups, requirements, etc.)

**Schema:**
```python
@dataclass
class Artifact:
    uuid: str                       # art_uuid1 (stable identifier)
    label: str                      # "goals_doc" (user-facing name)
    content: str                    # Current content (line-numbered)
    deltas: list[ArtifactDelta]     # Full commit history (references to Soil)
    snapshots: dict[str, str]       # commit → content
    label_history: list[str]        # Past labels for backward compatibility
```

**Properties:**
- **Lives in Core**: Mutable, user-controlled
- **UUID-based identity**: `uuid` never changes
- **Relabelable**: `label` can change without breaking references
- **Not in timeline**: Artifacts span time ranges; only their Deltas appear in timeline
- **Line-numbered content**: Enables line-based references
- **Self-contained history**: References Deltas in Soil

---

### ArtifactCollection

**Purpose:** Container for all project artifacts with UUID-based lookup

**Schema:**
```python
@dataclass
class ArtifactCollection:
    artifacts: dict[str, Artifact]  # uuid → artifact
    labels: dict[str, str]          # label → uuid (reverse lookup)
```

**Properties:**
- **UUID primary key**: Artifacts identified by UUID
- **Label-based access**: Users use labels, system resolves to UUIDs
- **Relabeling support**: Change `artifact.label` without breaking references
- **Reverse lookup**: `labels` dict enables fast label → UUID resolution

---

## Relations

Relations represent connections between Items, Entities, and Artifacts. MemoGarden uses a two-table design separating unique (1:1) relations from multi (N:N) relations.

### Design Rationale

**Why two tables?**
- **Constraint enforcement**: UniqueRelation can enforce UNIQUE(kind, target) at database level
- **Query clarity**: No ambiguity about cardinality when querying
- **Performance**: Different indexing strategies for different access patterns

**Why relations tables rather than item attributes?**
- **Backward references**: Some relations (e.g., supercedes) point from new→old, requiring update to old item
- **Consistency**: Uniform query semantics across relation kinds
- **Lifecycle**: Relations can migrate from Core (mutable) to Soil (immutable) independently
- **Future flexibility**: Can denormalize to attributes later if performance requires

### Relation Categories

| Category | Examples | Mutability | Notes |
|----------|----------|------------|-------|
| **Structural** | triggers, replies_to, contains | Immutable | Defines item's place in graph |
| **Temporal** | supercedes | Immutable once created | Created after both items exist |
| **Interpretive** | mentions, derived_from | Mutable | NLP may improve, user may correct |
| **Organizational** | groups_with (projects) | Mutable | User reorganizes over time |

### Relation Kinds

| Kind | Table | Description | Source→Target |
|------|-------|-------------|---------------|
| `triggers` | unique_relation | Causal chain | Cause → Effect |
| `supercedes` | unique_relation | Replacement/update | New → Old |
| `replies_to` | unique_relation | Message threading | Reply → Parent |
| `continues` | unique_relation | Branch continuation | New branch → Old branch |
| `mentions` | multi_relation | Entity/item reference | Mentioner → Mentioned |
| `derived_from` | multi_relation | Synthesis provenance | Derived → Sources |
| `contains` | multi_relation | Containment/grouping | Container → Contained |

### UniqueRelation

**Purpose:** Relations where each target appears at most once per kind

**Schema:**
```python
@dataclass
class UniqueRelation:
    uuid: str               # Stable identifier
    kind: str               # 'triggers' | 'supercedes' | 'replies_to' | 'continues'
    source: str             # UUID of source (the newer/acting item)
    source_type: str        # 'item' | 'entity' | 'artifact'
    target: str             # UUID of target (the older/affected item)
    target_type: str        # 'item' | 'entity' | 'artifact'
    realized_at: datetime   # When this relation was recorded
    metadata: dict | None   # Kind-specific data (e.g., {'reason': 'cancellation'})
```

**Constraints:**
- `UNIQUE(kind, target)`: Each item can only be triggered/superceded/replied-to by one other item

**Example - Trigger Chain:**
```python
# User message triggers agent tool call
UniqueRelation(
    uuid='rel_001',
    kind='triggers',
    source='msg_001',        # User's message
    source_type='item',
    target='tc_001',         # Agent's tool call
    target_type='item',
    realized_at=datetime.now(),
    metadata=None
)

# Supercession with reason
UniqueRelation(
    uuid='rel_002',
    kind='supercedes',
    source='event_new',      # Updated event
    source_type='item',
    target='event_old',      # Original event
    target_type='item',
    realized_at=datetime.now(),
    metadata={'reason': 'reschedule'}
)
```

### MultiRelation

**Purpose:** Relations allowing multiple connections per source or target

**Schema:**
```python
@dataclass
class MultiRelation:
    uuid: str               # Stable identifier
    kind: str               # 'mentions' | 'derived_from' | 'contains'
    source: str             # UUID of source
    source_type: str        # 'item' | 'entity' | 'artifact'
    target: str             # UUID of target
    target_type: str        # 'item' | 'entity' | 'artifact' | 'fragment'
    realized_at: datetime   # When this relation was recorded
    confidence: float | None  # For inferred relations (0.0-1.0)
    metadata: dict | None   # Kind-specific data
```

**Example - Mentions:**
```python
# Message mentions a person entity
MultiRelation(
    uuid='rel_003',
    kind='mentions',
    source='msg_001',
    source_type='item',
    target='entity_alice',
    target_type='entity',
    realized_at=datetime.now(),
    confidence=0.95,         # NLP-inferred
    metadata={'span': [45, 50]}  # Character positions in content
)
```

**Example - Derived From:**
```python
# Summary derived from multiple source items
MultiRelation(
    uuid='rel_004',
    kind='derived_from',
    source='summary_001',
    source_type='item',
    target='email_001',
    target_type='item',
    realized_at=datetime.now(),
    confidence=None,         # Explicit, not inferred
    metadata=None
)
# Additional relation for second source
MultiRelation(
    uuid='rel_005',
    kind='derived_from',
    source='summary_001',
    source_type='item',
    target='email_002',
    target_type='item',
    ...
)
```

### Relation Lifecycle

Relations can live in either Core (mutable) or Soil (immutable), reflecting their lifecycle state:

```
┌─────────────────┐      fossilize      ┌─────────────────┐
│  Core (mutable) │  ───────────────►   │ Soil (immutable)│
│                 │                     │                 │
│  - Active       │                     │  - Archived     │
│  - Editable     │                     │  - Referenced   │
│  - Organizational│                    │  - Structural   │
└─────────────────┘                     └─────────────────┘
```

**Guidelines:**
- **Structural relations** (triggers, replies_to) → Created directly in Soil
- **Organizational relations** (project membership) → Live in Core, fossilize when project closes
- **Interpretive relations** (mentions) → May live in Core if user-correctable, or Soil if system-authoritative

### Inline References vs Relation Table

**Mentions** can be represented two ways:
1. **Inline in content**: Parsed on read, uses markdown link syntax with local schema
2. **In relation table**: Indexed for search, with confidence scores

Recommendation: Keep mentions as inline content (source of truth), optionally materialize to relation table as an index. Mark indexed relations as `inferred=true` in metadata so they're understood as derived.

### Query Abstraction

To allow future optimization (denormalizing to item attributes), all relation queries should go through an abstraction layer:

```python
def get_triggering_item(item_uuid: str) -> str | None:
    """
    Returns UUID of item that triggered this one, if any.
    
    Implementation note: Currently queries unique_relation table.
    May be optimized to check item attribute first in future.
    """
    return query_unique_relation(kind='triggers', target=item_uuid)

def get_superceding_item(item_uuid: str) -> str | None:
    """Returns UUID of item that supercedes this one, if any."""
    return query_unique_relation(kind='supercedes', target=item_uuid)

def get_mentions(item_uuid: str) -> list[str]:
    """Returns UUIDs of all entities/items mentioned by this item."""
    return query_multi_relation(kind='mentions', source=item_uuid)
```

---

## Conversation Structures

### ConversationLog

**Purpose:** Mutable container for append-only conversation history

**Schema:**
```python
@dataclass
class ConversationLog:
    uuid: str                           # Stable identifier
    parent_uuid: str | None             # Branch parent (null for root)
    items: list[str]                    # Item UUIDs in chronological order
    summary: Summary | None             # Present if collapsed

@dataclass
class Summary:
    timestamp: datetime
    author: str
    content: str                        # Summary text
    fragment_ids: list[str]             # Summary as fragment ID(s)
```

**Properties:**
- **References Items by UUID**: Items list contains UUIDs pointing to Soil
- **Append-only**: Items grow via append
- **Parent tracking**: `parent_uuid` establishes branch hierarchy
- **Summary indicates state**: 
  - `summary = None` → Active/ongoing conversation
  - `summary = {...}` → Collapsed/resolved exploration
- **Reopenable**: Summary can be invalidated, conversation resumed (creates new log)

**Lifecycle:**
```
Created → Active (summary=None) → Collapsed (summary set) → Reopened (new log created)
```

---

### Frame

**Purpose:** Tracks a participant's current working position in the branch tree

**Schema:**
```python
@dataclass
class Frame:
    branch_uuid: str        # Which ConversationLog this frame is working in
    head: str | None        # Item UUID of latest item in this frame's view
```

**Properties:**
- **Per-participant**: Each participant (user, agent) has their own frame
- **Independent positioning**: User and agent can work in different branches simultaneously
- **Append targeting**: When a participant creates content, it appends to their frame's branch
- **Head tracking**: Tracks the latest item the participant has seen/created

---

### Stack

**Purpose:** Records all branches in the project in insertion order

**Schema:**
```python
Stack = list[str]  # ConversationLog UUIDs in insertion order
```

**Properties:**
- **Insertion order**: UUIDs appear in the order branches were created
- **No repeats**: Each UUID appears exactly once
- **Tree structure via parent_uuid**: Branch hierarchy derived from ConversationLog.parent_uuid
- **Includes all branches**: Both active and collapsed branches remain in stack
- **Revisiting creates new UUID**: Reopening old conversation creates new log with new UUID

---

### Project

**Purpose:** Top-level container for entire project

**Schema:**
```python
@dataclass
class Project:
    stack: list[str]                    # Branch UUIDs in insertion order
    artifacts: ArtifactCollection       # UUID-based artifact store (Core)
    logs: dict[str, ConversationLog]    # uuid → ConversationLog
    frames: dict[str, Frame]            # participant_id → Frame
```

---

## Item Type Hierarchy Summary

```
Item (base: uuid, _type, realized_at, canonical_at) [Soil]
├── Note (description, summary?, title?)
│   └── Message (sender, recipient?, subject?, fragments: List[Fragment])
├── ToolCall (tool, operation, params, result?, caller, context?)
├── ArtifactCreated (artifact_uuid, label)
├── ArtifactDelta (artifact_uuid, commit, parent?, ops, references)
└── SystemEvent (event_type, payload?)

Fragment (id, content) [Inline within Message, not standalone Item]

UniqueRelation (kind, source, target, ...) [Soil or Core]
MultiRelation (kind, source, target, confidence?, ...) [Soil or Core]

Artifact (uuid, label, content, deltas, snapshots, label_history) [Core]
```

---

## Key Mechanisms

### 1. Fragment Generation

**Process:**
1. User/agent composes message
2. Server-side subagent fragments into semantic units
3. Each fragment gets hash-based ID
4. IDs are internal; users see resolved descriptive references

**Example:**
```
User input:
"I want the search bar at the top because mobile users need quick 
access, but it should collapse when scrolling to save space."

Fragmented (internal):
^a7f: "I want the search bar at the top because mobile users need quick access,"
^b2e: "but it should collapse when scrolling to save space."

Displayed to user:
"I want the search bar at the top because mobile users need quick 
access, but it should collapse when scrolling to save space."
(fragment boundaries invisible unless explicitly requested)
```

---

### 2. Reference Resolution

**References are opaque to users.** The underlying syntax is an implementation detail.

**Internal representation:**
```
"Use PostgreSQL instead - ^k3m shows SQLite won't scale"
"Update goals_doc:15 to reflect new storage decision"
"See [previous exploration](uuid_abc) for context"
```

**User sees:**
```
"Use PostgreSQL instead - [scalability analysis] shows SQLite won't scale"
"Update [goals_doc line 15] to reflect new storage decision"  
"See [previous exploration] for context"
```

**Resolution pipeline:**
```
Raw content → parse_references() → resolve each to metadata → render as styled element
```

**Reference metadata:**
```python
FragmentRef:     { type: 'fragment', id, preview, message_uuid }
ArtifactLineRef: { type: 'artifact_line', uuid, label, line, content }
LogRef:          { type: 'log', uuid, summary_or_first_fragment }
ItemRef:         { type: 'item', uuid, _type, preview }
```

---

### 3. Relation Chain Construction

When an Item causes another Item to be created, a UniqueRelation with kind='triggers' is recorded.

**Process:**
1. User creates Message
2. Agent processes and creates ToolCall → UniqueRelation(kind='triggers', source=Message, target=ToolCall)
3. ToolCall results in ArtifactDelta → UniqueRelation(kind='triggers', source=ToolCall, target=ArtifactDelta)
4. Agent responds with Message → UniqueRelation(kind='triggers', source=ArtifactDelta, target=Message)

**Benefits:**
- **Audit trail**: "Why did this happen?" traces back to root cause
- **Retrace capability**: Replay agent activity as readable trace
- **Causality visualization**: Tree views of effects from any Item
- **Debugging**: Step through chains to understand agent behavior

**Query Patterns:**

Forward traversal ("What did this cause?"):
```sql
WITH RECURSIVE chain AS (
    SELECT target FROM unique_relation WHERE source = ? AND kind = 'triggers'
    UNION ALL
    SELECT r.target FROM unique_relation r 
    JOIN chain c ON r.source = c.target 
    WHERE r.kind = 'triggers'
)
SELECT * FROM item WHERE uuid IN (SELECT target FROM chain)
```

Root finding ("What user action started this?"):
```sql
-- Traverse backward until hitting an Item with no inbound trigger
WITH RECURSIVE chain AS (
    SELECT source FROM unique_relation WHERE target = ? AND kind = 'triggers'
    UNION ALL
    SELECT r.source FROM unique_relation r 
    JOIN chain c ON r.target = c.source 
    WHERE r.kind = 'triggers'
)
SELECT * FROM chain WHERE source NOT IN (
    SELECT target FROM unique_relation WHERE kind = 'triggers'
)
```

---

### 4. Parallel Exploration

User and agent can work in different branches simultaneously.

**Scenario:**
```
uuid_2 contains discussion with 3 ideas raised.
User suggests exploring ideas in parallel.

1. Agent forks uuid_3 from uuid_2 to explore idea 1
2. User forks uuid_4 from uuid_2 to explore idea 2
3. Both work concurrently:
   - Agent appends to uuid_3
   - User appends to uuid_4

frames = {
    'agent': Frame(branch_uuid='uuid_3', head='item_uuid_9'),
    'user': Frame(branch_uuid='uuid_4', head='item_uuid_11'),
}
```

**Display:**
- Side-by-side view shows both active branches
- Swipe to switch focus between branches
- Each branch grows independently

---

### 5. Branch Lifecycle

#### Create Branch
```python
def fork_frame(project: Project, participant: str, new_uuid: str, parent_uuid: str):
    """Create new branch and point participant's frame at it."""
    project.logs[new_uuid] = ConversationLog(
        uuid=new_uuid,
        parent_uuid=parent_uuid,
        items=[],
        summary=None
    )
    project.stack.append(new_uuid)
    project.frames[participant] = Frame(branch_uuid=new_uuid, head=None)
```

#### Collapse Branch

A branch can only be collapsed if it has **no active children**.

```python
def can_collapse(project: Project, uuid: str) -> bool:
    """Branch can collapse only if no active children."""
    for log in project.logs.values():
        if log.parent_uuid == uuid and log.summary is None:
            return False
    return True

def collapse_branch(project: Project, uuid: str, summary: Summary):
    """Collapse a branch, archiving its items behind a summary."""
    if not can_collapse(project, uuid):
        raise ValueError("Cannot collapse branch with active children")
    
    log = project.logs[uuid]
    log.summary = summary
```

#### Reopen Branch
```
User: "Revisit the exploration in uuid_2"

System:
1. Creates NEW ConversationLog(uuid_5) with parent_uuid referencing context
2. First item references old exploration
3. Loads uuid_2 items as context for agent
4. Continues in new log

stack = ["uuid_1", "uuid_2", "uuid_3", "uuid_4", "uuid_5"]

Old uuid_2 preserved unchanged (summary remains set)
```

---

### 6. Shared Tool Model (Joint Cognitive System)

User and agent share the same tools with symmetric operations.

**ArtifactReader operations:**

| Operation | Agent invocation | User equivalent |
|-----------|------------------|-----------------|
| Find relevant content | `semantic_search(artifact, query)` | Search box, browse |
| Focus attention | `scroll_to(artifact, start, end)` | Scroll, tap line number |
| Expand context | `scroll_up(n)` / `scroll_down(n)` | Scroll gesture |
| Take notes | `note(content)` | Annotate (future) |
| Select for reference | `select_lines(artifact, start, end)` | Tap/drag select |
| Propose change | `propose_edit(artifact, range, content, reasoning)` | Stage edit |

**Observability modes:**

| Mode | Description |
|------|-------------|
| Independent (default) | User has own view; agent works in background with status indicator |
| Follow (opt-in) | User's view tracks agent's current attention live |
| Retrace (after) | Replay agent's activity via relation chain traversal |

---

### 7. Multi-Artifact Changes

**Single Message can trigger multiple artifact updates:**

```
Timeline Items:
[Message: uuid_m1, content="Switch to PostgreSQL", ...]
[ArtifactDelta: uuid_d1, artifact=goals_doc, ...]
[ArtifactDelta: uuid_d2, artifact=arch_diagram, ...]
[ArtifactDelta: uuid_d3, artifact=constraints, ...]

Relations (kind='triggers'):
UniqueRelation(source=uuid_m1, target=uuid_d1)
UniqueRelation(source=uuid_m1, target=uuid_d2)
UniqueRelation(source=uuid_m1, target=uuid_d3)

Each delta's references = [^m8n] (fragment from the Message)
```

---

## Data Storage Model

### Soil Database Schema (SQLite)

```sql
-- Items table
CREATE TABLE item (
    uuid TEXT PRIMARY KEY,
    _type TEXT NOT NULL,
    realized_at TEXT NOT NULL,  -- ISO 8601
    canonical_at TEXT NOT NULL, -- ISO 8601
    data JSON NOT NULL          -- Type-specific fields
);

CREATE INDEX idx_item_type ON item(_type);
CREATE INDEX idx_item_realized ON item(realized_at);
CREATE INDEX idx_item_canonical ON item(canonical_at);

-- Unique relations (1:1 per kind)
CREATE TABLE unique_relation (
    uuid TEXT PRIMARY KEY,
    kind TEXT NOT NULL,           -- 'triggers', 'supercedes', 'replies_to', 'continues'
    source TEXT NOT NULL,         -- UUID of source
    source_type TEXT NOT NULL,    -- 'item' | 'entity' | 'artifact'
    target TEXT NOT NULL,         -- UUID of target
    target_type TEXT NOT NULL,    -- 'item' | 'entity' | 'artifact'
    realized_at TEXT NOT NULL,    -- ISO 8601
    metadata JSON,
    UNIQUE(kind, target)          -- Each target appears at most once per kind
);

CREATE INDEX idx_unique_rel_source ON unique_relation(source);
CREATE INDEX idx_unique_rel_target ON unique_relation(target);
CREATE INDEX idx_unique_rel_kind ON unique_relation(kind);

-- Multi relations (N:N)
CREATE TABLE multi_relation (
    uuid TEXT PRIMARY KEY,
    kind TEXT NOT NULL,           -- 'mentions', 'derived_from', 'contains'
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target TEXT NOT NULL,
    target_type TEXT NOT NULL,
    realized_at TEXT NOT NULL,
    confidence REAL,              -- For inferred relations (0.0-1.0)
    metadata JSON
);

CREATE INDEX idx_multi_rel_source ON multi_relation(source);
CREATE INDEX idx_multi_rel_target ON multi_relation(target);
CREATE INDEX idx_multi_rel_kind ON multi_relation(kind);
```

### Core Storage Structure

```
/project_xyz/
  stack.json                    # List of branch UUIDs
  frames.json                   # Participant frames
  
  artifacts/
    art_uuid1/
      metadata.json             # uuid, label, label_history
      content.txt               # Current content
      snapshots/
        c4f2a1b.txt
        d5e6f7.txt
    art_uuid2/
      ...
  
  logs/
    uuid_1.json                 # ConversationLog
    uuid_2.json
    ...
  
  labels.json                   # label → uuid reverse lookup
  
  soil.db                       # SQLite database for Items and Relations
  
  core_relations.db             # SQLite for mutable relations (optional, or same db)
```

---

## Reference Parsing

```python
import re

def parse_references(content: str) -> list[dict]:
    """Extract all references from content."""
    refs = []
    
    # Fragment refs: ^<hash>
    for match in re.finditer(r'\^[a-z0-9]{3,4}', content):
        refs.append({
            'type': 'fragment',
            'id': match.group(),
            'span': match.span()
        })
    
    # Artifact refs: <label>:<line>[@<commit>]
    pattern = r'([\w_]+):(\d+)(?:@([a-f0-9]+))?'
    for match in re.finditer(pattern, content):
        refs.append({
            'type': 'artifact_line',
            'label': match.group(1),
            'line': int(match.group(2)),
            'commit': match.group(3),
            'span': match.span()
        })
    
    # Log refs: [text](uuid_xxx)
    for match in re.finditer(r'\[.*?\]\((uuid_[\w-]+)\)', content):
        refs.append({
            'type': 'conversation_log',
            'uuid': match.group(1),
            'span': match.span()
        })
    
    # Item refs: @<uuid>
    for match in re.finditer(r'@([a-z0-9_-]+)', content):
        refs.append({
            'type': 'item',
            'uuid': match.group(1),
            'span': match.span()
        })
    
    return refs
```

---

## Future Work / Identified Gaps

### 1. Fossilization Mechanism
**Status:** Conceptually designed, needs implementation

Relation strength decay for archiving inactive entities and relations:
- Access events strengthen relations
- Exponential decay over time
- Threshold triggers fossilization candidacy
- Hysteresis prevents boundary oscillation
- Fossilized relations may be denormalized to item attributes

### 2. Relation Semantics Formalization
**Status:** Deferred

- Exact metadata schema per relation kind
- Criteria for which relations start in Core vs Soil
- Confidence thresholds for inferred relations
- Ternary+ relations if needed (currently assuming binary sufficient)

### 3. Selector Syntax Formalization
**Status:** Deferred

Patterns identified but need formal grammar and parser.

### 4. Artifact Schema Definition
**Status:** Deferred

Currently inferred from content; formal schemas for future.

### 5. Timeline Visualization
**Status:** Planned as first UI experiment

OLLOS-inspired unified timeline of Items.

### 6. AI Suggestion UX
**Status:** Needs design

Patterns to explore:
- Ambient indicators
- Batch review
- Confidence-based visibility
- Undo-friendly actions
- Progressive disclosure

### 7. Cross-Project References
**Status:** Out of scope (MVP)

### 8. Multi-User Collaboration
**Status:** Future consideration

Current model assumes single user + agent.

### 9. Scratchpad/Working Memory
**Status:** Needs design

Shared working space for task duration, distinct from permanent log.

### 10. Voice Input Integration
**Status:** Future

Mobile-first voice input for fragment creation.

### 11. Relation Denormalization Path
**Status:** Documented, not implemented

Migration strategy for moving hot relations to item attributes:
1. Add nullable column to item table
2. Backfill from relation table
3. Update write path to populate both
4. Update read path to prefer attribute
5. Relation table remains source of truth for consistency checks

---

## Open Questions

1. **Scratchpad semantics:** How does working memory relate to conversation logs? Separate entity or embedded?

2. **Frame persistence:** Should frames persist across sessions, or reset?

3. **Parallel branch display:** Side-by-side vs tabs vs other patterns?

4. **Collapse summary format:** User-authored, agent-generated, or both?

5. **Fossilization storage:** Where do fossilized entities go? Cold storage, compressed, tombstoned?

6. **Reference autocomplete:** UX for creating references while typing?

7. **Relation query API:** Should relation queries return full items or just UUIDs?

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-12-26 | Initial draft with complete ontology |
| 0.2.0 | 2025-12-27 | Added ToolCall entity, Frame entity, clarified stack semantics (insertion order, tree via parent_uuid), parallel exploration model, JCS-informed shared tool design |
| 0.3.0 | 2025-12-29 | Storage layer split (Soil/Core); Item base type with hierarchy; dual timestamps (realized_at, canonical_at); `_type` field with CamelCase convention; `caller` field on ToolCall; ArtifactCreated as distinct Item type; Trigger relation for explicit causal chains; clarified Fragments as inline within Messages; ArtifactDelta includes artifact_uuid; database schema draft |
| 0.4.0 | 2025-12-29 | Generalized relations model with UniqueRelation and MultiRelation tables; relation kinds (triggers, supercedes, replies_to, mentions, derived_from, contains); relation lifecycle (Core↔Soil); reserved attribute names for future denormalization; query abstraction layer; removed standalone Trigger entity (now kind='triggers' in UniqueRelation) |
| 0.4.1 | 2025-12-31 | Added Entity Change Tracking section with hash chain pattern; hash and previous_hash fields in Core entity table for conflict detection and sync; EntityDelta type for Soil (future); Delta Notification Service schema; documented hash computation algorithm and conflict detection flow; linked ArtifactDelta to Entity change tracking pattern |

---

**Status:** Ready for prototype implementation  
**Next Steps:** 
1. Implement Soil database with Item and Relation tables
2. Implement Core storage for Artifacts
3. Build relation CRUD with query abstraction layer
4. Prototype timeline visualization
5. Implement fragment generation and reference parsing

---

**End of Document**
