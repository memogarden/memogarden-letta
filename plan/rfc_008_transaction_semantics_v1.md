# RFC-008: Transaction Semantics & Consistency Model

**Version:** 1.0  
**Status:** Draft  
**Author:** JS  
**Date:** 2026-02-02

## Abstract

This RFC specifies MemoGarden's transaction semantics for operations spanning the two-database architecture (Soil for immutable facts, Core for mutable state). The design prioritizes survivability and operator-assisted recovery over absolute consistency guarantees, accepting rare failure modes that require manual intervention.

## Motivation

MemoGarden's two-database model creates coordination challenges:

- Items in Soil are immutable, append-only facts
- Entities in Core are mutable with delta-tracked changes
- EntityDeltas (tracking Entity changes) must be stored in Soil atomically with Core updates
- No distributed transaction protocol (2PC) exists for SQLite

The system must balance:
- **Consistency:** Cross-database operations should be atomic
- **Availability:** System must survive any failure and always start
- **Survivability:** Decade-long operation on resource-limited hardware
- **Simplicity:** No complex transaction coordinator or write-ahead logs

This RFC defines pragmatic transaction semantics that accept rare inconsistencies (~0.01%/year) in exchange for simplicity and robustness.

## Design Principles

1. **Always-available startup:** System starts regardless of database state
2. **Detect, don't prevent:** Report inconsistencies rather than guaranteeing prevention
3. **Operator-in-the-loop:** Manual resolution for rare failures
4. **Best-effort atomicity:** Cross-DB operations are atomic except during catastrophic failures
5. **Conservative SQLite usage:** Prefer safety over performance optimizations

## Core Architecture

### Two-Database Model

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  MemoGarden Handle  â”‚
â”‚                     â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚ Transaction   â”‚  â”‚
â”‚  â”‚ Coordinator   â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚          â”‚          â”‚
â”‚    â”Œâ”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”    â”‚
â”‚    â”‚           â”‚    â”‚
â”œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”¤
â”‚ Soil DB â”‚  â”‚Core DB â”‚
â”‚         â”‚  â”‚        â”‚
â”‚ Items   â”‚  â”‚Entitiesâ”‚
â”‚ SysRels â”‚  â”‚UsrRels â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**Soil (immutable timeline):**
- Items: Notes, Messages, Emails, ToolCalls, EntityDeltas
- System Relations: Immutable structural facts
- Fossilized User Relations: Archived engagement signals

**Core (mutable state):**
- Entities: Artifacts, Labels, Transactions
- Active User Relations: Current engagement signals
- ContextFrames: Attention tracking

### Transaction Scope Categories

MemoGarden operations fall into three transaction scope categories:

**1. Single-Database Operations (Simple)**

Operations that affect only one database:

| Operation | Database | Example |
|-----------|----------|---------|
| `add_item()` | Soil only | Create Note, Message, Email |
| `add_system_relation()` | Soil only | Create structural fact |
| `add_entity()` | Core only | Create Artifact |
| `add_user_relation()` | Core only | Create engagement signal |

**Transaction semantics:** Standard SQLite ACID within single database.

**2. Cross-Database Operations (Coordinated)**

Operations that must modify both databases atomically:

| Operation | Databases | Soil Effect | Core Effect |
|-----------|-----------|-------------|-------------|
| `update_entity()` | Both | Write EntityDelta | Update Entity state + hash |
| `fossilize_relation()` | Both | Write fossilized relation | Delete active relation |

**Transaction semantics:** Best-effort atomicity with application-level coordination.

**3. Split Operations (Retry Pattern)**

Operations where databases have dependency ordering:

| Operation | Pattern | Rationale |
|-----------|---------|-----------|
| `add_item() + add_user_relation()` | Item first, retry relation | Items are primary facts; relations are secondary |

**Transaction semantics:** Item creation commits independently; relation creation retries on failure.

## Transaction Implementation

### SQLite Configuration

```python
# Applied to both Soil and Core databases
PRAGMA journal_mode=WAL;           # Write-ahead logging
PRAGMA synchronous=FULL;           # Wait for fsync (crash-safe)
PRAGMA busy_timeout=5000;          # 5s timeout for lock conflicts
PRAGMA foreign_keys=ON;            # Enforce constraints
```

