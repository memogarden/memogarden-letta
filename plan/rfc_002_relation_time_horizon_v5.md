# RFC-002: Relation Time Horizon & Fossilization

**Version:** 5.0  
**Status:** Draft  
**Author:** MemoGarden Project  
**Created:** 2025-01-14  
**Last Updated:** 2025-01-20

## Abstract

This RFC specifies the time horizon mechanism for managing relation lifecycle in MemoGarden. Time horizon is a lightweight heuristic for determining which relations (and by derivation, which items) should be preserved versus fossilized. The mechanism applies only to user relations; system relations are immutable facts that persist until their source is deleted.

## Background

### Cognitive Science Foundation

Anderson & Schooler (1991, 1997) demonstrated that human memory is optimized to match statistical patterns of information recurrence:

- **Recency effect (power function):** Probability of needing information decreases as a power function of time since last access
- **Frequency effect (linear):** More encounters predict proportionally higher probability of future need
- **Spacing interaction:** Long gaps between accesses predict durable, long-term importance

The practical implication: items accessed with *expanding* gaps (1 day â†’ 1 week â†’ 1 month) exhibit the strongest signal for long-term preservation.

### Access Pattern Signatures

| Pattern | Gap Trend | Interpretation |
|---------|-----------|----------------|
| Burst then silence | Short gaps, then nothing | Project ended or abandoned |
| Regular intervals | Stable gaps | Ongoing reference material |
| Expanding gaps | Gaps growing | Foundational/durable knowledge |
| Contracting gaps | Gaps shrinking | Intensifying focus |
| Single access | N/A | Low confidence either way |

### Design Constraints

MemoGarden targets resource-constrained hardware (Raspberry Pi-class). The mechanism must be:

- **Minimal storage:** 2 integers per relation (time_horizon, last_access_at)
- **Integer arithmetic only:** No floating-point decay calculations
- **Batch-friendly:** Expensive operations only during periodic sweeps, not per-access
- **Graceful degradation:** System remains functional under storage pressure

---

## Design Decisions

### D1: Significance Lives on Relations, Not Items

Items do not have intrinsic significance. Their value derives from their relationships to other items/entities. An item's "significance" is computed from its inbound relations, not stored directly.

**Rationale:** Aligns with MemoGarden's artifact-first, relation-centric architecture. Avoids redundant state.

### D2: Time Horizon as the Currency

Rather than abstract "significance points," we use time horizon: a future timestamp indicating predicted relevance.

```
time_horizon: int  # days since epoch
```

**Rationale:** Interpretable (time), bounded (no overflow risk), matches cognitive science research.

### D3: System vs User Relations

| Property | System Relations | User Relations |
|----------|------------------|----------------|
| Examples | triggers, cites, derives_from, contains, replies_to | explicit_link |
| Created by | MemoGarden automatically | Explicit operator action |
| Mutability | Immutable fact | Mutable (time_horizon changes) |
| Decay | None | Time-based |
| Dies when | Source item deleted | time_horizon < today |

**Rationale:** System relations encode structural facts. Culling them would be changing history. User relations encode engagement/attention, which naturally fades.

**Note:** The `context_link` kind has been eliminated. Co-access patterns are captured via `ArtifactDelta.context` field and analyzed retrospectively from delta history, not through automatic relation creation.

### D4: Fossilization is Compression, Not Deletion

