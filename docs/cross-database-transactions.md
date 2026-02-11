# Cross-Database Transaction Coordination (Session 12)

**Status:** ✅ Complete
**Date:** 2026-02-09
**Tests:** 13/13 passing (36 total in system package)

## Overview

Implemented cross-database transaction coordination per RFC-008 v1.2. Ensures consistency between Soil (facts) and Core (entities) databases during operations that span both layers.

## Problem Statement

MemoGarden has two SQLite databases:
- **Soil** - Immutable facts (items, system relations)
- **Core** - Mutable entities (transactions, recurrences, user relations)

Some operations must update both databases atomically:
- Creating an entity with EntityDelta items
- Editing an entity (creates EntityDelta in Soil)
- Deleting an entity (creates tombstone in both)

**Challenge:** SQLite doesn't support cross-database transactions. We need application-level coordination.

## RFC-008 v1.2 Solution

### Transaction Coordinator

```python
class TransactionCoordinator:
    """Coordinates transactions across Soil and Core databases."""

    def __init__(self, soil: Soil, core: Core):
        self.soil = soil
        self.core = core
        self.status = SystemStatus.NORMAL

    def cross_database_transaction(self) -> CrossDatabaseTransaction:
        """Return context manager for coordinated commit."""
        return CrossDatabaseTransaction(self.soil, self.core, self)
```

### Commit Ordering (INV-TX-007)

**Critical Design Decision:** Soil commits first, then Core.

**Rationale:**
1. **Soil is source of truth** - Facts are immutable, entities derive from facts
2. **Orphan detection** - If Soil commits but Core fails, we detect EntityDeltas without parent entities
3. **Rollback safety** - If Core commits but Soil fails, we can rollback Core (no orphaned deltas created)

### Isolation Level (INV-TX-004)

**SERIALIZABLE via `BEGIN EXCLUSIVE`**

```python
# Both databases locked exclusively
soil_conn.execute("BEGIN EXCLUSIVE")
core_conn.execute("BEGIN EXCLUSIVE")
```

**Why EXCLUSIVE?**
- Prevents concurrent writes during cross-DB operation
- Ensures consistency checks see stable state
- Other handles block on `busy_timeout` (5s default)

### Failure Modes

#### 1. Soil Fails, Core Not Attempted
```
Soil: BEGIN EXCLUSIVE → INSERT → ROLLBACK
Core: (not attempted)
Result: Consistent (no changes)
```

#### 2. Soil Commits, Core Fails
```
Soil: BEGIN EXCLUSIVE → INSERT → COMMIT
Core: BEGIN EXCLUSIVE → INSERT → ERROR → ROLLBACK
Result: INCONSISTENT (orphaned EntityDeltas)
Action: Mark system INCONSISTENT, require manual repair
```

#### 3. Soil Commits, Core Commits
```
Soil: BEGIN EXCLUSIVE → INSERT → COMMIT
Core: BEGIN EXCLUSIVE → INSERT → COMMIT
Result: Consistent (atomic success)
```

#### 4. Process Killed Between Commits
```
Soil: BEGIN EXCLUSIVE → INSERT → COMMIT
[PROCESS KILLED]
Core: (no commit)
Result: INCONSISTENT (detected on startup)
Action: Startup consistency check finds orphaned EntityDeltas
```

## System Status

```python
class SystemStatus(Enum):
    """System consistency status."""
    NORMAL = "normal"           # No issues detected
    INCONSISTENT = "inconsistent"  # Cross-DB failure detected
    READ_ONLY = "read_only"     # Degraded mode, writes disabled
    SAFE_MODE = "safe_mode"     # Database corruption suspected
```

### Startup Consistency Checks

```python
def check_consistency(self) -> bool:
    """Run startup consistency checks."""
    issues = []

    # INV-TX-018: Check for orphaned EntityDeltas
    orphaned_deltas = self._find_orphaned_deltas()
    if orphaned_deltas:
        issues.append(f"Found {len(orphaned_deltas)} orphaned EntityDeltas")

    # INV-TX-019: Check for broken hash chains
    broken_chains = self._find_broken_hash_chains()
    if broken_chains:
        issues.append(f"Found {len(broken_chains)} broken hash chains")

    if issues:
        self.status = SystemStatus.INCONSISTENT
        logger.error(f"Consistency check failed: {'; '.join(issues)}")
        return False

    self.status = SystemStatus.NORMAL
    return True
```

## Implementation Details

### CrossDatabaseTransaction Context Manager

```python
class CrossDatabaseTransaction:
    """Context manager for coordinated cross-database transactions."""

    def __enter__(self):
        # Begin EXCLUSIVE transactions on both databases
        self.soil_conn.execute("BEGIN EXCLUSIVE")
        self.core_conn.execute("BEGIN EXCLUSIVE")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Success: Commit both (Soil first!)
            self.soil_conn.commit()
            try:
                self.core_conn.commit()
            except Exception as e:
                # Core failed after Soil committed → INCONSISTENT
                self.coordinator.status = SystemStatus.INCONSISTENT
                logger.critical(f"Core commit failed after Soil commit: {e}")
                # Best-effort rollback of Core (Soil already committed)
                self.core_conn.rollback()
                raise
        else:
            # Failure: Rollback both
            self.soil_conn.rollback()
            self.core_conn.rollback()
            return False  # Re-raise exception
```

### Orphaned EntityDelta Detection

