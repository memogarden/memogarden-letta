# RFC-003: Context Capture Mechanism

**Version:** 2.0  
**Status:** Draft  
**Author:** MemoGarden Project  
**Created:** 2025-01-18  
**Last Updated:** 2025-01-20

## Abstract

This RFC specifies the context capture mechanism for MemoGarden, a system for tracking patterns of attention that complements the existing timeline (Soil) and fossilization systems. Context operates as an **ephemeral view-stream** capturing *what was observed*, with meaningful co-access patterns captured at mutation time via the `ArtifactDelta.context` field. This design eliminates the need for intermediate view-to-relation pipelines.

## Motivation

MemoGarden's existing architecture captures structural facts (system relations like citations and triggers) and engagement signals (user relations with time horizons), but lacks a mechanism to understand *attention patterns*â€”what the operator and agents were looking at when they took action. This creates several limitations:

1. **No co-access tracking**: When user references artifact A while editing artifact B, the citation relation captures the structural link, but not that both were *in focus together*
2. **No context for decisions**: An ArtifactDelta records what changed, but not what information informed that change
3. **No collaborative understanding**: When agent takes over a task, it lacks visibility into what the previous operator was examining

The context mechanism addresses these by introducing:
- **View-stream**: Ephemeral ringbuffer of attention events (~24hr retention)
- **ContextFrame**: LRU set tracking current working attention state
- **Delta context capture**: Snapshot of ContextFrame at mutation time

---

## Design Principles

1. **View-stream is ephemeral**: Views are not permanent facts; they're operational state
2. **Context captured at mutation**: The meaningful signal is what was in focus when decisions were made
3. **Retrospective analysis**: Co-access patterns derived from delta history, not automatic relation creation
4. **Single participant per frame**: Simplifies access control and state management
5. **Viewable vs Contained**: Only container-level entities generate views
6. **Integer arithmetic only**: Consistent with MemoGarden's resource constraints

---

## Core Architecture

### View-stream vs Delta-stream

MemoGarden maintains two complementary streams:

| Property | Delta-stream (existing) | View-stream (new) |
|----------|------------------------|-------------------|
| **What it captures** | State mutations | Attention events |
| **Examples** | ArtifactDelta, Message | View entries |
| **Storage** | Soil (permanent) | Core (ephemeral ringbuffer) |
| **Retention** | Indefinite | ~24hr or N entries |
| **Relations formed** | System relations (cites, triggers) | None directly; context in deltas |

**Key insight**: When user sends a message referencing artifact A, two things happen:
- **Delta**: Message item created in Soil (permanent change)
- **View**: User's attention to artifact A recorded in ephemeral ringbuffer (operational state)
- **Context**: If this triggers an ArtifactDelta, the ContextFrame snapshot is captured in `delta.context`

### Two-Tier Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ ContextFrame (mutable, in Core)                                 â”‚
â”‚   - Single participant per frame                                â”‚
â”‚   - LRU set of N unique container UUIDs                         â”‚
â”‚   - Represents "what's in focus right now"                      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                          â”‚
                          â”œâ”€â”€â–º State mutation (message, artifact edit)
                          â”‚
                          â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ ArtifactDelta.context (in Soil, permanent)                      â”‚
â”‚   - Snapshot of ContextFrame.containers at mutation time        â”‚
â”‚   - Enables retrospective co-access analysis                    â”‚
â”‚   - No intermediate relation creation needed                    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ View Ringbuffer (ephemeral, in Core)                            â”‚
â”‚   - ~24hr retention or N entries                                â”‚
â”‚   - Browsing history semantics (back-button mental model)       â”‚
â”‚   - Monotonic, chronological: Aâ†’Bâ†’Aâ†’B produces [A,B,A,B,...]    â”‚
â”‚   - No permanence expectation                                   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Viewable vs Contained Entities

Not all entities generate Views. The distinction is between **containers** (viewable, generate Views) and **contained items** (no standalone Views):

| Viewable (generates Views) | Contained (no standalone Views) |
|---------------------------|--------------------------------|
| Artifact | Message, Note, ToolCall |
| ConversationLog | Fragment |
| Project | Individual Transaction |
| Entity collections | SystemEvent |

**Rationale**: Attention is tracked at container granularity. Structure within containers is captured via anchors.