**Rationale:**
- WAL mode: Better concurrency, faster commits
- FULL synchronous: Survive power loss
- 5s timeout: Balance responsiveness vs. allowing long operations
- Foreign keys: Detect constraint violations early

### Isolation Level

**SERIALIZABLE** via explicit `BEGIN EXCLUSIVE` on both databases.

```python
class MemoGarden:
    def begin_transaction(self):
        """Enter transaction mode. Raises if already in transaction."""
        if self._in_transaction:
            raise AlreadyInTransactionError()
        
        # Lock both databases exclusively
        self._soil_conn.execute("BEGIN EXCLUSIVE")
        try:
            self._core_conn.execute("BEGIN EXCLUSIVE")
        except Exception as e:
            # If Core lock fails, rollback Soil
            self._soil_conn.rollback()
            raise
        
        self._in_transaction = True
```

**Properties:**
- One transaction per handle
- No nesting (no SAVEPOINTs)
- Other handles block on `busy_timeout`
- Prevents concurrent cross-DB operations

### Commit Protocol

```python
def commit_transaction(self):
    """Commit both databases. Best-effort atomicity."""
    if not self._in_transaction:
        raise NotInTransactionError("commit")
    
    soil_ok = False
    core_ok = False
    
    try:
        # Commit Soil first (source of truth)
        self._soil_conn.commit()
        soil_ok = True
        
        # Then commit Core
        self._core_conn.commit()
        core_ok = True
        
    except Exception as e:
        # Log failure details
        self._log_commit_failure(soil_ok, core_ok, e)
        
        # Attempt rollback of both (even if one committed)
        self._rollback_both()
        
        # Mark system state
        if soil_ok and not core_ok:
            self.status = SystemStatus.INCONSISTENT
        
        raise TransactionCommitError(
            soil_ok=soil_ok, 
            core_ok=core_ok,
            reason=str(e)
        )
    finally:
        self._in_transaction = False
```

**Commit ordering rationale:**
- Soil first: It's the source of truth, can rebuild Core from it
- Core second: If Core fails, Soil has extra data (orphaned deltas)

**Failure scenarios:**

| Scenario | Soil | Core | System State | Recovery |
|----------|------|------|--------------|----------|
| Both succeed | âœ“ | âœ“ | NORMAL | None needed |
| Both fail | âœ— | âœ— | NORMAL | Transaction rolled back |
| Soil commits, Core fails | âœ“ | âœ— | INCONSISTENT | `memogarden repair` |
| Process killed between commits | âœ“ | âœ— | INCONSISTENT | Detected on next startup |

**Frequency estimate:** Soil-commits-Core-fails occurs ~0.01% per year (36 seconds of vulnerability per year for personal system with 100 transactions/day).

### Rollback Protocol

```python
def rollback_transaction(self):
    """Rollback both databases."""
    if not self._in_transaction:
        raise NotInTransactionError("rollback")
    
    try:
        self._soil_conn.rollback()
    except Exception as e:
        logger.error(f"Soil rollback failed: {e}")
    
    try:
        self._core_conn.rollback()
    except Exception as e:
        logger.error(f"Core rollback failed: {e}")
    
    self._in_transaction = False
```

**Best-effort rollback:** If commit succeeded on one DB, rollback is no-op on that DB. System marked INCONSISTENT.

### Context Manager

```python
@contextmanager
def transaction(self):
    """
    Context manager for transactions.
    Auto-commits on success, auto-rolls-back on exception.
    
    Locks both Soil and Core databases with EXCLUSIVE locks.
    
    Note: Cross-database atomicity is best-effort. Rare failures
    (~0.01%/year) require operator intervention via `memogarden repair`.
    """
    self.begin_transaction()
    try:
        yield self
        self.commit_transaction()
    except Exception:
        self.rollback_transaction()
        raise
```

**Usage:**
```python
with mg.transaction():
    entity = mg.get_entity('core_abc')
    mg.update_entity('core_abc', {'content': '...'}, based_on_hash=entity.hash)
    # Auto-commits both DBs on exit
```