```python
def _find_orphaned_deltas(self) -> List[str]:
    """Find EntityDeltas without parent entities (INV-TX-018)."""
    sql = """
        SELECT i.uuid
        FROM item i
        LEFT JOIN entity e ON i.metadata ->> 'entity_uuid' = e.uuid
        WHERE i._type = 'EntityDelta'
        AND e.uuid IS NULL
    """
    return [row["uuid"] for row in self.soil_conn.execute(sql).fetchall()]
```

### Broken Hash Chain Detection

```python
def _find_broken_hash_chains(self) -> List[str]:
    """Find entities with broken hash chains (INV-TX-019)."""
    sql = """
        SELECT e.uuid, e.hash, e.previous_hash,
               (SELECT hash FROM entity e2 WHERE e2.uuid = e.previous_hash) as expected_hash
        FROM entity e
        WHERE e.previous_hash IS NOT NULL
        AND e.previous_hash != (SELECT hash FROM entity e2 WHERE e2.uuid = e.previous_hash)
    """
    return [row["uuid"] for row in self.core_conn.execute(sql).fetchall()]
```

## Key Files

- [`system/transaction_coordinator.py`](../memogarden-system/system/transaction_coordinator.py) - Main coordinator
- [`system/exceptions.py`](../memogarden-system/system/exceptions.py) - ConsistencyError, OptimisticLockError
- [`tests/test_transaction_coordinator.py`](../memogarden-system/tests/test_transaction_coordinator.py) - 13 tests

## Test Coverage

1. **test_cross_database_transaction_success** - Both databases commit
2. **test_cross_database_transaction_rollback_on_exception** - Both rollback on error
3. **test_cross_database_transaction_context_manager_protocol** - Protocol compliance
4. **test_soil_commits_first** - Commit ordering verified
5. **test_get_transaction_coordinator** - Singleton pattern
6. **Orphaned delta tests** (4 tests) - Detection and handling
7. **Broken chain tests** (3 tests) - Hash verification

## RFC-008 v1.2 Invariants Enforced

### Transaction Scope
- **INV-TX-001:** Single-DB operations use standard SQLite ACID ✅
- **INV-TX-002:** Cross-DB operations use best-effort atomicity with app-level coordination ✅
- **INV-TX-003:** Split operations (item + relation) commit independently, retry relation on failure ✅

### Isolation and Locking
- **INV-TX-004:** SERIALIZABLE via `BEGIN EXCLUSIVE` on both databases ✅
- **INV-TX-005:** One transaction per handle (no nesting, no SAVEPOINTs) ✅
- **INV-TX-006:** Other handles block on `busy_timeout` (5s default) ✅

### Commit Ordering
- **INV-TX-007:** Commit ordering: Soil first, then Core ✅
- **INV-TX-008:** If Soil commits but Core fails → system marked INCONSISTENT ✅
- **INV-TX-009:** Process killed between commits → INCONSISTENT (detected on startup) ✅

### Rollback
- **INV-TX-010:** Best-effort rollback (if one DB committed, rollback is no-op on that DB) ✅

### Optimistic Locking
- **INV-TX-011:** `entity.hash = SHA256(JSON(state) + entity.previous_hash)` ✅
- **INV-TX-012:** Update requires `based_on_hash` to match current hash ✅
- **INV-TX-013:** Hash mismatch → OptimisticLockError ✅

### System Status
- **INV-TX-014:** Modes: NORMAL, INCONSISTENT, READ_ONLY, SAFE_MODE ✅
- **INV-TX-015:** No issues → NORMAL ✅
- **INV-TX-016:** Orphaned deltas → INCONSISTENT ✅
- **INV-TX-017:** Database corruption → SAFE_MODE ✅

### Startup Consistency Check
- **INV-TX-018:** Check for orphaned EntityDeltas ✅
- **INV-TX-019:** Check for broken hash chains ✅
- **INV-TX-020:** System starts regardless of state (always-available startup) ✅

## Future Work (Documented TODOs)

### Recovery Tools
- `memogarden diagnose` - Report inconsistencies with detailed analysis
- `memogarden repair` - Automated repairs for common issues
- Interactive repair mode - Operator-in-the-loop resolution for complex cases

### Advanced Consistency Checks
- Referential integrity verification (entity → entitydelta links)
- System relation consistency (source/target exist)
- Duplicate detection (same fact created multiple times)

### Performance Optimizations
- Reduce EXCLUSIVE lock duration (minimal time between BEGIN and first write)
- Read-only operations during INCONSISTENT state (with warnings)
- Async consistency checks (background sweep)

## Usage Example

```python
from system.core import get_core
from system.soil import get_soil
from system.transaction_coordinator import get_transaction_coordinator

# Get coordinator
coordinator = get_transaction_coordinator()

# Cross-database operation
with get_soil() as soil, get_core() as core:
    with coordinator.cross_database_transaction():
        # Both databases locked in EXCLUSIVE mode

        # Create EntityDelta in Soil
        delta = EntityDelta(...)
        soil.create_item(delta)

        # Update entity in Core
        core.entity.edit(
            entity_uuid=target,
            data=new_data,
            based_on_hash=current_hash
        )

        # Commits on exit (Soil first, then Core)
```

## Dependencies

- Session 6: Audit Facts (ActionResult tracking)
- Session 11: Schema Access Utilities (database schema access)
- RFC-008 v1.2: Transaction Semantics

## References

- RFC-008 v1.2: Transaction Semantics
- Implementation Plan: Session 12
- [`test_transaction_coordinator.py`](../memogarden-system/tests/test_transaction_coordinator.py) - Test examples
