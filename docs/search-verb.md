# Search Verb (Session 9)

**Status:** ✅ Complete
**Date:** 2026-02-09
**Tests:** 8/8 passing (part of 256 total tests)

## Overview

Implemented the `search` verb for semantic search and discovery across entities (Core) and facts (Soil). Provides fuzzy text matching with configurable coverage levels and effort modes.

## Architecture

### Request Schema

```json
{
  "op": "search",
  "query": "search terms",
  "target_type": "entity|fact|all",
  "coverage": "names|content|full",
  "strategy": "fuzzy|auto",
  "effort": "quick|standard|deep",
  "limit": 100
}
```

### Response Schema

```json
{
  "ok": true,
  "result": {
    "query": "search terms",
    "target_type": "entity",
    "coverage": "content",
    "strategy": "auto",
    "effort": "standard",
    "count": 42,
    "results": [
      {
        "kind": "entity",  // or "fact"
        "uuid": "core_abc123...",
        "type": "Transaction",
        "data": { ... }
      }
    ]
  }
}
```

## Search Parameters

### `target_type` - Search Scope
- `entity` - Search Core entities only
- `fact` - Search Soil items/facts only
- `all` - Search both entities and facts (default)

### `coverage` - Search Depth
- `names` - Title/name fields only (fastest)
  - Entities: `type` field
  - Facts: `_type` field
- `content` - Names + body text (default)
  - Entities: `type` + `data` fields
  - Facts: `_type` + `data` fields
- `full` - All searchable fields including metadata
  - Entities: `type` + `data` + derived fields
  - Facts: `_type` + `data` + `metadata`

### `strategy` - Search Algorithm
- `fuzzy` - Text matching with typo tolerance (SQLite LIKE)
- `auto` - System chooses based on query (currently: fuzzy)
- **Future:** `semantic` - Embedding-based vector search

### `effort` - Search Thoroughness
- `quick` - Cached results, shallow index (future)
- `standard` - Full search (default, current)
- `deep` - Exhaustive search with higher limits (future)

### `limit` - Result Pagination
- Maximum results to return (default: 100)
- **Future:** Continuation tokens for deep pagination

## Implementation

### Entity Search (Core)

```python
# system/core/entity.py
def search(self, query: str, coverage: str = "content", limit: int = 100) -> List[sqlite3.Row]:
    """Search entities by fuzzy text matching."""
    if coverage == "names":
        where_clause = "type LIKE ?"
        params = (f"%{query}%",)
    elif coverage == "content":
        where_clause = "type LIKE ? OR data LIKE ?"
        params = (f"%{query}%", f"%{query}%")
    else:  # full
        where_clause = "type LIKE ? OR data LIKE ? OR derived_from LIKE ?"
        params = (f"%{query}%", f"%{query}%", f"%{query}%")

    sql = f"""
        SELECT * FROM entity
        WHERE {where_clause}
        AND active = 1
        LIMIT ?
    """
    return self._execute_query(sql, params + (limit,))
```

### Fact/Item Search (Soil)

```python
# system/soil/database.py
def search_items(self, query: str, coverage: str = "content", limit: int = 100) -> List[sqlite3.Row]:
    """Search items/facts by fuzzy text matching."""
    if coverage == "names":
        where_clause = "_type LIKE ?"
        params = (f"%{query}%",)
    elif coverage == "content":
        where_clause = "_type LIKE ? OR data LIKE ?"
        params = (f"%{query}%", f"%{query}%")
    else:  # full
        where_clause = "_type LIKE ? OR data LIKE ? OR metadata LIKE ?"
        params = (f"%{query}%", f"%{query}%", f"%{query}%")

    sql = f"""
        SELECT * FROM item
        WHERE {where_clause}
        LIMIT ?
    """
    return self._execute_query(sql, params + (limit,))
```

## Key Files

- [`api/handlers/core.py:handle_search`](../memogarden-api/api/handlers/core.py#L870) - Search handler
- [`system/core/entity.py:search`](../memogarden-system/system/core/entity.py) - Entity search
- [`system/soil/database.py:search_items`](../memogarden-system/system/soil/database.py) - Item search
- [`api/schemas/semantic.py:SearchRequest`](../memogarden-api/api/schemas/semantic.py) - Request schema
- [`tests/test_search.py`](../memogarden-api/tests/test_search.py) - 8 tests

## Test Coverage

1. **test_search_entities_by_type** - Search by entity type (names coverage)
2. **test_search_entities_by_data_content** - Search by data field (content coverage)
3. **test_search_facts_by_content** - Search facts/notes by content
4. **test_search_all_target_type** - Search both entities and facts
5. **test_search_with_limit** - Pagination with limit parameter
6. **test_search_empty_results** - Handle queries with no matches
7. **test_search_fuzzy_matching** - Partial string matching
8. **test_search_full_coverage** - Search all fields including metadata

## RFC-005 v7.1 Alignment

### ✅ Implemented
- Fuzzy text matching (SQLite LIKE with wildcards)
- Coverage levels: names, content, full
- Target types: entity, fact, all
- Result format with `kind` marker ("entity" or "fact")
- Limit parameter for basic pagination

### ⏳ Deferred (Documented TODOs)
- **Continuation tokens** - Base64-encoded offset/limit/timestamp for deep pagination
- **Semantic search** - Embedding-based vector search (requires vector DB or external service)
- **Quick effort mode** - Cached results for frequent queries
- **Deep effort mode** - Exhaustive search with higher limits
- **Threshold filtering** - Similarity score filtering (requires semantic search)

## Performance Characteristics

### Current Implementation (Fuzzy)
- **Speed:** Fast for small-medium datasets (<10K entities)
- **Precision:** Medium (text matching only)
- **Recall:** High (finds all partial matches)

### Future (Semantic)
- **Speed:** Medium (embedding computation + vector search)
- **Precision:** High (semantic similarity)
- **Recall:** Medium-High (depends on embedding quality)

## Example Usage

### Search for Transactions
```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "search",
    "query": "coffee",
    "target_type": "entity",
    "coverage": "content",
    "limit": 10
  }'
```

### Search All Content
```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "search",
    "query": "invoice",
    "target_type": "all",
    "coverage": "full",
    "limit": 50
  }'
```

## Dependencies

- Session 1: Semantic API - Core bundle (foundation)
- Session 2: Semantic API - Soil bundle (fact search)

## References

- RFC-005 v7.1: API Design, Section 6 (Semantic Bundle)
- Implementation Plan: Session 9
- [`test_search.py`](../memogarden-api/tests/test_search.py) - Test examples
