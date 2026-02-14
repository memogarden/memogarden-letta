# API Test Performance Profile

**Date**: 2026-02-15
**Test Run ID**: 20260215-012320
**Total Duration**: 74.65s
**Total Tests**: 251 passed

## Status: Analysis Complete, Awaiting User Decision on Fixes

## Executive Summary

The API tests take approximately 75 seconds to run. The primary bottleneck is a single SSE (Server-Sent Events) test that accounts for 40% of total runtime, combined with per-test database setup overhead affecting all tests.

**Key Finding**: Fixing the SSE test alone would reduce total test time from 75s to ~45s (40% improvement). Fixing both the SSE test and database setup could reduce total time to under 20s.

---

## 1. Critical Bottleneck: SSE Test (30 seconds)

### Test Details
- **File**: `tests/test_sse.py`
- **Test**: `TestSSEEndpoint::test_events_stream_with_scope_filter`
- **Duration**: 30.00s (call time)
- **Impact**: 40% of total test runtime

### Root Cause
The test uses Flask's test client to make a GET request to the `/mg/events` SSE endpoint. The endpoint implements an infinite stream:

```python
# From api/events.py, line 291-307
def generate():
    """Generator function for SSE stream."""
    try:
        while True:  # <-- Infinite loop
            try:
                # Block for up to 30 seconds waiting for event
                event = conn.queue.get(timeout=30)  # <-- 30 second timeout
                # ... yield event data
            except Queue.Empty:
                # Send keepalive comment to prevent timeout
                yield ": keepalive\n\n"
```

The Flask test client waits for the response to complete, but SSE streams are designed to never complete. After 30 seconds with no events in the queue, `Queue.get(timeout=30)` raises `Queue.Empty`, the keepalive is yielded, and the client continues waiting for the next iteration.

### Test Code
```python
# From tests/test_sse.py, line 335-345
def test_events_stream_with_scope_filter(self, client, auth_headers):
    """Test SSE stream with scope subscription filter."""
    # Just verify the endpoint is registered and accessible
    # Note: Streaming endpoints in Flask test client may not fully work
    # so we just check that the endpoint can be reached
    response = client.get(
        "/mg/events?scopes=core_abc,core_def",
        headers=auth_headers
    )
    # Check for 200 (streaming ready) or 401 (auth failed)
    assert response.status_code in (200, 401)
```

The comment acknowledges the issue ("Streaming endpoints in Flask test client may not fully work") but doesn't prevent the 30-second wait.

### Recommended Fix
1. Add a timeout to the test client request
2. Mock the SSE streaming for testing
3. Mark as integration test and skip in unit test suite
4. Use a test-specific SSE endpoint with shorter timeout

---

## 2. Significant Bottleneck: Per-Test Database Setup (0.26-0.54s per test)

### Setup Time Distribution
- **Slowest setup**: 0.54s (`test_recurrences.py::test_authentication_with_api_key`)
- **Fastest setup**: 0.26s (many tests)
- **Average setup**: ~0.3s per test
- **Total setup time**: 251 tests × 0.3s = ~75s cumulative

Note: Setup time overlaps with test execution (pytest runs tests in parallel when possible), but the cumulative effect is significant.

### Root Causes

#### 2.1 Schema Loading on Every Test
Each test creates a new in-memory database and loads the full schema:

```python
# From tests/conftest.py, line 189-204
with _schema_lock:
    if not _schema_initialized:
        # Load schema from the memogarden-system core.sql file
        schema_path = project_root / "memogarden-system" / "system" / "schemas" / "sql" / "core.sql"
        final_schema_sql = schema_path.read_text()
        conn.executescript(final_schema_sql)  # <-- 6,649 bytes of SQL
```

The schema files are:
- `core.sql`: 6,649 bytes
- `soil.sql`: 3,446 bytes

#### 2.2 Unique Database per Test
```python
# From tests/conftest.py, line 169
_test_db_name = f"file:memogarden_test_{uuid.uuid4()}?mode=memory&cache=shared"
```

Each test generates a new UUID for the database name, ensuring isolation but preventing schema reuse.

#### 2.3 Authentication Fixture Overhead
Tests using `test_user_app` and `auth_headers` fixtures create users and hash passwords:
```python
# From tests/conftest.py, line 469-470
password_hash = hash_password(password)  # <-- bcrypt, computationally expensive
```

