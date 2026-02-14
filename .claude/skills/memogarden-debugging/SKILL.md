---
name: memogarden-debugging
description: Debugging workflows and troubleshooting for MemoGarden Core. Use when debugging database issues, API errors, test failures, or unexpected behavior.
---

# MemoGarden Debugging

## Database Issues

### Check if database exists

```bash
ls -la /home/kureshii/memogarden/memogarden-core/data/
```

### Connect to SQLite directly

```bash
sqlite3 /home/kureshii/memogarden/memogarden-core/data/memogarden.db
```

### In SQLite shell

```sql
-- List tables
.tables

-- Show table schema
.schema transactions

-- Query data
SELECT * FROM transactions LIMIT 10;

-- Check entity registry
SELECT * FROM entity_registry WHERE entity_type='transactions';

-- Exit
.quit
```

### Common Database Errors

**"database is locked"**
- WAL mode is enabled by default to prevent this
- If you see this, check for multiple processes accessing the database
- Tests use temp file database to avoid locking

**"no such table"**
- Database may not be initialized
- Run: `cd memogarden-api && poetry run python -c "from memogarden_core.db import init_db; init_db()"`

**Foreign key constraint errors**
- Check that referenced entities exist in `entity_registry`
- Verify `account_id`, `category_id` exist in respective tables

## API Issues

### Check Flask dev server logs

The Flask development server shows errors in the terminal output. Look for:
- Tracebacks with exact error locations
- 400/404/500 status codes with reasons
- SQL query errors

### Test endpoints with curl

```bash
# Health check
curl http://localhost:5000/health

# List transactions
curl http://localhost:5000/api/v1/transactions

# Create transaction
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "SGD", "transaction_date": "2025-12-24", "account_id": "test-id"}'
```

### Common API Errors

**400 Bad Request**
- Request validation failed
- Check response body for specific validation error
- Verify Pydantic schema in `api/v1/schemas/`

**404 Not Found**
- Resource doesn't exist
- Check UUID is valid
- Verify resource was created in database

**500 Internal Server Error**
- Unhandled exception on server
- Check Flask logs for traceback
- Common causes: database errors, missing imports, unhandled exceptions

## Test Failures

### Run with verbose output

```bash
cd memogarden-api
./run_tests.sh -v
```

### Run with print statements visible

```bash
./run_tests.sh -s
```

### Run single test for debugging

```bash
./run_tests.sh tests/api/test_transactions.py::test_create_transaction -v -s
```

### Common Test Failures

**ImportError: No module named 'memogarden_core'**
- You're not in the memogarden-core directory
- Navigate to: `cd memogarden-api`

**"database is locked" in tests**
- Tests use temp file database via `client` fixture
- Ensure you're using the `client` fixture, not creating your own database
- WAL mode is enabled for concurrent access

**AssertionError on response data**
- Check actual vs expected: `print(response.get_json())`
- Verify schema matches what you expect
- Check database state: use sqlite3 to inspect

**Fixture not found**
- Ensure conftest.py is in tests/ directory
- Restart pytest if conftest.py was modified

## Core API Issues

### Connection not closed

If you see "too many open connections" or similar:

```python
# ✅ CORRECT - connection closes automatically
core = get_core()
entity = core.entity.get_by_id(uuid)
# Connection closes via __del__

# ✅ CORRECT - connection closes on __exit__
with get_core(atomic=True) as core:
    core.entity.create("transactions")
    # Connection closes on __exit__

# ❌ WRONG - storing Core beyond its lifecycle
cores = []
cores.append(get_core())  # Connection stays open
```

### "Core must be created with atomic=True"

You're using Core as context manager without `atomic=True`:

```python
# ❌ WRONG
with get_core() as core:  # Missing atomic=True
    ...

# ✅ CORRECT
with get_core(atomic=True) as core:
    ...
```

### Entity not found after create

You may be creating entity outside atomic mode:

```python
# ❌ WRONG - each get_core() creates separate connection
core = get_core()
entity_id = core.entity.create("transactions")
# Connection closes, transaction not committed
core2 = get_core()
entity = core2.entity.get_by_id(entity_id)  # Not found!

# ✅ CORRECT - use atomic mode for multi-step operations
with get_core(atomic=True) as core:
    entity_id = core.entity.create("transactions")
    # All operations in same transaction, commits on __exit__
```

## Debugging Workflow

1. **Identify the error type**: Database, API, test, or Core API
2. **Check logs**: Flask dev server logs, pytest output, or sqlite3 errors
3. **Isolate the issue**: Create minimal reproduction case
4. **Verify assumptions**: Check database state, request format, expected vs actual
5. **Fix and test**: Write test that reproduces issue, fix, verify test passes

## Getting More Help

If stuck:

1. Check [architecture.md](../../memogarden/memogarden-core/docs/architecture.md) for technical patterns
2. Review [AGENTS.md](../../memogarden/AGENTS.md) for project conventions
3. Look at existing code patterns in `memogarden_core/`
4. Run tests with `-v -s` for detailed output
