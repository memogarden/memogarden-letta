# RFC-003: Context Mechanism v4

**Status:** Draft  
**Version:** 4.0  
**Date:** 2026-02-06  
**Supersedes:** RFC-003 v3

---

## Abstract

This RFC specifies the **Context Mechanism** for MemoGarden: a system for tracking operator and agent attention across objects, capturing working context in deltas, and maintaining view-streams for retrospective analysis and coordination.

The mechanism consists of three core components:
1. **ContextFrame:** Per-user and per-scope working memory (LRU-N of recently visited objects)
2. **View Stream:** Temporal record of actions forming a linked-list timeline
3. **Context Capture:** Automatic snapshot of relevant context into delta metadata

This revision focuses on **behavioral invariants** rather than implementation details, enabling optimization while maintaining semantic correctness.

**v4.0 changes:** Verb alignment with RFC-005 v6 (enter/leave/focus/rejoin).

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
  "context": ["entity_1", "entity_2", "entity_3", ...],  // Up to N facts
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
- Captured context MUST NOT exceed N facts (LRU limit)

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

**INV-8: Stream Suspension on Leave**  
When user leaves scope (via `leave` verb):
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
Scope activation is EXPLICIT via `enter`, `leave`, `focus` verbs:
- `enter`: Add scope to user's active set
- `leave`: Remove scope from user's active set
- `focus`: Switch primary scope among active scopes
- System MAY suggest scope activation (object belongs to scope A)
- User MUST confirm activation
- Object in multiple scopes â†’ user chooses which to activate
- System MUST display active scopes to user
- Users control scope through clear object boundaries

**INV-11a: Focus Separation**  
Entering a scope does NOT automatically make it primary. User must explicitly `focus` to change primary scope. This enables easier audit of scope transitions.

**INV-11b: Implied Focus**  
Focus is implied when:
- Subagent is created (has only one scope)
- User first registered (has only one scope)

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

### 3.10 Visit Filtering

**INV-17: Substantive vs Primitive Objects**  
Not all object accesses update context:
- **Substantive objects:** Added to context when visited (artifacts, notes, contacts)
- **Primitive objects:** NOT added to context (schemas, system config, metadata-only lookups)

**INV-18: Type-Based Classification**  
Classification is type-based, not operation-based:
- Accessing artifact content â†’ substantive (updates context)
- Accessing artifact metadata only â†’ still substantive type, but no visit recorded
- Accessing schema definition â†’ primitive (never updates context)

**INV-19: Hardcoded Initial Classification**  
For MVP, substantive/primitive classification is hardcoded. Future versions may allow per-type configuration.

---

### 3.11 Scope Ownership

**INV-20: One Primary Context Per Owner**  
Each owner (user or scope) has exactly ONE primary ContextFrame at any time.

**INV-21: Subordinate Context Ownership**  
Forked contexts are owned by the subordinate agent, not the scope. This allows multiple subordinates to fork from same scope simultaneously.

---

### 3.12 View Coalescence

**INV-22: Action Grouping**  
Multiple actions within a time window coalesce into single View:
- Reduces storage overhead
- Maintains semantic grouping ("one work session")

**INV-23: Coalescence Boundaries**  
View ends when:
- Explicit boundary (user triggers context break)
- Inactivity timeout (implementation-defined, suggested: 5 minutes)
- Mutation to different scope

---

### 3.13 Fossilization Integration

**INV-24: View Stream Compression**  
Old Views subject to fossilization:
- Action lists may be summarized
- Visited object lists preserved (audit trail)
- Links to fossilized entities remain valid

**INV-25: Context Preservation in Deltas**  
Delta `context` field is preserved during fossilization:
- Enables retrospective analysis of "what was I thinking about"
- Not subject to LRU eviction (immutable once captured)

---

### 3.14 Concurrent Access

**INV-26: No Shared ContextFrame**  
Two contributors cannot share a ContextFrame:
- Same scope, different users â†’ each has own ContextFrame
- Scope's ContextFrame reflects aggregate (both Views appended)
- User A's context is A's alone, B's context is B's alone

---

## 4. API Integration

Context verbs are part of the Core bundle (RFC-005 v6):

### 4.1 Semantic API Verbs

**enter** - Add scope to active set
```json
{
  "op": "enter",
  "scope": "scp_xxx"
}
```
Response: `{scope, active_scopes: [...]}`

**leave** - Remove scope from active set
```json
{
  "op": "leave", 
  "scope": "scp_xxx"
}
```
Response: `{scope, active_scopes: [...]}`

**focus** - Switch primary scope
```json
{
  "op": "focus",
  "scope": "scp_xxx"
}
```
Response: `{scope, primary_scope, active_scopes: [...]}`

**rejoin** - Merge subordinate context back to parent
```json
{
  "op": "rejoin"
}
```
Response: `{merged_at, child_scope, parent_scope}`

### 4.2 Internal API Methods

```python
def enter_scope(self, scope_id: str) -> dict:
    """Add scope to active set."""

def leave_scope(self, scope_id: str) -> dict:
    """Remove scope from active set."""

def focus_scope(self, scope_id: str) -> dict:
    """Switch primary scope among active scopes."""

def rejoin(self) -> dict:
    """Merge subordinate context back to parent."""

def context_break(self) -> None:
    """Create temporal boundary in view-stream."""

def get_context(self) -> list[str]:
    """Return current context (LRU-N)."""

def get_active_scopes(self) -> list[str]:
    """Return list of active scope IDs."""

def get_primary_scope(self) -> Optional[str]:
    """Return primary scope ID or None."""
```