## Operation-Specific Semantics

### Single-Database Operations

**add_item():**
```python
def add_item(self, type: str, content: dict, /, *, metadata: dict = None) -> Item:
    """Create immutable Item in Soil."""
    # If in transaction, uses existing Soil connection
    # Otherwise, auto-commits
    
    uuid = f"soil_{uuid4()}"
    integrity_hash = sha256(json.dumps(content, sort_keys=True))
    
    self._soil_conn.execute("""
        INSERT INTO item (uuid, _type, realized_at, canonical_at, 
                         integrity_hash, fidelity, data, metadata)
        VALUES (?, ?, ?, ?, ?, 'full', ?, ?)
    """, (uuid, type, now(), now(), integrity_hash, 
          json.dumps(content), json.dumps(metadata)))
    
    if not self._in_transaction:
        self._soil_conn.commit()
    
    return Item(uuid=uuid, type=type, content=content, ...)
```

**Transaction behavior:**
- Within transaction: Defers commit
- Outside transaction: Auto-commits immediately

### Cross-Database Operations

**update_entity():**
```python
def update_entity(self, uuid: str, content: dict, /, 
                  *, based_on_hash: str) -> Entity:
    """
    Update Entity in Core, create EntityDelta in Soil.
    Requires explicit transaction.
    """
    if not self._in_transaction:
        raise NotInTransactionError(
            "update_entity requires explicit transaction"
        )
    
    # 1. Verify optimistic lock (hash matches)
    entity = self._get_entity_for_update(uuid)
    if entity.hash != based_on_hash:
        raise OptimisticLockError(
            expected=based_on_hash,
            actual=entity.hash,
            entity_uuid=uuid
        )
    
    # 2. Compute new hash
    new_hash = sha256(json.dumps(content, sort_keys=True) + entity.hash)
    
    # 3. Stage EntityDelta for Soil (written at commit)
    delta = {
        'entity_uuid': uuid,
        'previous_hash': entity.hash,
        'new_hash': new_hash,
        'changes': content,
        'applied_at': now()
    }
    self._pending_deltas.append(delta)
    
    # 4. Update Entity in Core
    self._core_conn.execute("""
        UPDATE entity 
        SET hash=?, previous_hash=?, version=version+1, 
            updated_at=?, state=?
        WHERE uuid=?
    """, (new_hash, entity.hash, now(), json.dumps(content), uuid))
    
    # 5. On commit, pending deltas written to Soil
    return Entity(uuid=uuid, hash=new_hash, content=content, ...)
```

**Atomicity guarantee:**
- Both DBs locked (EXCLUSIVE)
- EntityDelta written to Soil atomically with Entity update in Core
- On failure, both roll back (best-effort)

**Hash chain safety:**
- New hash computed but not stored until commit
- Impossible to extend chain with uncommitted hash
- Optimistic lock checked at commit time (re-validate hash)

**fossilize_relation():**
```python
def fossilize_relation(self, relation_uuid: str) -> None:
    """
    Move user relation from Core to Soil.
    Requires explicit transaction.
    """
    if not self._in_transaction:
        raise NotInTransactionError(
            "fossilize_relation requires explicit transaction"
        )
    
    # 1. Read relation from Core
    relation = self._core_conn.execute("""
        SELECT * FROM user_relation WHERE uuid=?
    """, (relation_uuid,)).fetchone()
    
    # 2. Insert into Soil (change UUID prefix)
    soil_uuid = f"soil_{relation_uuid[5:]}"  # core_ â†’ soil_
    self._soil_conn.execute("""
        INSERT INTO system_relation 
        (uuid, kind, source, target, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (soil_uuid, relation['kind'], relation['source'], 
          relation['target'], relation['created_at'], 
          relation['metadata']))
    
    # 3. Delete from Core
    self._core_conn.execute("""
        DELETE FROM user_relation WHERE uuid=?
    """, (relation_uuid,))
    
    # On commit, both operations persisted atomically
```

### Split Operations

**add_item() + add_user_relation():**

