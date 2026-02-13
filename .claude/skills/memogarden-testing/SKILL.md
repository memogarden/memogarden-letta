---
name: memogarden-testing
description: Testing philosophy, workflows, and best practices for MemoGarden Core. Use when writing tests, running tests, debugging test failures, or checking test coverage. Focuses on behavior-focused testing without mocks.
---

# MemoGarden Testing

## Testing Philosophy

**No Mocks or Monkeypatching**

MemoGarden tests avoid mocks, monkeypatching, and other test doubles. We test behavior, not implementation details.

**Rationale:**
- Mocks couple tests to internal implementation, making refactoring brittle
- Tests with real database (`:memory:` SQLite) provide better confidence
- Behavior-focused tests survive refactoring; implementation-focused tests break
- Simpler to understand and maintain

**Guidelines:**
- Test **observable behavior**: inputs → outputs, database state, API responses
- Test **error handling**: real error conditions, not mocked exceptions
- Test **integrations**: real SQLite with actual schema, in-memory database

For detailed testing examples and patterns, see [memogarden-core/docs/architecture.md](../../memogarden/memogarden-core/docs/architecture.md).

## Running Tests

**Standard: Use run_tests.sh script**

Always use the standardized `run_tests.sh` script for test execution. This ensures consistent behavior and provides grep-able output for automation.

```bash
# MemoGarden API Tests
./memogarden-api/run_tests.sh

# MemoGarden System Tests
./memogarden-system/run_tests.sh

# MemoGarden Client Tests
./memogarden-client/run_tests.sh

# Run specific test file
./memogarden-api/run_tests.sh tests/api/test_transactions.py

# Run specific test
./memogarden-api/run_tests.sh tests/api/test_transactions.py::test_create_transaction

# Run with verbose output
./memogarden-api/run_tests.sh -v

# Run with print statements visible
./memogarden-api/run_tests.sh -s

# Run single test for debugging
./memogarden-api/run_tests.sh tests/api/test_transactions.py::test_create_transaction -v -s

# Get summary only (for agents - avoids full test output in context)
./memogarden-api/run_tests.sh --format=md --tb=no -q 2>&1 | grep -A 5 "Test Summary"
```

**Why use run_tests.sh:**
- Ensures correct Poetry environment is used
- Works from any directory
- Provides grep-able output with test run ID and summary
- Last 7 lines always contain the full summary footer (use `tail -n 7`)
- Centralized implementation via `scripts/test_entrypoint.sh` (easy to update globally)

**Agent note:** If you need functionality not supported by `run_tests.sh`, alert a human to improve `scripts/test_entrypoint.sh` centrally rather than using ad-hoc bash commands.

**Format options for agents:**
- `--format=markdown` (or `--format=md`) - Markdown output, easier for parsing
- `--format=plaintext` - Plain text without borders
- `--format=textbox` (default) - Unicode bordered box

## Test Database

Tests use in-memory SQLite (`:memory:`) for isolation. Test fixtures in each project's `tests/conftest.py` create fresh databases for each test.

## Writing Tests

Follow these patterns when writing new tests:

1. **Use the client fixture** for API endpoint tests
2. **Use the test_db fixture** for direct database tests
3. **Test observable behavior**: request → response, database state changes
4. **Test error cases**: invalid input, missing resources, constraint violations
5. **Avoid mocks**: use real SQLite with actual schema

Example test pattern:
```python
def test_create_transaction(client):
    """Test creating a transaction via API."""
    response = client.post("/api/v1/transactions", json={
        "amount": 100.00,
        "currency": "SGD",
        "transaction_date": "2025-12-24",
        "account_id": "test-account-id"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["amount"] == 100.00
```

## Common Test Failures

**Database locking errors:**
- The test fixture uses temp file database to avoid locking
- WAL mode is enabled for better concurrent access
- If you see locking errors, check that you're using the correct fixture correctly

**Import errors:**
- Ensure you're in the correct project directory (memogarden-system, memogarden-api, etc.)
- Run `poetry install` if dependencies are missing

**Schema errors:**
- The test fixture automatically initializes schema
- If schema changes, ensure schema files are up to date

## Coverage

Target >80% coverage for core functionality. To check coverage:

```bash
# System tests
./memogarden-system/run_tests.sh --cov=system --cov-report=term-missing

# API tests
./memogarden-api/run_tests.sh --cov=api --cov-report=term-missing
```