### 4.3 Visit Tracking

```python
def get_entity(self, uuid: str, *, visit: bool = True) -> Entity:
    """Get entity, optionally tracking visit."""

def get_metadata(self, uuid: str) -> ObjectMetadata:
    """Get metadata without visit."""
```

---

## 5. Edge Cases and Open Questions

### 5.1 Concurrent Scope Access

**Scenario:** Two users in same scope simultaneously, both visit entity X.

**Behavior:**
- Two separate Views created (different UUIDs, different users)
- Both Views appended to scope's view-stream
- If one user on main context, other on forked context:
  - Main: View appends to scope's primary ContextFrame
  - Fork: View appends to subordinate's ContextFrame
  - Both contexts exist (different owners per INV-26)

### 5.2 Subordinate Never Merges

**Scenario:** Agent crashes, forked context never merged.

**Recovery:**
- Supervisor detects crash, attempts recovery
- If recovery succeeds: normal merge via `rejoin`
- If abandoned: subordinate ContextFrame eligible for GC
- Subordinate's Views persist (orphaned but queryable)

### 5.3 Stale Context References

**Scenario:** Entity X in context, then X superseded/deleted.

**Behavior:** Keep stale reference in ContextFrame.containers.

**Rationale:** Context is historical ("what was I working on"), not current state. Superseded entities still meaningful for retrospection.

### 5.4 View Coalescence Timeout

**Open:** How long after last action before View ends?

**Guidance:** Implementation-defined. Suggested: 5 minutes of inactivity.

### 5.5 Context Size Tuning

**Open:** Is N=7 optimal?

**Guidance:** Empirical tuning required. Start with 7, adjust based on:
- User feedback ("context feels too narrow/too wide")
- Delta analysis (are captured contexts meaningful?)
- Memory pressure (larger N = more storage)

---

## 6. Integration with Existing RFCs

### 6.1 RFC-002: Relation Time Horizons

Context mechanism complements time horizons:
- **Time horizon:** Determines relation significance decay
- **Context:** Determines "what was I thinking about" for delta
- **Together:** Enable fossilization policy ("keep deltas where context was significant")

### 6.2 RFC-005: API Design

Context verbs integrated into Core bundle:
- `enter`, `leave`, `focus`, `rejoin` are Semantic API verbs
- Response envelope includes `actor` for audit
- Context verbs bundled with Core (not separate Context bundle)

### 6.3 RFC-007: Runtime Operations

Context mechanisms add background tasks:
- View coalescence (end inactive Views)
- Context GC (cleanup destroyed subordinate contexts)
- View compression (fossilization)

---

## 7. Future Work (Deferred)

### 7.1 Automatic Context Inference

Detect patterns in user behavior, suggest context activation:
- "You've opened 3 files from Project A, activate scope?"
- Machine learning on co-access patterns
- Fuzzy context boundaries

### 7.2 Context Templates

Predefined context patterns for common workflows:
- "Morning review" context
- "Deep work" context
- "Triage" context

### 7.3 Multi-Device Context Sync

Each user-device pair has own view-stream, sync mechanism TBD:
- Conflict resolution (concurrent edits from phone + laptop)
- Offline operation
- Eventual consistency

### 7.4 Context Visualization

Dashboard showing:
- Current context (what's in LRU-N)
- Context transitions over time
- Co-access graphs (what objects typically worked on together)

---

## 8. Implementation Checklist

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
- [ ] `enter`/`leave`/`focus` verb implementation
- [ ] Active scope display in UI

### Phase 3: Fork/Merge

- [ ] Fork context creation
- [ ] ViewMerge schema and logic
- [ ] `rejoin` verb implementation
- [ ] Subordinate context destruction
- [ ] Merge recovery procedures

### Phase 4: Lifecycle Management

- [ ] View coalescence (timeout-based)
- [ ] Context break operation
- [ ] Context GC policies
- [ ] View compression (fossilization)

---

## 9. Terminology

**Context:** The set of objects currently in working memory (ContextFrame.containers)  
**View:** Immutable record of actions within a time window  
**View-Stream:** Chronological sequence of Views forming timeline  
**Primary Context:** The contextually-relevant ContextFrame for an operation  
**Primary Scope:** The currently-focused scope among active scopes  
**Active Scopes:** Set of scopes user has entered but not left  
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
- **RFC-005 v6:** API Design (Semantic Verbs & Options Schemas)
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
| 4.0 | 2026-02-06 | **Verb alignment with RFC-005 v6:** Added `focus` verb for explicit primary scope switching. Clarified enter/leave/focus separation (INV-11a, INV-11b). Updated API section with complete verb definitions. Context verbs bundled with Core. Added terminology for primary scope vs active scopes. |

---

**Status:** Draft  
**Next Steps:**
1. Review invariants with stakeholders
2. Implement ContextFrame + View schema in Core
3. Add context tracking to internal API operations
4. Implement `enter`/`leave`/`focus`/`rejoin` verbs
5. Build scope activation UI
6. Test fork/merge with real agent delegation
7. Tune context size (N) based on usage data

---

**END OF RFC**