Pattern for creating fact + engagement:

```python
# NOT in explicit transaction
try:
    # Step 1: Create Item (commits to Soil)
    item = mg.add_item('Note', {'text': '...'})
    
    # Step 2: Add relation (commits to Core)
    try:
        mg.add_user_relation(
            kind='explicit_link',
            source=context_uuid,
            target=item.uuid,
            horizon='+30d'
        )
    except Exception as e:
        # Item exists in Soil, relation failed
        # Retry or log for later
        logger.warning(f"Failed to add relation to {item.uuid}: {e}")
        # Operator can add relation later via repair

except Exception as e:
    # Item creation failed, nothing committed
    raise
```

**Rationale:**
- Items are primary facts (source of truth)
- Relations are secondary (can be reconstructed)
- Item without relation is valid state (orphan)
- Relation without item would be invalid (dangling reference)

## Optimistic Locking

### Entity Hash Chains

Each Entity maintains a cryptographic hash chain:

```python
entity.hash = SHA256(JSON(entity.state) + entity.previous_hash)
```

**Properties:**
- Tamper detection: Recompute chain, verify hashes
- Optimistic locking: Update requires knowing current hash
- Full lineage: Trace back through previous_hash links

### Conflict Detection

```python
# Client 1
entity = mg.get_entity('core_abc')  # hash = H1
# ... time passes ...
mg.update_entity('core_abc', {...}, based_on_hash=H1)

# Client 2 (concurrent)
entity = mg.get_entity('core_abc')  # hash = H1
mg.update_entity('core_abc', {...}, based_on_hash=H1)

# One succeeds (hash â†’ H2)
# Other fails: OptimisticLockError (expected H1, got H2)
```

### Conflict Resolution

```python
try:
    with mg.transaction():
        mg.update_entity('core_abc', content, based_on_hash=old_hash)
except OptimisticLockError as e:
    # Read current state
    current = mg.get_entity('core_abc')
    
    # Application decides:
    # - Retry with new hash (3-way merge)
    # - Abort and notify user
    # - Apply Last-Write-Wins policy
    
    # Example: Retry with new hash
    merged = three_way_merge(old_content, content, current.state)
    mg.update_entity('core_abc', merged, based_on_hash=current.hash)
```

**Policy:** MemoGarden provides detection, applications provide resolution strategy.

## Undo vs. Rollback

MemoGarden separates two concepts:

### Transaction Rollback

**Scope:** Current transaction  
**Timing:** Immediate (before commit)  
**Mechanism:** SQLite ROLLBACK  
**Effect:** Uncommitted changes discarded  

```python
with mg.transaction():
    mg.add_item('Note', {...})
    raise Exception()  # Auto-rollback, item not created
```

### Undo Operation

**Scope:** Committed operations  
**Timing:** Within 5 minutes of original operation  
**Mechanism:** Compensating ToolCall  
**Effect:** New facts reverse prior facts  

```python
# Create item (commits immediately)
item = mg.add_item('Note', {'text': 'wrong'})

# Undo within 5 minutes
mg.undo_tool_call(tool_call_uuid)
# Creates UndoToolCall Item
# Executes tool-specific undo logic
# May create new Items (e.g., supersession)
```

**Tool support for undo:**
```python
class ToolDefinition:
    name: str
    supports_undo: bool
    undo_fn: Optional[Callable]

# Example
def undo_add_item(original_call: ToolCall, undo_call: ToolCall):
    """Undo item creation via supersession."""
    original_item = mg.get_item(original_call.result['uuid'])
    tombstone = mg.add_item('Tombstone', {
        'supersedes': original_item.uuid,
        'reason': 'undo'
    })
```

