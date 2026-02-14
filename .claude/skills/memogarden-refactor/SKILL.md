---
name: memogarden-refactor
description: Code refactoring and test optimization workflows for MemoGarden Core. Use when cleaning up code duplication, optimizing test performance, or improving code maintainability.
---

# MemoGarden Refactoring

## Refactoring Philosophy

**Clarity > Cleverness**

MemoGarden values simple, clear code over clever abstractions. Refactoring should make code easier to understand, maintain, and debug.

**Guidelines:**
- Reduce duplication (DRY principle)
- Improve code clarity and readability
- Make bugs easier to fix in one place
- Enable interface-focused testing
- Optimize for developer experience

## Code Duplication Analysis

### Identifying Duplication

Look for these patterns:
- Similar logic in multiple functions
- Repeated database query patterns
- Duplicate validation logic
- Similar error handling code
- Repeated fixture setup in tests

### Refactoring Strategies

1. **Extract common logic** into shared functions
2. **Create utility modules** for reusable operations
3. **Use composition over inheritance** when appropriate
4. **Consolidate similar test cases** into parameterized tests

### Example

**Before (duplicated):**
```python
# In three different endpoint files
def create_transaction(data):
    entity_id = uid.generate_uuid()
    create_entity(db, "transactions", entity_id)
    # ... transaction logic
    return entity_id

def create_recurrence(data):
    entity_id = uid.generate_uuid()
    create_entity(db, "recurrences", entity_id)
    # ... recurrence logic
    return entity_id
```

**After (refactored):**
```python
# In db/entity.py
def create_entity_with_type(entity_type: str) -> str:
    """Create entity and return ID."""
    entity_id = secret.generate_uuid()
    create_entity(entity_type, entity_id)
    return entity_id

# Usage
def create_transaction(data):
    entity_id = core.entity.create("transactions")
    # ... transaction logic
```

## Test Profiling

### Current Baseline

- Target: <2.8 seconds for full test suite
- Current: ~49 seconds
- Scope: 394 tests

### Profiling Commands

**Profile test execution time:**
```bash
cd /home/kureshii/memogarden/memogarden-core

# Profile with pytest-durations (slowest 10 tests)
./run_tests.sh --durations=10

# Profile all tests (durations for all)
./run_tests.sh --durations=0

# Profile with detailed timing
./run_tests.sh --setup-show -v
```

**Identify bottlenecks:**
```bash
# Profile test file loading
./run_tests.sh --collect-only --quiet

# Profile fixture initialization
./run_tests.sh --setup-show
```

### Optimization Strategies

1. **Database setup**
   - Use in-memory database (`:memory:`) when possible
   - Minimize schema initialization overhead
   - Share fixtures across tests where safe

2. **Fixture optimization**
   - Use `scope="session"` for expensive one-time setup
   - Use `scope="module"` for shared test data
   - Avoid database resets between every test when not needed

3. **Test organization**
   - Consolidate similar test cases with `@pytest.mark.parametrize`
   - Remove redundant assertions
   - Focus on critical paths, not edge cases

4. **Auth fixtures**
   - Cache JWT token generation
   - Reuse test user creation across tests
   - Minimize password hashing operations (slow with bcrypt work factor 12)

### Example: Optimizing Auth Fixtures

**Before (slow):**
```python
# Every test recreates user and hashes password
@pytest.fixture
def test_user(test_db):
    user = create_user("testuser", "password123")  # bcrypt hashing
    return user

def test_login_1(client, test_user):
    login("testuser", "password123")

def test_login_2(client, test_user):
    login("testuser", "password123")
```

**After (fast):**
```python
# Reuse user across all tests in module
@pytest.fixture(scope="module")
def test_user_module():
    user = create_user("testuser", "password123")
    return user

def test_login_1(client, test_user_module):
    login("testuser", "password123")

def test_login_2(client, test_user_module):
    login("testuser", "password123")
```

## Interface vs Implementation Testing

### Test Interface, Not Implementation

**Ask yourself:**
- Does this test verify what the function promises to do?
- Or does it verify how the function internally does it?
- Will this test survive if I refactor the implementation?

**Interface testing** (good):
```python
def test_transaction_create_returns_id(client):
    """Test that creating a transaction returns an ID."""
    response = client.post("/api/v1/transactions", json={...})
    assert response.status_code == 201
    assert "id" in response.get_json()
```

**Implementation testing** (brittle):
```python
def test_transaction_calls_entity_create_first(mocker):
    """Test that entity.create is called before transaction.insert."""
    # This couples test to internal implementation order
    mocker.patch("memogarden_core.db.entity.create")
    # ... brittle implementation test
```

