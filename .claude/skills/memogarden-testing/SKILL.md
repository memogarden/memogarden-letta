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

Navigate to the memogarden-core directory first:

```bash
cd /home/kureshii/memogarden/memogarden-core
```

**Run all tests:**
```bash
poetry run pytest
```

**Run specific test file:**
```bash
poetry run pytest tests/api/test_transactions.py
```

**Run specific test:**
```bash
poetry run pytest tests/api/test_transactions.py::test_create_transaction
```

**Run with verbose output:**
```bash
poetry run pytest -v
```

**Run with print statements visible:**
```bash
poetry run pytest -s
```

**Run single test for debugging:**
```bash
poetry run pytest tests/api/test_transactions.py::test_create_transaction -v -s
```

## Test Database

Tests use in-memory SQLite (`:memory:`) for isolation. The `client` fixture in [tests/conftest.py](../../memogarden/memogarden-core/tests/conftest.py) creates a fresh database for each test using a temp file (not `:memory:` directly) for proper connection sharing.

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
- If you see locking errors, check that you're using the `client` fixture correctly

**Import errors:**
- Ensure you're in the memogarden-core directory
- Run `poetry install` if dependencies are missing

**Schema errors:**
- The test fixture automatically initializes schema
- If schema changes, ensure [schema.sql](../../memogarden/memogarden-core/memogarden_core/schema/schema.sql) is up to date

## Coverage

Target >80% coverage for core functionality. To check coverage:

```bash
poetry run pytest --cov=memogarden_core --cov-report=term-missing
```
