# Semantic API - Core Bundle (Session 1)

**Status:** ✅ Complete
**Date:** 2026-02-07
**Tests:** 22/22 passing

## Overview

Implemented the `/mg` Semantic API endpoint with Core bundle verbs following RFC-005 v7.1. The Semantic API provides verb-based messaging for AI agents and advanced integrations, distinct from the traditional REST API.

## Architecture

### Request/Response Envelope

All Semantic API requests use a single `/mg` endpoint with verb-based dispatch:

```json
// Request
{
  "op": "create|get|edit|forget|query|link|track|search|...",
  "params": { ... },
  "request_id": "optional correlation ID"
}

// Response
{
  "ok": true|false,
  "actor": "core_uuid",
  "timestamp": "2026-02-07T10:30:00Z",
  "result": { ... },
  "error": {  // Only when ok=false
    "code": "not_found",
    "message": "Human readable description",
    "details": { }
  }
}
```

### Actor Tracking

- Requests authenticated via JWT or API key
- `actor` field contains UUID of authenticated user/agent
- Audit facts capture actor for all operations

## Core Bundle Verbs

### `create` - Create Entity
Creates a new entity (Transaction, Recurrence, Artifact, Label, Operator, Agent, Entity).

**Request:**
```json
{
  "op": "create",
  "type": "Transaction",
  "data": { "amount": 100, "currency": "SGD" }
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "uuid": "core_abc123...",
    "type": "Transaction",
    "version": 1,
    "hash": "sha256...",
    "created_at": "2026-02-07T10:30:00Z",
    "data": { "amount": 100, "currency": "SGD" }
  }
}
```

### `get` - Get Entity by UUID
Retrieves a single entity by UUID.

**Accepts both prefixed and non-prefixed UUIDs:**
- `core_abc123...` ✅
- `abc123...` ✅ (auto-detected)

**Returns:** Entity with all fields

### `edit` - Edit Entity
Updates entity fields with set/unset semantics.

**Request:**
```json
{
  "op": "edit",
  "target": "core_abc123...",
  "set": { "amount": 200 },
  "unset": ["description"],
  "based_on_hash": "previous_hash_for_optimistic_locking"
}
```

**Optimistic Locking:**
- `based_on_hash` required for concurrent update safety
- Hash mismatch → `OptimisticLockError`

### `forget` - Soft Delete
Marks entity as inactive but traces remain in Soil.

**Request:**
```json
{
  "op": "forget",
  "target": "core_abc123..."
}
```

**Note:** Entity persists with `active=0` for audit trail

### `query` - Query with Filters
Query entities with filter operators.

**Filter Operators:**
- Bare value: `{ "type": "Transaction" }` → `type = 'Transaction'`
- OR: `{ "type": {"any": ["Transaction", "Recurrence"]} }`
- NOT: `{ "active": {"not": true} }`

**Pagination:**
- `offset` - Skip N results
- `limit` - Return max N results

## Key Files

- [`api/semantic.py`](../memogarden-api/api/semantic.py) - Semantic API dispatcher
- [`api/handlers/core.py`](../memogarden-api/api/handlers/core.py) - Core verb handlers
- [`api/schemas/semantic.py`](../memogarden-api/api/schemas/semantic.py) - Pydantic schemas
- [`tests/test_semantic_api.py`](../memogarden-api/tests/test_semantic_api.py) - 22 tests

## Implementation Details

### UUID Prefix Handling

```python
def strip_prefix(uuid_str: str) -> str:
    """Remove core_ or soil_ prefix if present."""
    if uuid_str.startswith("core_"):
        return uuid_str[5:]
    if uuid_str.startswith("soil_"):
        return uuid_str[6:]
    return uuid_str

def add_core_prefix(uuid_str: str) -> str:
    """Add core_ prefix if not present."""
    if uuid_str.startswith("core_"):
        return uuid_str
    return f"core_{uuid_str}"
```

### Baseline Entity Types

Supported entity types (from JSON schemas):
- `Transaction` - Financial transaction
- `Recurrence` - Recurring transaction pattern
- `Artifact` - External document (invoice, receipt, email)
- `Label` - User-defined category
- `Operator` - Human user account
- `Agent` - AI agent account
- `Entity` - Generic entity base type

## RFC-005 v7.1 Invariants Enforced

- **INV-API-001:** Facts use `add`/`amend`, entities use `create`/`edit`
- **INV-API-002:** `create` = bring into being, `edit` = revise and publish
- **INV-API-003:** `forget` marks inactive but traces remain
- **INV-API-004:** Query filters support `=`, `{"any": [...]}`, `{"not": value}`
- **INV-API-005:** `null` = "not yet known" (Unknown), not "intentionally empty"
- **INV-API-006:** All responses include `ok`, `actor`, `timestamp`, `result`/`error`

## Deferred Features

- `register` verb - Register custom entity type schemas
- Full query DSL operators - Extended filter syntax
- Domain-specific table updates - Specialized entity handling

## Dependencies

None - Core bundle is foundational infrastructure.

## References

- RFC-005 v7.1: API Design
- Implementation Plan: Session 1
- Git commit history for detailed changes
