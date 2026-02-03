# RFC-003: Context Mechanism v3

**Status:** Draft  
**Version:** 3.0  
**Date:** 2026-02-03  
**Supersedes:** RFC-003 v2

---

## Abstract

This RFC specifies the **Context Mechanism** for MemoGarden: a system for tracking operator and agent attention across objects, capturing working context in deltas, and maintaining view-streams for retrospective analysis and coordination.

The mechanism consists of three core components:
1. **ContextFrame:** Per-user and per-scope working memory (LRU-N of recently visited objects)
2. **View Stream:** Temporal record of actions forming a linked-list timeline
3. **Context Capture:** Automatic snapshot of relevant context into delta metadata

This revision focuses on **behavioral invariants** rather than implementation details, enabling optimization while maintaining semantic correctness.

---

## 1. Motivation

### 1.1 Problem Statement

MemoGarden serves as persistent substrate for human-AI collaboration. Current challenges:

**Lack of working context:** Operations occur in isolation. When user updates an artifact, system doesn't know "what else were they thinking about?" This makes:
- Delta context reconstruction difficult
- Agent handover lossy (agent doesn't know what operator was focusing on)
- Retrospective analysis limited (can't answer "what was I working on when I made this change?")

**No collaboration visibility:** When multiple contributors work on a scope, no mechanism to understand:
- Who did what, when
- How work transitioned between contributors
- What context informed each decision

**Attention scatter:** Without tracking focus, system can't distinguish:
- Active work (what I'm currently engaged with)
- Peripheral access (metadata lookups, search results)
- Historical review (browsing old data)

### 1.2 Design Goals

**G1. Capture working context:** Record what objects operator/agent is focusing on during work  
**G2. Enable context handover:** Support contributor transitions (operator â†’ agent, agent â†’ subagent)  
**G3. Support retrospective analysis:** Allow querying "what was I working on during this time period?"  
**G4. Maintain scope continuity:** Preserve scope view-stream across multiple contributors  
**G5. Minimize operator overhead:** Context tracking automatic, explicit control where needed  
**G6. Enable experimentation:** Defer implementation details to allow optimization  

---

## 2. Core Concepts

### 2.1 ContextFrame

**Definition:** A ContextFrame is a Core entity that maintains:
- **Owner:** User or Scope entity
- **Containers:** LRU-N list of recently visited object UUIDs (N=7 initially, tunable)
- **View timeline:** Ordered list of View UUIDs forming the view-stream

**Purpose:** Represents "what am I currently working on" for a user or scope.

**Ownership:**
- Each user has ONE primary ContextFrame
- Each scope has ONE primary ContextFrame
- Forked contexts (subordinate work) owned by subordinate agent

### 2.2 View Stream

**Definition:** A chronological, append-only record of actions taken by a user/scope, structured as a linked list of View entities.

**View:** Immutable record containing:
- **UUID:** Unique identifier
- **Actions:** List of operations performed (ViewAction objects)
- **Started/Ended:** Temporal boundaries
- **Previous:** Link to prior View (forms linked list, NULL for stream start)

**ViewAction:** Individual operation record:
```json
{
  "type": "update_entity",
  "target": "core_artifact_abc123",
  "timestamp": "2026-02-03T14:32:01Z",
  "visited": ["core_artifact_abc123", "core_note_def456"]
}
```

### 2.3 Context Capture

**Definition:** Automatic snapshot of ContextFrame's container list into delta metadata at time of mutation.

**Primary Context:** The contextually-relevant ContextFrame for a given operation:
- If mutated object in scope â†’ scope's ContextFrame
- Otherwise â†’ user's ContextFrame

**Delta metadata includes:**
```json
{
  "context": ["entity_1", "entity_2", "entity_3", ...],  // Up to N items
  "context_frame": "scope_abc123_context"  // Which context captured
}
```

---

## 3. Invariants (Prescribed Behavior)

These invariants define required system behavior. Implementations MUST satisfy these constraints.

### 3.1 View Identity

**INV-1: Unique View UUID**  
Each View has exactly ONE UUID. When an action occurs in scope context, the SAME View UUID is appended to both user and scope ContextFrames.

**Implementation freedom:** System MAY duplicate View data for performance, but MUST maintain single logical identity. Lookup by View UUID returns consistent data regardless of which ContextFrame referenced it.

---

### 3.2 Context Update Synchronization

**INV-2: Synchronized Append**  
When user visits object while scoped to project(s):
- ONE View created (single UUID)
- View appended to user's ContextFrame
- View appended to ALL active scope ContextFrames
- All appends occur atomically (appear in all streams or none)

---

### 3.3 Delta Context Capture

**INV-3: Primary Context Capture**  
Delta's `context` field captures the PRIMARY context at time of mutation:
- If mutated object belongs to scope â†’ scope's ContextFrame containers
- Otherwise â†’ user's ContextFrame containers
- Captured context MUST NOT exceed N items (LRU limit)

**INV-4: Automatic Capture**  
Context capture is automatic. System snapshots ContextFrame.containers when creating delta without caller intervention.

---

### 3.4 Fork and Merge

**INV-5: Fork Inheritance**  
When subordinate context forks from parent:
- New ContextFrame created with subordinate as owner
- Subordinate's initial containers COPIED from parent's containers at fork time
- Subsequent visits update subordinate's containers independently

**INV-6: Merge Termination**  
Upon merge:
- ViewMerge appended to BOTH parent and subordinate view-streams
- Subordinate's ContextFrame destroyed (entity deleted)
- Subordinate's view-stream terminates (no further appends)
- Subordinate's Views persist (immutable history, subject to eventual GC)

**INV-7: No Automatic Context Inheritance**  
Parent's context does NOT incorporate subordinate's context after merge. Parent MAY manually traverse subordinate's view-stream if desired.

---

### 3.5 Scope Suspension

**INV-8: Stream Suspension on Exit**  
When user exits scope:
- User's view-stream continues (user still active)
- Scope's view-stream suspended (no appends until another contributor enters)

**Consequence:** Scope view-streams are discontinuous, reflecting contributor handoffs.

---

### 3.6 View Chaining

**INV-9: Linked List Structure**  
Views form temporal linked list via `prev` pointer:
```
View_1 â†’ View_2 â†’ View_3 â†’ ViewMerge â†’ View_4
        (prev)   (prev)    (prev)      (prev)
```

**INV-10: ViewMerge Structure**  
ViewMerge extends View with:
- `prev`: Points to parent's previous View
- `metadata.merged_views`: List of subordinate view UUIDs being merged

---

### 3.7 Scope Activation

**INV-11: Explicit Scope Control**  
Scope activation is EXPLICIT:
- System MAY suggest scope activation (object belongs to scope A)
- User MUST confirm activation
- Object in multiple scopes â†’ user chooses which to activate
- System MUST display active scopes to user
- Users control scope through clear object boundaries

---

### 3.8 Context Size and Eviction

**INV-12: LRU-N Limit**  
Each ContextFrame maintains LRU-N of visited objects (N=7 initially):
- Context size MUST NOT exceed N
- New visit evicts least-recently-used when at capacity
- Eviction per-context (user's LRU-N independent of scope's LRU-N)
- Delta `context` field contains at most N objects

**INV-13: Tunable N**  
N=7 is initial value, subject to empirical adjustment based on usage patterns.

---

### 3.9 Context Persistence

**INV-14: Cross-Session Persistence**  
ContextFrames persist indefinitely across sessions:
- User logs out â†’ context preserved
- User logs in â†’ context restored
- No automatic timeout or decay

**INV-15: Persistent Users Only**  
Context persistence applies to:
- Operators (primary users)
- Primary agents (long-lived assistants)
- NOT subagents (spawned for specific tasks, destroyed after merge)

**INV-16: Explicit Context Break**  
System MUST provide operation to create context break:
- Breaks view-stream chain (next View has `prev = NULL`)
- ContextFrame.containers MAY remain unchanged (implementation detail)
- Deltas created after break MUST NOT capture pre-break context
- Effect: Temporal boundary in view-stream ("new chapter")

---

### 3.10 View Immutability

**INV-17: User Immutability**  
Users CANNOT modify Views after creation. Views are write-once from user perspective.

**INV-18: System Fossilization**  
System MAY compress Views for storage efficiency:
- Compression MUST preserve semantic meaning
- Compressed View MUST indicate compression in metadata
- Example: Multiple edits to same artifact â†’ single summarized edit
- View UUID remains stable across compression

**INV-19: Append-Only Streams**  
View-streams are append-only. No retroactive modification except:
- Entire View deletion by GC
- System compression per INV-18

---

### 3.11 Context Filtering

**INV-20: Write-Time Filtering**  
When object visited, system MUST classify as primitive or substantive:
- **Substantive:** Added to ContextFrame.containers (LRU-N)
- **Primitive:** NOT added to containers, MAY appear in ViewAction metadata

**INV-21: Classification Stability**  
Object type classification (primitive/substantive) MUST NOT change at runtime.

**INV-22: Default Policy**  
System behavior for unclassified types is implementation-defined, but MUST be consistent.

---

### 3.12 Visit Semantics

**INV-23: Visit Updates Context**  
ANY operation that visits an object MUST update context:
- Add object to ContextFrame.containers (if substantive)
- Update LRU ordering
- Context update synchronous (completes before operation returns)

**INV-24: Metadata-Only Non-Visiting**  
Operations accessing only metadata MUST NOT update context:
- `get_metadata(uuid)` â†’ no context update
- `search(query)` â†’ no context update (until results accessed)

**INV-25: Explicit Visit Control**  
Operations MUST provide mechanism to suppress visit tracking when needed.  
Default behavior SHOULD be visit=true (conservative).

---

### 3.13 Context Ownership

**INV-26: One Primary Context per Owner**  
Each owner (user or scope) has exactly ONE primary ContextFrame:
- User cannot have multiple primary contexts simultaneously
- Scope cannot have multiple primary contexts simultaneously
- Forked contexts owned by different entities (subordinate, not original owner)

---

## 4. Scope Continuity

**Design Principle:** Scopes are persistent entities representing life goals or major projects, involving multiple contributors (operators and agents) potentially specializing in different roles.

**View-Stream Continuity:**
- Scope view-stream reflects contributions of all contributors
- Work handed from one contributor to another
- No loss of continuity unless intended (context break)
- Discontinuous timeline natural (contributors come and go)

**Example Timeline:**
```
Operator works on Scope A (9am-11am)
  â†’ Scope A view-stream: [View_1, View_2, View_3]
  
Operator exits Scope A, Agent enters (11am-2pm)
  â†’ Scope A view-stream: [View_1, View_2, View_3, View_4, View_5]
  
Agent exits, Operator re-enters (2pm-5pm)
  â†’ Scope A view-stream: [...View_5, View_6, View_7]
```

Each contributor maintains own personal view-stream while also appending to scope's shared stream.

---

## 5. Implementation Guidance (Non-Normative)

These are suggested approaches, not requirements.

### 5.1 ContextFrame Schema

```python
@dataclass
class ContextFrame:
    """Core entity representing working context."""
    uuid: str                    # Entity UUID
    owner_id: str                # User or Scope UUID
    owner_type: str              # "user" | "scope"
    containers: list[str]        # LRU-N of object UUIDs (max N items)
    views: list[str]             # Timeline of View UUIDs
    created_at: datetime
    primary: bool = True         # False for destroyed/merged contexts
```

**Indexing:**
```sql
CREATE INDEX idx_context_owner ON context_frame(owner_id, owner_type, primary);
```

### 5.2 View Schema

```python
@dataclass
class View:
    """Immutable action record in view-stream."""
    uuid: str
    context_frame: str           # Owner's ContextFrame UUID
    actions: list[ViewAction]
    started_at: datetime
    ended_at: datetime | None    # NULL if active
    prev: str | None             # Previous View UUID (linked list)
    compressed: bool = False     # True if fossilized

@dataclass
class ViewAction:
    """Individual operation in View."""
    type: str                    # "get_entity", "update_entity", etc.
    target: str                  # Primary object UUID
    timestamp: datetime
    visited: list[str]           # All objects accessed (for metadata)
    
@dataclass
class ViewMerge(View):
    """Special View marking merge point."""
    merged_views: list[str]      # Subordinate view UUIDs
    merge_strategy: str          # "subordinate_complete", etc.
```

### 5.3 Context Update Hook

```python
def _track_visit(func):
    """Decorator to update context after operation."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Execute operation
        result = func(self, *args, **kwargs)
        
        # Extract visited objects
        visited = self._extract_visited(func.__name__, args, kwargs, result)
        
        # Filter substantive objects
        substantive = [uuid for uuid in visited if self._is_substantive(uuid)]
        
        if substantive:
            # Get current user and active scopes
            user_id, _ = get_current_user()
            scope_ids = self._get_active_scopes(user_id)
            
            # Create action
            action = ViewAction(
                type=func.__name__,
                target=substantive[0],
                timestamp=datetime.utcnow(),
                visited=visited
            )
            
            # Update contexts
            view_uuid = self._append_to_streams(
                user_id=user_id,
                scope_ids=scope_ids,
                action=action,
                visited=substantive
            )
        
        return result
    return wrapper
```

### 5.4 Context Capture Implementation

```python
def _create_delta(self, entity_uuid: str, changes: dict) -> Delta:
    """Create delta with automatic context capture."""
    # Determine primary context
    scope_id = self._get_entity_scope(entity_uuid)
    
    if scope_id:
        # Entity in scope â†’ capture scope's context
        context_frame = self._get_context_frame(scope_id, "scope")
    else:
        # Personal entity â†’ capture user's context
        user_id, _ = get_current_user()
        context_frame = self._get_context_frame(user_id, "user")
    
    # Snapshot containers (up to N items)
    context_snapshot = context_frame.containers[:self.config.context_size]
    
    delta = Delta(
        uuid=self._generate_uuid("soil"),
        entity_uuid=entity_uuid,
        changes=changes,
        context=context_snapshot,
        context_frame=context_frame.uuid,
        applied_at=datetime.utcnow()
    )
    
    return delta
```

### 5.5 Dual-Append Strategy

**Option A: Denormalized (Duplicate Views)**
```python
def _append_to_streams(self, user_id, scope_ids, action, visited):
    """Create separate View for each stream."""
    view_uuid = generate_uuid("core")
    
    # User's stream
    self._create_view_record(view_uuid, user_id, "user", action)
    
    # Scope streams (same UUID, duplicated data)
    for scope_id in scope_ids:
        self._create_view_record(view_uuid, scope_id, "scope", action)
    
    # Update all contexts (LRU)
    self._update_context(user_id, "user", visited)
    for scope_id in scope_ids:
        self._update_context(scope_id, "scope", visited)
    
    return view_uuid
```

**Option B: Normalized (Single View, Multiple References)**
```python
def _append_to_streams(self, user_id, scope_ids, action, visited):
    """Single View referenced by multiple ContextFrames."""
    view_uuid = generate_uuid("core")
    
    # Single View record
    self._create_view_record(view_uuid, action)
    
    # Reference from user's ContextFrame
    self._add_view_reference(user_id, "user", view_uuid)
    
    # Reference from scope ContextFrames
    for scope_id in scope_ids:
        self._add_view_reference(scope_id, "scope", view_uuid)
    
    # Update contexts
    # ... same as Option A
    
    return view_uuid
```

Both satisfy invariants. Choice is optimization trade-off.

### 5.6 Context Break Implementation

```python
def context_break(self) -> None:
    """Create temporal boundary in view-stream."""
    user_id, _ = get_current_user()
    context_frame = self._get_context_frame(user_id, "user")
    
    # Mark current View as ended
    if context_frame.views:
        current_view = self._get_view(context_frame.views[-1])
        current_view.ended_at = datetime.utcnow()
        self._save_view(current_view)
    
    # Next View will have prev=NULL (implementation detail)
    # ContextFrame.containers handling per INV-16:
    # - MAY clear: context_frame.containers = []
    # - MAY keep: no modification
    # - MUST ensure: next delta doesn't capture pre-break context
    
    # Example: Tag ContextFrame with break marker
    context_frame.last_break_at = datetime.utcnow()
    self._save_context_frame(context_frame)
```

Then in delta creation:
```python
def _create_delta(self, entity_uuid, changes):
    # ... determine context_frame ...
    
    # Check for recent context break
    if context_frame.last_break_at:
        elapsed = datetime.utcnow() - context_frame.last_break_at
        if elapsed < timedelta(seconds=1):  # Just broke
            context_snapshot = []  # Don't capture pre-break context
        else:
            context_snapshot = context_frame.containers
    else:
        context_snapshot = context_frame.containers
    
    # ... create delta with context_snapshot ...
```

---

## 6. Edge Cases and Open Questions

### 6.1 Concurrent Scope Access

**Scenario:** Two users in same scope simultaneously, both visit entity X.

**Behavior:**
- Two separate Views created (different UUIDs, different users)
- Both Views appended to scope's view-stream
- If one user on main context, other on forked context:
  - Main: View appends to scope's primary ContextFrame
  - Fork: View appends to subordinate's ContextFrame
  - Both contexts exist (different owners per INV-26)

### 6.2 Subordinate Never Merges

**Scenario:** Agent crashes, forked context never merged.

**Recovery:**
- Supervisor detects crash, attempts recovery
- If recovery succeeds: normal merge
- If abandoned: subordinate ContextFrame eligible for GC
- Subordinate's Views persist (orphaned but queryable)

### 6.3 Stale Context References

**Scenario:** Entity X in context, then X superseded/deleted.

**Behavior:** Keep stale reference in ContextFrame.containers.

**Rationale:** Context is historical ("what was I working on"), not current state. Superseded entities still meaningful for retrospection.

### 6.4 View Coalescence Timeout

**Open:** How long after last action before View ends?

**Guidance:** Implementation-defined. Suggested: 5 minutes of inactivity.

### 6.5 Context Size Tuning

**Open:** Is N=7 optimal?

**Guidance:** Empirical tuning required. Start with 7, adjust based on:
- User feedback ("context feels too narrow/too wide")
- Delta analysis (are captured contexts meaningful?)
- Memory pressure (larger N = more storage)

---

## 7. Integration with Existing RFCs

### 7.1 RFC-002: Relation Time Horizons

Context mechanism complements time horizons:
- **Time horizon:** Determines relation significance decay
- **Context:** Determines "what was I thinking about" for delta
- **Together:** Enable fossilization policy ("keep deltas where context was significant")

### 7.2 RFC-005: API Design

Context tracking integrated into semantic verbs:
```python
# Full API
def get_entity(self, uuid: str, *, visit: bool = True) -> Entity:
    """Get entity, optionally tracking visit."""

def get_metadata(self, uuid: str) -> ObjectMetadata:
    """Get metadata without visit."""

def context_break(self) -> None:
    """Create temporal boundary in view-stream."""

# Internal (not exposed via HTTP yet)
def get_context(self) -> list[str]:
    """Return current context (LRU-N)."""
```

### 7.3 RFC-007: Runtime Operations

Context mechanisms add background tasks:
- View coalescence (end inactive Views)
- Context GC (cleanup destroyed subordinate contexts)
- View compression (fossilization)

---

## 8. Future Work (Deferred)

### 8.1 Automatic Context Inference

Detect patterns in user behavior, suggest context activation:
- "You've opened 3 files from Project A, activate scope?"
- Machine learning on co-access patterns
- Fuzzy context boundaries

### 8.2 Context Templates

Predefined context patterns for common workflows:
- "Morning review" context
- "Deep work" context
- "Triage" context

### 8.3 Multi-Device Context Sync

Each user-device pair has own view-stream, sync mechanism TBD:
- Conflict resolution (concurrent edits from phone + laptop)
- Offline operation
- Eventual consistency

### 8.4 Context Visualization

Dashboard showing:
- Current context (what's in LRU-N)
- Context transitions over time
- Co-access graphs (what objects typically worked on together)

---

## 9. Implementation Checklist

### Phase 1: Core Mechanism (MVP)

- [ ] ContextFrame entity in Core schema
- [ ] View and ViewAction schema
- [ ] LRU-N container tracking
- [ ] Context capture in delta creation
- [ ] Visit tracking decorator
- [ ] Primitive/substantive classification

### Phase 2: Scope Support

- [ ] Scope entity definition
- [ ] Dual-append implementation
- [ ] Scope activation/deactivation verbs
- [ ] Active scope display in UI

### Phase 3: Fork/Merge

- [ ] Fork context creation
- [ ] ViewMerge schema and logic
- [ ] Subordinate context destruction
- [ ] Merge recovery procedures

### Phase 4: Lifecycle Management

- [ ] View coalescence (timeout-based)
- [ ] Context break operation
- [ ] Context GC policies
- [ ] View compression (fossilization)

---

## 10. Terminology

**Context:** The set of objects currently in working memory (ContextFrame.containers)  
**View:** Immutable record of actions within a time window  
**View-Stream:** Chronological sequence of Views forming timeline  
**Primary Context:** The contextually-relevant ContextFrame for an operation  
**Scope:** First-class MemoGarden entity for organizing work (not "Project")  
**Visit:** Operation that accesses object content and updates context  
**Substantive Object:** Object type added to context when visited  
**Primitive Object:** Object type excluded from context (metadata only)  
**Context Break:** Temporal boundary in view-stream, starts new chapter  

**Note on Projects:** "Project" refers to Project Studio's implementation layer built atop MemoGarden Scopes. This RFC uses "Scope" for MemoGarden's first-class entity.

---

## References

### Related Documents

- **RFC-001 v4:** Security & Operations Architecture
- **RFC-002 v5:** Relation Time Horizon & Fossilization
- **RFC-005 v3:** API Design (Message-Passing Semantics)
- **RFC-007 v1:** Runtime Operations
- **PRD v0.10.0:** MemoGarden Core Ontology

### Influences

- **Information Foraging Theory** (Pirolli & Card, 1999): Attention as information scent
- **Activity-Centered Computing:** Task context as organizing principle
- **MemGPT Architecture:** Memory blocks scoped to agent sessions
- **Working Memory Models:** Miller's "7Â±2" capacity limit

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-18 | Initial: view-stream, context frames, ViewLinkIndex, ContextLink |
| 2.0 | 2025-01-20 | Simplification: removed ViewLinkIndex, ContextLink auto-generation, made View ephemeral |
| 3.0 | 2026-02-03 | **Invariant-focused revision:** 26 behavioral invariants, scope continuity, fork/merge semantics, dual-append clarification, context break specification, fossilization compression, deferred implementation details |

---

**Status:** Draft  
**Next Steps:**
1. Review invariants with stakeholders
2. Implement ContextFrame + View schema in Core
3. Add context tracking to internal API operations
4. Build scope activation UI
5. Test fork/merge with real agent delegation
6. Tune context size (N) based on usage data

---

**END OF RFC**