**Properties:**
- Undo respects Soil immutability (creates new facts, doesn't delete)
- Not all tools support undo
- After 5 minutes: Operator investigates delta log, performs manual mutations
- No redo capability

## Failure Modes & Recovery

### Startup Consistency Check

```python
def startup_check(soil_conn, core_conn):
    """Check for inconsistencies on startup."""
    issues = []
    
    # 1. Check for orphaned deltas
    orphans = soil_conn.execute("""
        SELECT ed.entity_uuid, ed.new_hash
        FROM item i
        JOIN json_extract(i.data, '$.entity_uuid') AS ed_uuid
        WHERE i._type = 'EntityDelta'
        AND NOT EXISTS (
            SELECT 1 FROM core.entity e
            WHERE e.uuid = ed_uuid
            AND e.hash = json_extract(i.data, '$.new_hash')
        )
    """).fetchall()
    
    if orphans:
        issues.append(ConsistencyIssue(
            type='orphaned_delta',
            count=len(orphans),
            details=orphans
        ))
    
    # 2. Check hash chain integrity
    broken_chains = core_conn.execute("""
        SELECT uuid FROM entity
        WHERE previous_hash IS NOT NULL
        AND previous_hash != (
            SELECT hash FROM entity AS prev
            WHERE prev.uuid = (
                SELECT entity_uuid FROM soil.item
                WHERE _type='EntityDelta'
                AND json_extract(data, '$.new_hash') = entity.previous_hash
                LIMIT 1
            )
        )
    """).fetchall()
    
    if broken_chains:
        issues.append(ConsistencyIssue(
            type='broken_hash_chain',
            count=len(broken_chains),
            details=broken_chains
        ))
    
    return issues
```

### Operating Modes

```python
class SystemStatus(Enum):
    NORMAL = "normal"           # Healthy operation
    INCONSISTENT = "inconsistent"  # Detected issues, still usable
    READ_ONLY = "readonly"      # Maintenance mode
    SAFE_MODE = "safe_mode"     # Degraded, diagnostics only
```

**Mode transitions:**
```
Startup:
- No issues â†’ NORMAL
- Orphaned deltas detected â†’ INCONSISTENT
- Database corruption â†’ SAFE_MODE
- Operator flag â†’ READ_ONLY

Runtime:
- NORMAL â†’ INCONSISTENT: Commit failure (Soil ok, Core fail)
- Any â†’ READ_ONLY: Operator sets mode
- INCONSISTENT â†’ NORMAL: After successful repair
```

### Recovery Tools

**memogarden diagnose:**
```bash
$ memogarden diagnose

MemoGarden Diagnostics Report
=============================

System Status: INCONSISTENT

Issues Found:
1. Orphaned EntityDeltas: 3 deltas
   - Entity core_abc123: Delta points to hash H2, entity at H1
   - Entity core_def456: Delta points to hash H5, entity at H4
   - Entity core_ghi789: Delta points to hash H8, entity at H7

2. Database Health: OK
   - Soil: 1.2 GB, 0 integrity errors
   - Core: 450 MB, 0 integrity errors

3. Recent Errors:
   - 2026-02-02 14:23:15: Core commit failed (SQLITE_IOERR)

Recommended Actions:
- Run: memogarden repair rebuild-core
- Review: /var/log/memogarden/errors.log
```

**memogarden repair:**
```bash
$ memogarden repair rebuild-core

Rebuilding Core from Soil...
âœ“ Scanned 15,234 EntityDeltas in Soil
âœ“ Identified 3 out-of-sync entities
âœ“ Replayed deltas for core_abc123 (H1 â†’ H2)
âœ“ Replayed deltas for core_def456 (H4 â†’ H5)
âœ“ Replayed deltas for core_ghi789 (H7 â†’ H8)
âœ“ Verified hash chains

Repair complete. System status: NORMAL
```

## Performance Characteristics

### Transaction Overhead

**Single-DB operations (no explicit transaction):**
- ~1ms overhead (BEGIN/COMMIT)
- Minimal for personal system workload

**Cross-DB operations (explicit transaction):**
- ~2-5ms overhead (two BEGINs, two COMMITs)
- 5s timeout on lock contention (rare)

**Optimistic lock conflicts:**
- Retry overhead: Re-read entity, recalculate hash
- ~2-3ms per retry
- Exponential backoff if multiple conflicts

### Concurrency

**Multiple handles, same process:**
- SQLite handles locking automatically
- busy_timeout prevents indefinite blocking
- EXCLUSIVE locks serialize cross-DB operations

**Multiple processes:**
- SQLite file locking prevents corruption
- Cross-DB atomicity may degrade (no process-level coordination)
- Acceptable for personal system (rare multi-process access)

**Typical workload (personal system):**
- 10-100 transactions/day
- Peak: 1-2 transactions/second (user actively working)
- Negligible contention with conservative locking

## Testing Strategy

### Unit Tests

```python
def test_transaction_rollback():
    """Verify both DBs rolled back on error."""
    with pytest.raises(ValueError):
        with mg.transaction():
            item = mg.add_item('Note', {'text': 'test'})
            mg.add_entity('Artifact', {'label': 'test'})
            raise ValueError("test error")
    
    # Verify neither DB has changes
    assert mg.get_item(item.uuid) is None
    assert mg.get_entity('core_test') is None

def test_optimistic_lock_conflict():
    """Verify conflict detection on concurrent updates."""
    entity = mg.get_entity('core_abc')
    
    # Simulate concurrent update
    mg.update_entity('core_abc', {'v': 2}, based_on_hash=entity.hash)
    
    # This should fail
    with pytest.raises(OptimisticLockError):
        mg.update_entity('core_abc', {'v': 3}, based_on_hash=entity.hash)
```

### Integration Tests

```python
def test_split_operation_resilience():
    """Verify Item created even if relation fails."""
    # Simulate Core database locked
    core_conn.execute("BEGIN EXCLUSIVE")
    
    item = mg.add_item('Note', {'text': 'test'})
    assert item.uuid.startswith('soil_')
    
    # Relation fails (Core locked)
    with pytest.raises(DatabaseLockError):
        mg.add_user_relation('explicit_link', ctx, item.uuid, '+30d')
    
    # Item still exists
    assert mg.get_item(item.uuid) is not None
    
    # Can add relation after unlock
    core_conn.rollback()
    mg.add_user_relation('explicit_link', ctx, item.uuid, '+30d')
```

### Chaos Testing

```python
def test_power_loss_during_commit():
    """Simulate process kill between Soil and Core commits."""
    # Monkey-patch commit to kill process
    original_commit = core_conn.commit
    def kill_after_soil():
        soil_conn.commit()
        os.kill(os.getpid(), signal.SIGKILL)
    
    core_conn.commit = kill_after_soil
    
    # This will kill process after Soil commits
    with pytest.raises(SystemExit):
        with mg.transaction():
            mg.update_entity('core_abc', {...}, based_on_hash=h1)
    
    # Restart and verify inconsistency detected
    mg2 = MemoGarden()
    assert mg2.status == SystemStatus.INCONSISTENT
    issues = mg2.diagnose()
    assert len(issues) == 1
    assert issues[0].type == 'orphaned_delta'
```

## Open Questions

1. **Multi-process coordination:** Should multiple processes coordinate cross-DB operations at application level, or rely purely on SQLite locking?
   - **Recommendation:** SQLite locking sufficient for personal system. Multi-process scenarios are rare.

2. **Automatic repair:** Should system attempt automatic repair on startup for simple inconsistencies (orphaned deltas)?
   - **Recommendation:** No. Conservative policy: Report, require operator approval.

3. **Metrics storage:** Should transaction metrics (commit latency, failures) be stored in Soil as SystemEvent Items?
   - **Deferred:** Implementation detail for metrics RFC.

## References

- RFC-001 v4: Security & Operations Architecture
- RFC-002 v5: Relation Time Horizon & Fossilization
- RFC-005 v3: API Design
- RFC-006 v1: Error Handling & Diagnostics
- RFC-007 v1: Runtime Operations
- PRD v0.10.0: MemoGarden Personal Information System
- SQLite WAL mode: https://sqlite.org/wal.html
- SQLite transaction documentation: https://sqlite.org/lang_transaction.html

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-02 | Initial specification |

---

**Status:** Draft  
**Next Steps:**
1. Review transaction coordination mechanism
2. Review failure mode handling
3. Implement startup consistency checks
4. Implement transaction API with context manager
5. Test power-loss scenarios
6. Document operator recovery procedures

---

**END OF RFC**