**Anchor syntax for precise references**: `container_uuid#position`

Examples:
- `core_convolog_abc#soil_item_xyz` (specific item within a conversation log)
- `core_artifact_def#145` (line 145 of an artifact)

**Implication**: Views capture containers; structure captured via anchors. Attention is coarse, structure is precise.

---

## Entity Definitions

### View (Ephemeral)

**Purpose:** Records attention event in the view stream ringbuffer

**Schema:**
```python
@dataclass
class View:
    # NOT an Item - lives in ephemeral ringbuffer, not Soil
    subject: str              # Participant ID (user/agent who viewed)
    container: str            # Viewable entity UUID (core_ prefix)
    anchor: str | None        # Position within container (optional)
    timestamp: datetime       # When view occurred
    actions: list[ViewAction] # Non-mutating actions during this view

@dataclass
class ViewAction:
    action_type: str    # 'scroll' | 'search' | 'select'
    timestamp: datetime
    params: dict        # Action-specific parameters
```

**Properties:**
- **Not an Item**: Lives in ephemeral ringbuffer, not Soil
- **Coalesces actions**: Actions accumulate until container loses focus or mutation occurs
- **Bounded retention**: ~24hr or N entries (configurable)
- **Browsing history semantics**: Monotonic and chronological

**View Coalescence:**
```python
def on_container_focus(participant: str, container_uuid: str, anchor: str | None):
    """Called when participant focuses on a container."""
    
    ringbuffer = get_view_ringbuffer(participant)
    
    # Always append new entry (browsing history semantics)
    view = View(
        subject=participant,
        container=container_uuid,
        anchor=anchor,
        timestamp=now(),
        actions=[]
    )
    ringbuffer.append(view)

def on_view_action(participant: str, action: ViewAction):
    """Called for non-mutating actions (scroll, search, select)."""
    
    ringbuffer = get_view_ringbuffer(participant)
    if ringbuffer.current_view:
        ringbuffer.current_view.actions.append(action)
```

### ContextFrame

**Purpose:** Tracks current working attention state as an LRU set of unique containers

**Schema:**
```python
@dataclass
class ContextFrame:
    uuid: str                   # Stable identifier (core_ prefix)
    project_uuid: str           # Which project this context belongs to
    participant: str            # Single participant per frame
    containers: list[str]       # LRU-ordered UUIDs, max N unique
    created_at: datetime
    parent_frame_uuid: str | None  # If forked from another frame
```

**Properties:**
- **Single participant per frame**: Simplified from multi-participant model
- **LRU semantics**: Access promotes container to front; no duplicates
- **Bounded size**: N configurable (e.g., 20 containers)
- **Represents working set**: "What's in focus right now"

**LRU Operations:**
```python
MAX_CONTAINERS = 20  # Configurable

def context_frame_access(frame: ContextFrame, container_uuid: str):
    """Record that participant is attending to this container."""
    
    # Remove if already present (will re-add at front)
    if container_uuid in frame.containers:
        frame.containers.remove(container_uuid)
    
    # Add to front (most recent)
    frame.containers.insert(0, container_uuid)
    
    # Enforce bound
    if len(frame.containers) > MAX_CONTAINERS:
        frame.containers = frame.containers[:MAX_CONTAINERS]

def context_frame_snapshot(frame: ContextFrame) -> list[str]:
    """Return current state for embedding in delta."""
    return frame.containers.copy()
```

### ArtifactDelta.context Field

**Purpose:** Captures what was in focus when change was made

**Schema addition:**
```python
@dataclass
class ArtifactDelta(Item):
    # ... existing fields ...
    artifact_uuid: str
    commit: str
    parent: str | list[str] | None
    ops: str
    references: list[str]
    context: list[str]  # NEW: Snapshot of ContextFrame.containers at mutation time
```

**Context Capture on Mutation:**
```python
def create_artifact_delta(
    artifact_uuid: str,
    ops: str,
    references: list[str],
    participant: str
) -> ArtifactDelta:
    """Create delta with context snapshot."""
    
    frame = get_context_frame(participant)
    
    delta = ArtifactDelta(
        uuid=generate_soil_uuid(),
        _type='ArtifactDelta',
        realized_at=now(),
        canonical_at=now(),
        artifact_uuid=artifact_uuid,
        commit=compute_new_commit_hash(),
        parent=get_current_commit(artifact_uuid),
        ops=ops,
        references=references,
        context=context_frame_snapshot(frame)  # Capture what was in focus
    )
    
    create_item(delta)
    return delta
```

