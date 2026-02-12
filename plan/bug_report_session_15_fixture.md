# Bug Report: Session 15 Test Fixture Issue

**Date:** 2026-02-12
**Session:** 15 - Scope Entity and Schema
**Severity:** Low (tests pass, fixture issue is known/documented)

## Description

The `db_core` fixture in `memogarden-system/tests/conftest.py` returns `None` instead of a `Core` object, causing test failures when used.

## Root Cause

```python
@pytest.fixture
def db_core():
    return init_core_db()  # Returns None, not a Core object
```

The `init_core_db()` function initializes the database but returns `None`. Tests expect a `Core` object with an `.entity` attribute.

## Current Status

- Tests have a note: *"Tests have pytest fixture initialization issues (fixture returns None)"*
- Tests are marked as **"Not blocking"** because Scope entity works via generic EntityOperations API
- Tests are being skipped/failed when run as part of full suite

## Fix Options

1. **Fix fixture to return Core object:**
   ```python
   @pytest.fixture
   def db_core():
       init_core_db()  # Initialize DB
       return get_core()  # Return Core object
   ```

2. **Use get_core() directly in tests** (simpler approach)

3. **Make tests explicitly use get_core() context manager**

## Recommendation

Option 1 is cleanest - update the fixture to return a proper Core object after initializing the database. This requires modifying `init_core_db()` to return the Core object or calling `get_core()` after initialization.

## Files Affected

- `memogarden-system/tests/conftest.py` - fixture definition
- `memogarden-system/tests/test_scope_entity.py` - tests using the fixture