The `hash_password` function uses bcrypt with a work factor, which is intentionally slow for security.

### Recommended Fixes

1. **Session-scoped database fixture**: Use `scope="session"` for database setup
2. **Transaction rollback**: Use a single database with transaction rollback between tests
3. **Mock authentication**: Pre-hash test passwords or use a faster hash for testing
4. **Lazy schema loading**: Cache parsed schema SQL in memory

---

## 3. Secondary Bottlenecks

### 3.1 Authentication Tests
Multiple tests verify authentication with API keys, each creating new API keys:
- `test_authentication_with_api_key`: 0.54s setup
- Multiple variations across `test_transactions.py`, `test_recurrences.py`

### 3.2 No Test Parallelization
Tests run sequentially. pytest-xdist could parallelize independent tests.

---

## 4. Performance Breakdown

| Component | Time | Percentage |
|-----------|------|------------|
| SSE single test | 30.0s | 40% |
| Cumulative setup overhead | ~30-40s | 40-53% |
| Actual test execution | ~5-15s | 7-20% |
| **Total** | **74.65s** | **100%** |

---

## 5. Slowest Tests (Top 10 by Call Duration)

| Rank | Test | Duration |
|------|------|----------|
| 1 | `test_sse.py::TestSSEEndpoint::test_events_stream_with_scope_filter` | 30.00s |
| 2 | `test_sse.py::TestSSEStatsEndpoint::test_stats_returns_connection_info` | <0.01s |
| 3-251 | All other tests | <0.01s each |

**Observation**: Aside from the SSE test, all individual tests execute very quickly (<10ms). The bottleneck is almost entirely in setup/infrastructure.

---

## 6. Recommended Actions

### Immediate (High Impact, Low Risk)

1. **Fix SSE Test** (30s savings)
   - Add `timeout=1` parameter to test client GET request
   - Or mock the SSE generator for testing
   - Or skip the streaming test in unit tests

2. **Pre-hash Test Passwords** (~5-10s savings)
   - Store pre-computed bcrypt hash for "TestPass123"
   - Avoid bcrypt computation in fixture

### Short-term (Medium Impact, Medium Risk)

3. **Session-scoped Database** (~20-30s savings)
   - Use `scope="session"` for `flask_app` fixture
   - Implement transaction rollback between tests
   - Requires careful test isolation verification

4. **Schema SQL Caching** (~5s savings)
   - Parse `core.sql` and `soil.sql` once at session start
   - Reuse parsed SQL for all database initializations

### Long-term (High Impact, High Risk)

5. **Test Parallelization** (~50-60s savings)
   - Implement pytest-xdist for parallel test execution
   - Requires careful fixture scoping and isolation verification
   - May expose race conditions in test suite

6. **Test Categorization**
   - Separate unit tests (no DB) from integration tests (with DB)
   - Run unit tests in CI on every commit
   - Run integration tests nightly or on PR

---

## 7. Appendix: Test Files with Slowest Setup

Top 10 by setup time (from `--setup-only` profile):

| Rank | Test | Setup Time |
|------|------|-------------|
| 1 | `test_recurrences.py::test_authentication_with_api_key` | 0.54s |
| 2 | `test_transactions.py::test_authentication_with_api_key` | 0.54s |
| 3 | `test_transactions.py::test_transaction_id_with_core_prefix` | 0.35s |
| 4 | `test_track.py::TestTrackVerb::test_track_entity_with_derived_from` | 0.35s |
| 5 | `test_sse.py::TestSSEStatsEndpoint::test_stats_returns_connection_info` | 0.35s |
| 6 | `test_audit_facts.py::TestAuditFacts::test_create_operation_creates_audit_facts` | 0.34s |
| 7 | `test_transactions.py::test_get_transaction_not_found` | 0.34s |
| 8 | `test_track.py::TestTrackVerb::test_track_simple_entity_no_sources` | 0.33s |
| 9 | `test_transactions.py::test_get_transaction` | 0.33s |
| 10 | `test_track.py::TestTrackVerb::test_track_nonexistent_entity` | 0.33s |

---

## 8. References

- Test execution log: `./run_tests.sh --durations=30`
- Fixture profiling: `./run_tests.sh --setup-only -vv`
- SSE endpoint: `api/events.py:245-324`
- Test fixtures: `tests/conftest.py:144-292`