---

## Context Capture Rules

### What Triggers Context Capture

Context is captured **only on state-mutating actions**:

| Action Type | Captures Context? | Notes |
|-------------|-------------------|-------|
| ArtifactDelta created | âœ“ | Primary use case |
| Message sent | âœ— | Message itself doesn't have context field |
| ToolCall executed | âœ— | But resulting delta does |
| Browsing/scrolling | âœ— | Non-mutating; recorded in View.actions |
| Search query | âœ— | Non-mutating; recorded in View.actions |

**Principle**: Context answers "what was the operator looking at when they made this change?"

### ContextFrame â†” ConversationLog Cardinality

**Many-to-many relationship:**
- ConversationLog can be visited by multiple participants (multiple ContextFrames)
- ContextFrame may show attention across multiple ConversationLogs (each as a container)

---

## Retrospective Analysis

### Deriving Co-Access from Delta History

Co-access patterns are derived by analyzing `delta.context` arrays:

```python
def find_co_accessed_artifacts(artifact_uuid: str, time_window_days: int = 30) -> dict[str, int]:
    """Find artifacts that were in context when this artifact was modified."""
    
    deltas = query_artifact_deltas(
        artifact_uuid=artifact_uuid,
        since=current_day() - time_window_days
    )
    
    co_access_counts = defaultdict(int)
    for delta in deltas:
        for context_uuid in delta.context:
            if context_uuid != artifact_uuid:
                co_access_counts[context_uuid] += 1
    
    return dict(co_access_counts)

def find_artifacts_modified_while_viewing(viewed_uuid: str) -> list[str]:
    """Find artifacts that were modified while this artifact was in context."""
    
    deltas = query_all_deltas_with_context_containing(viewed_uuid)
    return [d.artifact_uuid for d in deltas]
```

### Query Patterns

**What was in focus during artifact edit?**
```sql
SELECT context FROM item 
WHERE _type = 'ArtifactDelta' 
AND json_extract(data, '$.artifact_uuid') = ?
ORDER BY realized_at DESC
LIMIT 10;
```

**Which artifacts are frequently co-accessed?**
```python
def compute_co_access_graph(project_uuid: str) -> dict[tuple[str, str], int]:
    """Build graph of artifact co-access weights."""
    
    deltas = query_all_artifact_deltas(project_uuid)
    edge_weights = defaultdict(int)
    
    for delta in deltas:
        context = delta.context
        # All pairs in context are co-accessed
        for i, a in enumerate(context):
            for b in context[i+1:]:
                edge = tuple(sorted([a, b]))
                edge_weights[edge] += 1
    
    return dict(edge_weights)
```

---

## Context Frame Lifecycle

### Creation

Context frames are created for:
- New project participation
- Task delegation (fork creates new frame)

```python
def create_context_frame(project_uuid: str, participant: str) -> ContextFrame:
    return ContextFrame(
        uuid=generate_core_uuid(),
        project_uuid=project_uuid,
        participant=participant,
        containers=[],
        created_at=now(),
        parent_frame_uuid=None
    )
```

### Delegation Patterns

**Fork (concurrent work):**
```python
def fork_context_frame(frame: ContextFrame, new_participant: str) -> ContextFrame:
    """Create new frame for delegated work, preserving context."""
    
    new_frame = ContextFrame(
        uuid=generate_core_uuid(),
        project_uuid=frame.project_uuid,
        participant=new_participant,
        containers=frame.containers.copy(),  # Inherit current context
        created_at=now(),
        parent_frame_uuid=frame.uuid
    )
    return new_frame
```

**Handover (blocking):**
```python
def handover_context_frame(frame: ContextFrame, to_participant: str):
    """Transfer frame ownership (original participant blocks)."""
    
    frame.participant = to_participant
    # Original participant gets frame back when task completes
```

### Focus Tracking

**Open question (KIV):** How does system determine container "has focus" for View session boundaries?

**Proposed approach:** Infer from mutation target + timeout fallback (preferred over explicit heartbeats)