### Refactoring for Testability

If implementation is hard to test at the interface level:

1. **Extract pure functions** from complex logic
2. **Use dependency injection** for database/file access
3. **Create clear boundaries** between layers
4. **Document the interface contract** explicitly

## Mock Audit

### Philosophy: No Mocks

MemoGarden avoids mocks following [testing philosophy](memogarden-testing). Use real dependencies (SQLite, filesystem, network when available).

### Audit Process

**Step 1: Find all mocks**
```bash
cd /home/kureshii/memogarden/memogarden-core
grep -r "mock\|patch\|Mock" tests/
```

**Step 2: Question each mock**
- Is this mock testing behavior or implementation?
- Can I use a real dependency instead?
- Is the test providing value?

**Step 3: Refactor or remove**
- Replace mock with real dependency (SQLite, temp files)
- If test requires mock, consider removing it
- If test is critical, refactor implementation to avoid needing mock

### Example: Removing Mocks

**Before (with mock):**
```python
def test_external_api_client(mocker):
    """Test API client handles errors."""
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mocker.patch("requests.get", return_value=mock_response)
    # ... test with mock
```

**After (real dependency):**
```python
def test_external_api_client(test_server):
    """Test API client handles errors."""
    # Use real test server that returns 500
    # Or use VCR.py to record/replay real HTTP interactions
    # Or skip integration test and test at higher level
```

## Test Cleanup

### Remove Redundant Tests

**Duplicate tests:**
```python
# Redundant - testing same thing twice
def test_create_transaction_with_amount(client):
    response = client.post("/api/v1/transactions", json={"amount": 10.0, ...})
    assert response.status_code == 201

def test_create_transaction_amount_field(client):
    response = client.post("/api/v1/transactions", json={"amount": 15.0, ...})
    assert response.status_code == 201  # Same test, different value
```

**Consolidate with parameterization:**
```python
@pytest.mark.parametrize("amount,expected", [
    (10.0, 10.0),
    (15.0, 15.0),
    (-5.0, -5.0),
])
def test_create_transaction_with_various_amounts(client, amount, expected):
    response = client.post("/api/v1/transactions", json={"amount": amount, ...})
    assert response.status_code == 201
    assert response.get_json()["amount"] == expected
```

### Remove Low-Value Tests

Tests that provide little confidence:
- Tests of internal helper functions (not part of public API)
- Tests of trivial getters/setters
- Tests that just assert code runs without checking behavior

**Example (low value):**
```python
def test_uid_generate_returns_string():
    """Test generate_uid returns a string."""
    result = uid.generate_uuid()
    assert isinstance(result, str)  # Trivial, adds little value
```

**Better (test actual behavior):**
```python
def test_uid_generate_unique_ids():
    """Test that UUIDs are unique."""
    ids = [uid.generate_uuid() for _ in range(1000)]
    assert len(set(ids)) == 1000  # Tests meaningful behavior
```

## Refactoring Workflow

1. **Profile baseline**
   - Run `./run_tests.sh --durations=10`
   - Identify top 10 slowest tests
   - Document current state

2. **Code duplication audit**
   - Search for repeated patterns
   - Identify abstraction opportunities
   - Prioritize high-impact, low-risk refactorings

3. **Test optimization**
   - Optimize fixture scopes
   - Remove redundant tests
   - Consolidate parameterized tests
   - Reduce unnecessary database resets

4. **Mock audit**
   - Find all mocks in test suite
   - Evaluate necessity of each
   - Refactor to remove or justify keeping

5. **Verify improvements**
   - Rerun profiler: `./run_tests.sh --durations=10`
   - Ensure coverage maintained (>80%)
   - Run full test suite to confirm no regressions

6. **Document changes**
   - Update implementation plan
   - Commit with clear rationale

## Success Criteria

- ✅ Test suite runs in <2.8 seconds
- ✅ No code duplication (DRY principle applied)
- ✅ No unnecessary mocks
- ✅ Tests focus on interface behavior
- ✅ Coverage maintained at >80%
- ✅ Code is clearer and more maintainable

## Commands Reference

```bash
# Profile slowest tests
./run_tests.sh --durations=10

# Profile all tests
./run_tests.sh --durations=0

# Run with coverage
./run_tests.sh --cov=memogarden_core --cov-report=term-missing

# Find duplicated code patterns
grep -r "pattern" memogarden_core/

# Find all mocks
grep -r "mock\|patch\|Mock" tests/

# Run specific test module
./run_tests.sh tests/auth/test_decorators.py -v

# Run with setup show (debug fixtures)
./run_tests.sh --setup-show
```
