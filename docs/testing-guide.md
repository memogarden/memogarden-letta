# Testing Guide

This guide documents testing patterns, fixtures, and conventions used across MemoGarden.

## Fixtures

### Available Fixtures (from `memogarden-api/tests/conftest.py`)

| Fixture | Description | Location |
|----------|-------------|----------|
| `flask_app` | Flask app with in-memory test database | `conftest.py` |
| `client(flask_app)` | Flask test client for API requests | `conftest.py` |
| `auth_headers(test_user_app)` | JWT authentication headers | `conftest.py` |
| `test_user_app(flask_app)` | Creates test user in DB | `conftest.py` |
| `db_core` | Core instance with test DB (system tests) | `conftest.py` |

### System Test Fixtures (from `memogarden-system/tests/conftest.py`)

| Fixture | Description |
|----------|-------------|
| `db_core` | Core instance for testing entity operations |

## API Response Format

All Semantic API responses use the envelope format:

```json
{
  "ok": true | false,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T...",
  "result": {...},      // on success
  "error": {...}        // on failure
}
```

## Test Patterns

### Error Testing

```python
# ✅ Recommended: Check ok flag
assert response.json["ok"] is False

# ✅ Status code check
assert response.status_code == 404

# ✅ Error type check (for validation errors)
error = response.json.get("error", {})
assert error.get("type") in ["string_too_short", "value_error", ...]
```

### UUID Prefix Handling

```python
from system.utils import uid

# entity_ops.create() returns plain UUID
log_uuid = entity_ops.create(...)

# API returns prefixed UUIDs
assert result["uuid"] == uid.add_core_prefix(log_uuid)
```

### Entity Type Registration

When adding new entity types, update `BASELINE_ENTITY_TYPES` in
`memogarden-api/api/handlers/core.py`:

```python
BASELINE_ENTITY_TYPES = {
    "Transaction", "Recurrence", "Artifact",
    "ConversationLog",  # ← Add new types here
    ...
}
```

## Existing Test Examples

See these files for patterns:

| File | Description |
|------|-------------|
| `memogarden-api/tests/test_search.py` | Search verb tests |
| `memogarden-api/tests/test_artifact_delta_api.py` | Artifact delta API tests |
| `memogarden-api/tests/test_semantic_api.py` | Core semantic API tests |
| `memogarden-system/tests/test_artifact_delta.py` | Delta operations |
| `memogarden-system/tests/test_conversation_fold.py` | Fold operation |
| `memogarden-api/tests/test_conversation_fold_api.py` | Fold API |

## Common Test Patterns

### Creating Entities for Tests

```python
def test_something(client, auth_headers):
    # Create entity
    create_response = client.post("/mg", json={
        "op": "create",
        "type": "ConversationLog",
        "data": {"parent_uuid": None, "items": []}
    }, headers=auth_headers)

    assert create_response.status_code == 200
    entity_uuid = create_response.json["result"]["uuid"]

    # Now test the entity
    response = client.post("/mg", json={
        "op": "fold",
        "target": entity_uuid,
        ...
    }, headers=auth_headers)

    assert response.status_code == 200
```

### Testing Validation Errors

```python
def test_validation_error(client, auth_headers):
    response = client.post("/mg", json={
        "op": "some_operation",
        "invalid_field": "value"
    }, headers=auth_headers)

    # Check response indicates error
    assert response.json["ok"] is False
    assert response.status_code == 400
```

### Testing with Direct Database Access

```python
def test_with_db(core):
    # Direct entity creation
    log_uuid = core.entity.create(
        entity_type="ConversationLog",
        data={"parent_uuid": None, "items": []}
    )

    # Test operations
    result = core.conversation.fold(log_uuid=log_uuid, ...)
    assert result.collapsed is True
```

## Running Tests

### All System Tests
```bash
cd memogarden-system
poetry run pytest
```

### All API Tests
```bash
cd memogarden-api
poetry run pytest
```

### Specific Test Files
```bash
# System tests
poetry run pytest tests/test_conversation_fold.py

# API tests
poetry run pytest tests/test_conversation_fold_api.py
```

## Key Takeaways

1. **Use existing fixtures** - Don't recreate auth headers, test client setup
2. **Check `ok` flag** - More reliable than parsing error messages
3. **UUID prefixes** - Remember `entity_ops.create()` returns plain, API returns prefixed
4. **Register new entity types** - Update `BASELINE_ENTITY_TYPES` when adding entities
5. **Follow existing patterns** - Copy from working tests before writing new ones