```python
FOCUS_TIMEOUT_SECONDS = 300  # 5 minutes

def infer_focus_change(participant: str, mutation_target: str):
    """Infer focus from mutation target."""
    
    frame = get_context_frame(participant)
    context_frame_access(frame, mutation_target)
    
    # Also update view ringbuffer
    on_container_focus(participant, mutation_target, anchor=None)
```

---

## Storage Schema

### Core Database

```sql
-- Context frames
CREATE TABLE context_frame (
    uuid TEXT PRIMARY KEY,              -- core_ prefix
    project_uuid TEXT NOT NULL,
    participant TEXT NOT NULL,
    containers JSON NOT NULL,           -- LRU-ordered list of container UUIDs
    created_at TEXT NOT NULL,           -- ISO 8601
    parent_frame_uuid TEXT,
    
    FOREIGN KEY (project_uuid) REFERENCES project(uuid),
    FOREIGN KEY (parent_frame_uuid) REFERENCES context_frame(uuid)
);

CREATE INDEX idx_context_frame_project ON context_frame(project_uuid);
CREATE INDEX idx_context_frame_participant ON context_frame(participant);

-- View ringbuffer (ephemeral, could be in-memory with periodic flush)
CREATE TABLE view_ringbuffer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant TEXT NOT NULL,
    container TEXT NOT NULL,
    anchor TEXT,
    timestamp TEXT NOT NULL,            -- ISO 8601
    actions JSON                        -- List of ViewAction
);

CREATE INDEX idx_view_participant ON view_ringbuffer(participant);
CREATE INDEX idx_view_timestamp ON view_ringbuffer(timestamp);

-- Cleanup old views (run periodically)
-- DELETE FROM view_ringbuffer WHERE timestamp < datetime('now', '-24 hours');
```

### Soil Database (ArtifactDelta.context)

The `context` field is stored in the existing `data` JSON column of the `item` table:

```sql
-- Query deltas with context
SELECT 
    uuid,
    json_extract(data, '$.artifact_uuid') as artifact_uuid,
    json_extract(data, '$.context') as context
FROM item
WHERE _type = 'ArtifactDelta'
AND json_extract(data, '$.artifact_uuid') = ?;
```

---

## Metrics & Observability

### Core Metrics

```python
@dataclass
class ContextMetrics:
    # Frame activity
    active_context_frames: int
    avg_containers_per_frame: float
    context_frame_forks_per_day: int
    
    # View stream
    views_captured_per_hour: float
    avg_actions_per_view: float
    ringbuffer_size: int
    
    # Delta context
    avg_context_size_per_delta: float
    deltas_with_empty_context_pct: float
```

### Dashboard View

```
Context System Status                    [Last updated: 2026-01-20 14:32]

â”Œâ”€ Active Context Frames â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ project_main:     user      [â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ] 18 containers       â”‚
â”‚ email_triage:     agent     [â–ˆâ–ˆâ–ˆâ–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘]  4 containers       â”‚
â”‚ doc_analysis:     user      [â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘] 12 containers       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€ View Stream â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Ringbuffer: 847/1000 entries                                       â”‚
â”‚ Views/hr: 45 (avg)                                                  â”‚
â”‚ Oldest entry: 18 hours ago                                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€ Delta Context Coverage â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Last 24h: 156 deltas, avg 8.3 containers in context                â”‚
â”‚ Empty context: 3% (usually system-generated deltas)                â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Configuration

```python
@dataclass
class ContextConfig:
    # ContextFrame sizing
    max_containers_per_frame: int = 20
    
    # View stream sizing
    view_ringbuffer_max_entries: int = 1000
    view_retention_hours: int = 24
    
    # Focus tracking
    focus_timeout_seconds: int = 300  # Inactivity before focus considered lost