When an item fossilizes:
- Item still exists in Soil (compressed form based on fidelity state)
- System relations persist unchanged
- User relations have time_horizon in the past (that's why it fossilized)

**Rationale:** Supports resurrection, maintains referential integrity, preserves audit trail.

### D5: Views Are Events, Not Relations

A view is a point-in-time fact ("operator viewed X at time T"), recorded in an ephemeral ringbuffer. The *meaning* of views comes from context: what else was being attended to at that moment, captured in `ArtifactDelta.context` when mutations occur.

**Rationale:** Relations represent ongoing connections, not ephemeral events. Context is captured at mutation time, not through intermediate view-to-relation pipelines.

### D6: No Grace Period

All items are stored immediately. Fossilization mechanism determines retention based on access patterns. Bulk imports start cold, prove worth through access, or fossilize.

**Rationale:** Simpler. Eliminates cliff-effect from synchronized expiration. Items with no user relations fossilize when swept.

---

## UUID Conventions

MemoGarden uses **two separate UUID namespaces** by storage origin:

| System | UUID Prefix | Database | Mutability | Examples |
|--------|-------------|----------|------------|----------|
| **Soil** | `soil_` | Soil DB | Immutable | `soil_abc123...` |
| **Core** | `core_` | Core DB | Mutable | `core_xyz789...` |

**UUID Format:**
```
soil_<uuid4>    # e.g., soil_a1b2c3d4-e5f6-7890-abcd-ef1234567890
core_<uuid4>    # e.g., core_fedcba98-7654-3210-fedc-ba9876543210
```

System relations live in Soil â†’ use `soil_` prefix.
Active user relations live in Core â†’ use `core_` prefix.
Fossilized user relations move to Soil â†’ receive `soil_` prefix on fossilization.

---

## Relation Classification

### System Relations (Immutable Facts)

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

**Properties:**
- No time_horizon field (existence is binary)
- Created when structural fact is established
- Deleted only when source item is deleted
- Not subject to decay or fossilization

**Schema:**
```python
@dataclass
class SystemRelation:
    uuid: str               # Stable identifier (soil_ prefix)
    kind: str               # One of SYSTEM_RELATION_KINDS
    source: str             # UUID of source
    source_type: str        # 'item' | 'entity' | 'artifact'
    target: str             # UUID of target
    target_type: str        # 'item' | 'entity' | 'artifact'
    created_at: int         # Days since epoch
    evidence: Evidence | None
    metadata: dict | None
```

### User Relations (Engagement Signals)

```python
USER_RELATION_KINDS = {
    'explicit_link',  # Operator-created connection
}
```

**Note:** `context_link` kind has been **eliminated**. Co-access is captured via `ArtifactDelta.context` field and analyzed retrospectively from delta history.

**Properties:**
- Has time_horizon and last_access_at fields
- Created by explicit operator action
- Subject to time-based decay
- Fossilizes when time_horizon < today

**Schema:**
```python
@dataclass
class UserRelation:
    uuid: str               # Stable identifier (core_ when active, soil_ when fossilized)
    kind: str               # One of USER_RELATION_KINDS
    source: str             # UUID of source
    source_type: str        # 'item' | 'entity' | 'artifact'
    target: str             # UUID of target
    target_type: str        # 'item' | 'entity' | 'artifact' | 'fragment'
    time_horizon: int       # Future timestamp (days since epoch)
    last_access_at: int     # Timestamp of most recent access (days since epoch)
    created_at: int         # Days since epoch
    evidence: Evidence | None
    metadata: dict | None
```

---

## Time Horizon Mechanism

### Core Algorithm

Each user relation stores two integers:

```python
time_horizon: int   # future timestamp (days since epoch)
last_access_at: int # timestamp of most recent access (days since epoch)
```

On access:

```python
SAFETY_COEFFICIENT = 1.2  # Margin for irregular access patterns

def on_relation_access(relation: UserRelation):
    today = current_day()
    delta = today - relation.last_access_at
    relation.time_horizon += int(delta * SAFETY_COEFFICIENT)
    relation.last_access_at = today
```

### Why Addition Works

Same number of accesses, different spacing, different outcomes:

| Pattern | Accesses | Deltas | Horizon Gained |
|---------|----------|--------|----------------|
| Daily for a week | 7 | 1+1+1+1+1+1+1 | ~8 days |
| Weekly for 7 weeks | 7 | 7+7+7+7+7+7+7 | ~59 days |
| Monthly for 7 months | 7 | 30+30+30+30+30+30+30 | ~252 days |

Long gaps signal durable importance â†’ more runway. Burst activity (many accesses, tiny gaps) accumulates minimal runway.

### Keep/Fossilize Decision

```python
def relation_is_alive(relation: UserRelation) -> bool:
    return relation.time_horizon >= current_day()

def relation_should_fossilize(relation: UserRelation) -> bool:
    return relation.time_horizon < current_day()
```

No explicit decay computation required. Time simply passes the horizon by.

### Safety Coefficient

SAFETY_COEFFICIENT (1.1â€“1.5) provides margin for irregular access patterns:

| Scenario | Gap | Coefficient | Runway |
|----------|-----|-------------|--------|
| Annual tax document | 365 days | 1.0 | 365 days (tight) |
| Annual tax document | 365 days | 1.2 | 438 days (safe margin) |

Recommendation: Start with 1.2, tune based on observation.

---

## Item Fidelity States

Items track their compression state via a `fidelity` field:

| State | Content | References | Notes |
|-------|---------|------------|-------|
| `full` | Complete original | Intact | Default for new items |
| `summary` | Compressed representation | Intact | LLM or extractive summary |
| `stub` | Minimal metadata only | Intact | UUID, timestamps, type preserved |
| `tombstone` | Deleted marker | May be broken | For deletion under storage pressure |

**Schema addition to Item:**
```python
@dataclass
class Item:
    # ... existing fields ...
    fidelity: str              # 'full' | 'summary' | 'stub' | 'tombstone'
    fossilized_at: int | None  # Days since epoch, when fossilized
```

---

## Item Lifecycle

### Item Significance (Derived)

```python
def item_time_horizon(item_uuid: str) -> int | None:
    """
    Derived from inbound user relations.
    Returns None if no user relations (orphan).
    """
    user_rels = get_inbound_user_relations(item_uuid)
    if not user_rels:
        return None
    return max(r.time_horizon for r in user_rels)
```

Using `max` (not sum): item survives if *any* relation is alive. Conservative approach appropriate for fossilization gating.

### Fossilization Trigger

```python
def should_fossilize_item(item: Item) -> bool:
    # Already fossilized? Skip
    if item.fidelity != 'full':
        return False
    
    # Check user relations
    horizon = item_time_horizon(item.uuid)
    
    if horizon is None:
        # Orphan (no user relations): fossilize
        return True
    
    return horizon < current_day()
```

**Note:** Grace period has been **eliminated**. Items with no user relations fossilize immediately when swept.

### Fossilization Process

```python
def fossilize_item(item: Item, target_fidelity: str = 'summary'):
    """Compress item, preserve structure."""
    
    if target_fidelity == 'summary':
        summary = generate_summary(item)  # Extractive or LLM-based
        item.fidelity = 'summary'
        item.summary = summary
        # Original content may be cleared for space
    elif target_fidelity == 'stub':
        item.fidelity = 'stub'
        # Clear content, keep metadata
    
    item.fossilized_at = current_day()
    
    # System relations: unchanged (facts persist)
    # User relations: already have horizon < today (that's why we're here)
    
    # Log event
    create_item(SystemEvent(
        event_type='item_fossilized',
        payload={'item_uuid': item.uuid, 'fidelity': target_fidelity}
    ))
```

### What Survives Fossilization

| Component | Before | After | Notes |
|-----------|--------|-------|-------|
| Item content | Full | Summary/stub | Compression based on fidelity |
| Item metadata | Full | Full | UUID, timestamps, type preserved |
| System relations | Exist | Exist | Facts unchanged |
| User relations | time_horizon in past | Moved to Soil | Could be pruned for space |
| Inbound system relations | Exist | Exist | Other items still cite this |

### Resurrection

```python
def on_fossilized_item_access(item: Item):
    """Re-enter engagement cycle."""
    
    create_item(SystemEvent(
        event_type='fossilized_item_accessed',
        payload={'item_uuid': item.uuid}
    ))
    
    # Item remains in compressed state unless explicitly expanded
    # New user relations will accumulate, potentially preventing re-fossilization
```

---

## Deletion Under Storage Pressure

When storage exceeds threshold, fossilized items are deleted.

### Policy

**Priority order for deletion:**
1. Least-accessed (aligns with time-horizon philosophy)
2. Oldest as tiebreaker
3. Size as multiplier (large items evicted sooner at same access level)

**Formula (empirical tuning required):**
```python
import math

def eviction_score(item: Item) -> float:
    days_since_access = current_day() - item.last_access_day
    significance = item_significance(item.uuid) or 1  # Avoid division by zero
    size_weight = math.log(item.size_bytes + 1)
    
    return days_since_access * size_weight / significance
```

Higher score = evict sooner.

### Deletion Process

```python
def delete_under_pressure(target_free_bytes: int):
    """Delete fossilized items until target space freed."""
    
    candidates = query_fossilized_items_by_eviction_score()
    freed = 0
    
    for item in candidates:
        if freed >= target_free_bytes:
            break
            
        # Downgrade fidelity before full deletion
        if item.fidelity == 'summary':
            freed += downgrade_to_stub(item)
        elif item.fidelity == 'stub':
            freed += delete_item(item)  # Creates tombstone
```

### Degraded Item Transparency

References to degraded items must surface fidelity warnings:

```python
def resolve_reference(uuid: str) -> ReferenceResult:
    item = get_item(uuid)
    
    return ReferenceResult(
        uuid=uuid,
        fidelity=item.fidelity,
        content=item.content if item.fidelity == 'full' else item.summary,
        warning=f"Item degraded to {item.fidelity}" if item.fidelity != 'full' else None
    )
```

---

## Batch Processing

### Fossilization Sweep

Periodic process (e.g., daily) to identify and process fossilization candidates:

```python
def fossilization_sweep():
    """Daily sweep for fossilization candidates."""
    
    candidates = query_fossilization_candidates()
    metrics = SweepMetrics(
        timestamp=now(),
        items_scanned=len(candidates),
        items_fossilized=0,
        relations_scanned=0,
        relations_expired=0
    )
    
    for item in candidates:
        if should_fossilize_item(item):
            fossilize_item(item)
            metrics.items_fossilized += 1
    
    log_sweep_metrics(metrics)

def query_fossilization_candidates() -> list[Item]:
    """Find items that might need fossilization."""
    return query("""
        SELECT i.* FROM item i
        WHERE i.fidelity = 'full'
        AND NOT EXISTS (
            SELECT 1 FROM user_relation r
            WHERE r.target = i.uuid
            AND r.time_horizon >= ?
        )
    """, [current_day()])
```

### Metrics Collection

```python
@dataclass
class SweepMetrics:
    timestamp: datetime
    items_scanned: int
    items_fossilized: int
    relations_scanned: int
    relations_expired: int
    
def log_sweep_metrics(metrics: SweepMetrics):
    """Record metrics for threshold tuning."""
    create_item(SystemEvent(
        event_type='fossilization_sweep',
        payload=asdict(metrics)
    ))
```

---

## Schema

### Soil Tables

```sql
-- Items table (with fidelity tracking)
CREATE TABLE item (
    uuid TEXT PRIMARY KEY,              -- soil_ prefix
    _type TEXT NOT NULL,
    realized_at TEXT NOT NULL,          -- ISO 8601
    canonical_at TEXT NOT NULL,         -- ISO 8601
    integrity_hash TEXT,                -- SHA256 of content fields
    fidelity TEXT NOT NULL DEFAULT 'full',  -- 'full' | 'summary' | 'stub' | 'tombstone'
    fossilized_at INTEGER,              -- Days since epoch
    data JSON NOT NULL                  -- Type-specific fields
);

CREATE INDEX idx_item_type ON item(_type);
CREATE INDEX idx_item_realized ON item(realized_at);
CREATE INDEX idx_item_canonical ON item(canonical_at);
CREATE INDEX idx_item_fidelity ON item(fidelity);

-- System relations (immutable facts)
CREATE TABLE system_relation (
    uuid TEXT PRIMARY KEY,              -- soil_ prefix
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target TEXT NOT NULL,
    target_type TEXT NOT NULL,
    created_at INTEGER NOT NULL,        -- Days since epoch
    evidence JSON,
    metadata JSON,
    
    UNIQUE(kind, source, target)
);

CREATE INDEX idx_sysrel_source ON system_relation(source);
CREATE INDEX idx_sysrel_target ON system_relation(target);
CREATE INDEX idx_sysrel_kind ON system_relation(kind);
```

### Core Tables

```sql
-- User relations (engagement signals, active only)
CREATE TABLE user_relation (
    uuid TEXT PRIMARY KEY,              -- core_ prefix (becomes soil_ on fossilization)
    kind TEXT NOT NULL,                 -- Currently only 'explicit_link'
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target TEXT NOT NULL,
    target_type TEXT NOT NULL,
    time_horizon INTEGER NOT NULL,      -- Days since epoch
    last_access_at INTEGER NOT NULL,    -- Days since epoch
    created_at INTEGER NOT NULL,
    evidence JSON,
    metadata JSON,
    
    UNIQUE(kind, source, target)
);

CREATE INDEX idx_userrel_source ON user_relation(source);
CREATE INDEX idx_userrel_target ON user_relation(target);
CREATE INDEX idx_userrel_horizon ON user_relation(time_horizon);
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
class FossilizationConfig:
    # Time horizon
    safety_coefficient: float = 1.2
    
    # Sweep schedule
    sweep_interval_hours: int = 24
    
    # Summary generation
    summary_method: str = 'extractive'  # 'extractive' | 'llm'
    summary_max_tokens: int = 200
    
    # Storage pressure
    storage_pressure_threshold_pct: float = 85.0
    eviction_target_free_pct: float = 20.0
```

All parameters should be configurable, not hardcoded. Metrics will inform tuning.

---

## Identified Gaps

This RFC intentionally does not address the following areas, which require separate design work:

### Gap 1: Explicit Linking UX

**What's missing:** How operator creates explicit user relations.

**Current state:** No UI or tool defined for explicit linking.

**Expected behavior:** Operator can manually link items, creating user relations with initial time horizon.

### Gap 2: Relation Inheritance on Item Edit

**What's missing:** When item B is edited to reference item A, does a system relation (cites) get created automatically?

**Current state:** Unclear whether reference parsing creates relations.

**Expected behavior:** Inline references (e.g., `^a7f`, `goals_doc:15`) should create system relations automatically.

### Gap 3: Cascading Effects

**What's missing:** When item A is deleted, what happens to:
- System relations where A is source? (Should die)
- System relations where A is target? (Should die? Or mark as dangling?)
- User relations involving A? (Should die)

**Current state:** Not specified.

### Gap 4: Bulk Import Handling

**What's missing:** 500 emails arrive at once. How are their initial user relations (if any) and time horizons set?

**Current state:** Each starts cold with no user relations; fossilizes if not accessed.

### Gap 5: Resurrection Depth

**What's missing:** When fossilized item is accessed, should it be fully restored or remain compressed?

**Options:**
- Full restore (expensive, may not be wanted)
- Compressed + active flag (cheap, might be sufficient)
- Lazy restore on second access (middle ground)

### Gap 6: Multi-Hop Significance Propagation

**What's missing:** Should high-significance items boost connected items?

**Current state:** Not implemented. Each relation decays independently.

**Consideration:** May add complexity without proportionate benefit. Deferred.

### Gap 7: Eviction Score Formula

**What's missing:** Empirical validation of deletion priority weights.

**Current state:** Formula proposed but needs tuning.

---

## Eliminated Concepts

The following concepts from earlier designs have been removed:

| Concept | Previous Version | Reason for Elimination |
|---------|------------------|------------------------|
| Grace period | v4.0 | Fossilization handles retention; eliminates cliff-effect |
| `context_link` kind | v4.0 | Co-access captured via `ArtifactDelta.context`; analyzed retrospectively |
| ViewLinkIndex promotion | RFC-003 | Context captured on mutation, not through eviction pipeline |

---

## Open Questions

1. **Initial time horizon for new user relations:** What value? `current_day() + 7`?

2. **Relation pruning:** Should user relations with horizon far in the past be deleted entirely, or kept indefinitely in Soil?

3. **Orphan handling:** Items with no relations at all. Fossilize immediately, or wait for some access window?

4. **Summary quality:** Extractive (fast, predictable) vs LLM-generated (better, costly)? Hybrid based on item type?

5. **Per-type decay rates:** Should emails decay faster than documents? Or uniform treatment?

---

## Future Work

### Playback Scrubber

Visual tool for parameter exploration:
- Time slider showing system state at any point
- Trace specific item through lifecycle
- Side-by-side parameter comparison

### Adaptive Thresholds

Parameters adjust based on:
- Storage pressure
- Per-item-type patterns
- Operator feedback on fossilization decisions

---

## References

- Anderson, J. R., & Schooler, L. J. (1991). Reflections of the environment in memory. *Psychological Science*, 2(6), 396-408.
- Anderson, J. R., & Schooler, L. J. (1997). The adaptive nature of memory. In *Handbook of Human Memory*.
- memogarden_prd_v0_6_0.md: Core ontology, storage architecture
- RFC-001 v4: Security architecture, operational design
- RFC-003 v1: Context mechanism (ViewLinkIndex eliminated)
- memogarden-time-horizon-whitepaper.md: Cognitive science foundation
- memogarden_design_review_2025_01_20.md: Consolidated design decisions

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-14 | Initial draft with significance points model |
| 2.0 | 2025-01-14 | Removed cache/staging, tightened scope |
| 3.0 | 2025-01-16 | Replaced significance with time horizon; separated system/user relations; identified gaps |
| 4.0 | 2025-01-16 | Full rewrite: consolidated design decisions; complete schemas; detailed fossilization lifecycle |
| 5.0 | 2025-01-20 | **Design review integration:** UUID prefixes (soil_/core_); Grace period eliminated; `context_link` kind eliminated (co-access via ArtifactDelta.context); Fidelity states added; Deletion under storage pressure policy; Updated gaps and eliminated concepts |

---

**Status:** Draft  
**Next Steps:**
1. Implement system relation auto-creation from references (Gap 2)
2. Prototype fossilization sweep with metrics collection
3. Build playback scrubber for parameter tuning
4. Implement user relation access tracking
5. Validate eviction score formula empirically (Gap 7)

---

**END OF RFC**