```

All parameters tunable based on hardware capabilities and observed behavior.

---

## Eliminated Concepts

The following concepts from RFC-003 v1 have been removed:

| Concept | Previous Design | Reason for Elimination |
|---------|-----------------|------------------------|
| ViewLinkIndex | Hot cache of ~100 co-access patterns | Context captured on mutation via `delta.context` |
| ContextLink relations | Auto-generated from index eviction | Co-access derived retrospectively from delta history |
| View-link promotion pipeline | Eviction â†’ ContextLink creation | No intermediate relation creation needed |
| Multi-participant ContextFrame | write/read participant sets | Simplified to single participant per frame |
| View as Soil Item | Views stored permanently | Views are ephemeral operational state |
| Significance tracking on views | View counts, time horizons | Not needed; analysis is retrospective |

**Key simplification:** The original design created automatic relations from attention patterns. The new design captures context at mutation time and derives patterns retrospectively. This eliminates intermediate state management and the complexity of view-to-relation pipelines.

---

## Integration with Existing Systems

### Relation to System Relations

**System relations** (triggers, cites) capture *structural facts*:
- Created when structural link established (e.g., inline reference parsed)
- Immutable facts in Soil
- Never decay

**Context capture** captures *attention state*:
- Captured at mutation time in `delta.context`
- Ephemeral view stream for operational use
- Patterns derived retrospectively, not stored as relations

### Relation to User Relations (RFC-002)

User relations remain the mechanism for explicit engagement signals with time horizon decay. Context does **not** automatically create user relations.

If operator wants to explicitly link items based on observed co-access patterns, they can create user relations manually (explicit_link kind).

### Relation to Fossilization (RFC-002)

Context data in deltas is permanent (lives in Soil with the delta). View ringbuffer is ephemeral and not subject to fossilization.

---

## Open Questions

### 1. Focus Tracking Mechanism

**Status:** Needs validation

How does system determine container "has focus" for View session boundaries?

**Current proposal:** Infer from mutation target + timeout fallback

**Alternative:** Explicit focus events from UI layer

### 2. Coalescence Timeout

**Status:** Needs tuning

How long after last action before View is considered "closed"?

**Current proposal:** 5 minutes (FOCUS_TIMEOUT_SECONDS)

### 3. View Ringbuffer Sizing

**Status:** Needs empirical tuning

Start with 1000 entries / 24hr retention. Adjust based on:
- Memory pressure
- Query patterns (how far back do we need?)

### 4. Context in Non-Artifact Deltas

**Status:** Deferred

Should Message and other Items also capture context? Currently only ArtifactDelta has the `context` field.

**Consideration:** Messages don't have a natural "what was modified" semantic, so context is less meaningful.

---

## Implementation Checklist

### Phase 1: Core Mechanism (MVP)

- [ ] ContextFrame entity in Core schema
- [ ] LRU container tracking
- [ ] Context capture on ArtifactDelta creation
- [ ] Basic metrics collection

### Phase 2: View Stream

- [ ] View ringbuffer table/structure
- [ ] View coalescence logic
- [ ] ViewAction accumulation
- [ ] Periodic cleanup of old views

### Phase 3: Context Frame Management

- [ ] Frame creation for new projects
- [ ] Fork semantics for delegation
- [ ] Handover semantics
- [ ] Focus tracking (inferred from mutations)

### Phase 4: Retrospective Analysis

- [ ] Co-access query functions
- [ ] Co-access graph computation
- [ ] Dashboard for context visibility

---

## References

### Influences

- **Information Foraging Theory** (Pirolli & Card, 1999): Attention as signal of information scent
- **Activity-Centered Computing**: Task context as organizing principle
- **MemGPT/Letta**: Memory blocks scoped to agent

### Related Documents

- **RFC-001 v4**: Security architecture, operational design
- **RFC-002 v5**: Relation time horizon & fossilization
- **PRD v0.6.0**: Core ontology, storage architecture
- **Design Review 2025-01-20**: Consolidated design decisions

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-18 | Initial specification: view-stream, context frames, view-link index, ContextLink relations |
| 2.0 | 2025-01-20 | **Major simplification from design review:** ViewLinkIndex eliminated; ContextLink auto-generation eliminated; View stream now ephemeral ringbuffer (not Soil); ContextFrame simplified to single participant; Context captured via ArtifactDelta.context; Viewable vs Contained distinction; Retrospective analysis replaces automatic relation creation |

---

**Status:** Draft  
**Next Steps:**
1. Implement ContextFrame with LRU container tracking
2. Add `context` field to ArtifactDelta creation
3. Build view ringbuffer for operational visibility
4. Implement retrospective co-access analysis queries

---

**END OF RFC**
