# RFC 005: MemoGarden API Design

**Version:** 3.1  
**Status:** Draft  
**Author:** JS  
**Date:** 2026-02-02

## Summary

MemoGarden provides three distinct interfaces:
1. **Internal Python API** - Direct database access for server and internal modules
2. **REST API** - Simple CRUD operations for conventional applications
3. **Semantic API** - Message-passing interface for rich queries and graph operations

The Internal Python API is the canonical implementation. The REST and Semantic APIs are HTTP interfaces served by `memogarden-api`, which uses the Internal API to access the system.

## Motivation

Three different use cases require three different interfaces:

**Internal modules** (HTTP server, agents, importers):
- Direct database access
- Full control over transactions and performance
- Filesystem-level operations
- Same-process, same-machine

**Simple applications** (budgeting, habit tracking):
- Conventional CRUD semantics
- Namespace isolation
- Familiar REST patterns
- HTTP client libraries

**Sophisticated applications** (project studios, reflection tools):
- Semantic search and exploration
- Graph traversal
- Context-aware queries
- Fuzzy, interpretive operations

Attempting to serve all three with a single interface results in either over-complexity for simple apps or under-serving sophisticated ones.

## Architecture Overview

```
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   External Apps                     Ã¢â€â€š
Ã¢â€â€š   (budgeting, calendar, studio)     Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
               Ã¢â€â€š HTTP
               Ã¢â€ â€œ
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   memogarden-api (HTTP Server)      Ã¢â€â€š
Ã¢â€â€š                                     Ã¢â€â€š
Ã¢â€â€š   REST API:      /apps/{id}/...    Ã¢â€â€š
Ã¢â€â€š   Semantic API:  /mg                Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
               Ã¢â€â€š Python imports
               Ã¢â€ â€œ
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   Internal Python API               Ã¢â€â€š
Ã¢â€â€š   (MemoGarden class)                Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
               Ã¢â€â€š SQLite
               Ã¢â€ â€œ
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   Soil + Core databases             Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```

## Part 1: Internal Python API

### Design Principles

1. **Handle-based** - Connection-like pattern (similar to sqlite3, psycopg3)
2. **Flat namespace** - All operations are top-level methods (Soil/Core are hidden)
3. **FFI-friendly** - Designed to map to future C API for Rust/FilC rewrite
4. **Thread-per-handle** - Not thread-safe, one handle per thread
5. **Transaction-stateful** - Transaction state lives in handle, not passed as parameters

### Initialization

```python
from memogarden import MemoGarden

# Auto-detect profile (most common)
mg = MemoGarden()

# Explicit profile
mg = MemoGarden(profile='device')
mg = MemoGarden(profile='personal')

# With options
mg = MemoGarden(profile='device', options={
    'data_dir': '/custom/path',
    'encryption': True,
    'cache_size_mb': 500
})

# Testing
mg = MemoGarden(profile='memory')  # In-memory, ephemeral

# Context manager
with MemoGarden() as mg:
    results = mg.search(...)
```

**Profile system:**
- `'auto'` - Auto-detect from system (default)
- `'device'` - Dedicated hardware deployment
- `'system'` - Shared server deployment (will become `'deployed'`)
- `'personal'` - User installation
- `'container'` - Docker/K8s (will merge into `'deployed'`)
- `'memory'` - In-memory testing mode

### Core API Surface

#### Items (Soil Layer - Immutable Records)

```python
def add_item(self, type: str, content: dict, /, *, 
             metadata: Optional[dict] = None) -> Item:
    """Create immutable item in Soil layer."""

def get_item(self, uuid: str, /) -> Optional[Item]:
    """Retrieve item by UUID."""

def get_item_chain(self, uuid: str, /) -> List[Item]:
    """Get supersession chain for item (oldest to newest)."""

def amend_item(self, uuid: str, new_content: dict, /, *, 
               new_metadata: Optional[dict] = None) -> Item:
    """
    Create new item superseding existing one.
    Returns the NEW item (superseding version).
    """

def supersede_item(self, old_uuid: str, new_uuid: str, /) -> None:
    """Explicitly mark new_uuid as superseding old_uuid."""

def find_items(self, /, *, 
               type: Optional[str] = None,
               since: Optional[datetime] = None,
               until: Optional[datetime] = None,
               limit: int = 100) -> List[Item]:
    """Query items by type and time range."""
```

#### Entities (Core Layer - Mutable Beliefs)

```python
def create_entity(self, type: str, initial_state: dict, /) -> Entity:
    """Create mutable entity in Core layer."""

def get_entity(self, uuid: str, /) -> Optional[Entity]:
    """Retrieve entity by UUID (returns current state)."""

def mutate_entity(self, uuid: str, delta: dict, /) -> Entity:
    """Apply delta to entity. Returns updated entity."""

def get_entity_deltas(self, uuid: str, /, *, 
                      since: Optional[datetime] = None,
                      until: Optional[datetime] = None) -> List[Delta]:
    """Retrieve delta history for entity."""

def find_entities(self, /, *, 
                  type: Optional[str] = None,
                  state_matches: Optional[dict] = None,
                  limit: int = 100) -> List[Entity]:
    """Query entities by type and state criteria."""
```

#### Relations (Graph Edges - Cross-Layer)

```python
def relate(self, from_uuid: str, to_uuid: str, rel_type: str, /, *,
           horizon: Optional[str] = None,
           metadata: Optional[dict] = None) -> Relation:
    """
    Create relation between two items/entities.
    
    Args:
        from_uuid: Source UUID
        to_uuid: Target UUID
        rel_type: Relation type string
        horizon: Optional time horizon (e.g., '6M', '1Y')
        metadata: Optional relation metadata
    """

def unrelate(self, relation_uuid: str, /) -> None:
    """Remove relation by UUID."""

def get_relation(self, relation_uuid: str, /) -> Optional[Relation]:
    """Retrieve relation by UUID."""

def get_relations(self, uuid: str, /, *, 
                  direction: str = 'outbound',
                  rel_type: Optional[str] = None) -> List[Relation]:
    """
    Get relations for item/entity.
    
    Args:
        direction: 'outbound' | 'inbound' | 'both'
        rel_type: Optional filter by relation type
    """
```

#### Search (Semantic Queries)

```python
def search(self, /, *,
           artifact: Optional[str] = None,
           context: Optional[List[str]] = None,
           effort: str = 'quick',
           ranking: Optional[List[str]] = None,
           scope: Optional[dict] = None,
           limit: int = 20) -> SearchResult:
    """
    Execute semantic search across MemoGarden.
    
    Args:
        artifact: Optional focal point UUID
        context: List of context UUIDs
        effort: 'quick' | 'standard' | 'thorough'
        ranking: List of ranking dimensions
        scope: Dict with time windows, type filters
        limit: Maximum results to return
    
    Returns:
        SearchResult with items, interpretation, continuation token
    """

def continue_search(self, token: str, /, *, 
                    refine: Optional[dict] = None) -> SearchResult:
    """Continue previous search with optional refinement."""
```

#### Schemas

```python
def register_schema(self, type_name: str, schema: dict, /) -> None:
    """Register schema for custom type."""

def get_schema(self, type_name: str, /) -> Optional[dict]:
    """Retrieve schema for type."""

def list_schemas(self) -> List[str]:
    """List all registered schema type names."""

def validate_content(self, type_name: str, content: dict, /) -> ValidationResult:
    """Validate content against schema without storing."""
```

#### Transactions

```python
def begin_transaction(self) -> None:
    """Enter transaction mode. Raises if already in transaction."""

def commit_transaction(self) -> None:
    """Commit current transaction. Raises if not in transaction."""

def rollback_transaction(self) -> None:
    """Rollback current transaction. Raises if not in transaction."""

def in_transaction(self) -> bool:
    """Check if currently in transaction."""

@contextmanager
def transaction(self):
    """
    Context manager for transactions.
    Auto-commits on success, auto-rolls-back on exception.
    
    Locks both Soil and Core databases with EXCLUSIVE locks.
    Cross-database atomicity is best-effort. Rare failures
    (~0.01%/year) require operator intervention via `memogarden repair`.
    
    For detailed transaction semantics, see RFC-008.
    """
```

#### Lifecycle

```python
def close(self) -> None:
    """Close handle and release resources."""

def is_open(self) -> bool:
    """Check if handle is open."""
```

### Internal-Only Operations

These operations require filesystem access and are only available in the Internal API:

```python
# Database administration
def vacuum(self) -> None:
    """Compact databases (VACUUM)."""

def analyze(self) -> None:
    """Update query planner statistics."""

def checkpoint(self) -> None:
    """Force WAL checkpoint."""

def backup(self, dest_path: str, /) -> None:
    """Backup databases to path."""

def get_db_stats(self) -> dict:
    """Database size, page count, fragmentation."""

# Internal utilities (private, underscore-prefixed)
def _detect_profile(self) -> str:
    """Auto-detect deployment profile from system."""

def _resolve_paths(self, profile: str) -> dict:
    """Resolve data_dir, config_dir per profile."""

def _load_bundled_schemas(self) -> None:
    """Load schemas from package resources."""
```

### Data Types

```python
@dataclass
class Item:
    """Immutable record from Soil layer."""
    uuid: str
    type: str
    content: dict
    metadata: dict
    created_at: datetime
    superseded_by: Optional[str]

@dataclass
class Entity:
    """Mutable belief from Core layer."""
    uuid: str
    type: str
    state: dict
    created_at: datetime
    updated_at: datetime

@dataclass
class Delta:
    """Entity mutation record."""
    uuid: str
    entity_uuid: str
    changes: dict
    applied_at: datetime
    source: Optional[str]

@dataclass
class Relation:
    """Graph edge between items/entities."""
    uuid: str
    from_uuid: str
    to_uuid: str
    rel_type: str
    horizon: Optional[str]
    metadata: dict
    created_at: datetime

@dataclass
class SearchResult:
    """Rich search results with metadata."""
    items: List[Union[Item, Entity]]
    token: Optional[str]
    cache_expires_at: Optional[datetime]
    interpretation: SearchInterpretation
    performance: SearchPerformance
    limitations: List[SearchLimitation]
    
    def has_more(self) -> bool:
        return (self.token is not None and 
                self.performance.continuations_remaining > 0)
```

### Thread Safety

**One handle per thread.** Handles are NOT thread-safe:

```python
# Ã¢Å“â€œ Good: One handle per thread
def worker():
    mg = MemoGarden()
    mg.add_item('Note', {...})
    mg.close()

# Ã¢Å“â€” Bad: Shared handle across threads
mg = MemoGarden()
def worker():
    mg.add_item('Note', {...})  # Race conditions!
```

Multiple handles can safely access the same database (SQLite handles locking).

## Part 2: HTTP API Server

The `memogarden-api` package provides an HTTP server with two interfaces:

### Server Architecture

Single FastAPI server, two route groups:

```python
# memogarden-api/api/main.py
from memogarden import MemoGarden
from fastapi import FastAPI

app = FastAPI()

# Singleton internal handle
_mg = MemoGarden(profile='auto')

# REST API routes
@app.post("/apps/{app_id}/items")
async def create_item(app_id: str, request: ItemRequest):
    item = _mg.add_item(request.type, request.content,
                        metadata={'app_id': app_id})
    return ItemResponse.from_item(item)

# Semantic API dispatcher
@app.post("/mg")
async def semantic_api(message: dict):
    op = message.get("op")
    handler = HANDLERS.get(op)
    return await handler(_mg, message)
```

### REST API

**Purpose:** Simple CRUD for conventional applications

**Pattern:** Resource-oriented paths with HTTP verbs

**Namespace isolation:** Apps scoped to `/apps/{app_id}/...`

```
# Items
POST   /apps/{app_id}/items
GET    /apps/{app_id}/items/{uuid}
GET    /apps/{app_id}/items?type=Email&since=2026-01-01
PUT    /apps/{app_id}/items/{uuid}         # Actually creates superseding item
DELETE /apps/{app_id}/items/{uuid}

# Entities  
POST   /apps/{app_id}/entities
GET    /apps/{app_id}/entities/{uuid}
PATCH  /apps/{app_id}/entities/{uuid}      # Delta application
DELETE /apps/{app_id}/entities/{uuid}

# Relations
POST   /apps/{app_id}/relations
GET    /apps/{app_id}/relations?from={uuid}
DELETE /apps/{app_id}/relations/{uuid}
```

**Characteristics:**
- Conventional REST semantics
- Apps cannot modify each other's data
- Returns current state only (no delta history exposed)
- Predictable, testable, familiar to developers

### Semantic API

**Purpose:** Rich semantic queries, graph operations, contextual search

**Pattern:** Message-passing to single endpoint

**Endpoint:** `POST /mg`

**Message format:**
```json
{
  "op": "search",
  "artifact": "uuid-123",
  "context": ["uuid-456", "uuid-789"],
  "effort": "quick",
  "ranking": ["similarity", "recency"],
  "limit": 20
}
```

**Supported operations:**
```
POST /mg
Body: {"op": "search", "artifact": "...", "context": [...], ...}
Body: {"op": "continue", "token": "...", "refine": {...}}
Body: {"op": "get_item", "uuid": "..."}
Body: {"op": "get_entity", "uuid": "..."}
Body: {"op": "relate", "from_uuid": "...", "to_uuid": "...", "rel_type": "..."}
Body: {"op": "get_relations", "uuid": "...", "direction": "outbound"}
Body: {"op": "mutate_entity", "uuid": "...", "delta": {...}}
Body: {"op": "amend_item", "uuid": "...", "new_content": {...}}
```

**Response format:**
```json
{
  "result": {...},
  "interpretation": {
    "context_summary": "collaborative work on semantic-web project",
    "ranking_applied": "similarity(0.6) Ãƒâ€” recency(0.3) Ãƒâ€” significance(0.1)",
    "scope_description": "last 90 days, work+project contexts"
  },
  "performance": {
    "execution_ms": 145,
    "depth_reached": 2,
    "continuations_remaining": 3
  },
  "limitations": [
    {"type": "partial_results", "message": "..."}
  ]
}
```

**Characteristics:**
- All parameters in JSON body (no URL params except endpoint)
- Fuzzy, interpretive queries
- Returns rich metadata about interpretation
- Cross-app visibility (can query across namespaces)
- Context-dependent, non-deterministic results

### Why `/mg`?

Following GraphQL's pattern (`/graphql`), the semantic API lives at a memorable short path:

- **Short and punchy** - Easy to type, remember
- **Parallel to `/gql`** - Similar feel to GraphQL shorthand
- **Clear separation** - Obviously different from REST resources
- **Clean URLs** - `http://localhost:8080/mg`

Not called a "query language" because it's not - it's message-passing with interpretation, not a structured query syntax.

### Single Server, Two Paradigms

**Why not separate servers?**
- Simpler deployment (one process, one port)
- Shared resources (single MemoGarden handle)
- Unified auth/middleware
- Can split later if loads diverge

**API Layout:**
```
GET    /                           # API documentation
GET    /health                     # Health check

# REST API (resource-oriented)
POST   /apps/{app_id}/items
GET    /apps/{app_id}/items/{id}
...

# Semantic API (message-passing)
POST   /mg
```

### Implementation Example

```python
from fastapi import FastAPI, HTTPException
from typing import Dict, Any

app = FastAPI()

# Semantic API handlers
HANDLERS = {
    "search": handle_search,
    "continue": handle_continue,
    "relate": handle_relate,
    "get_item": handle_get_item,
    # ...
}

@app.post("/mg")
async def semantic_api(message: Dict[str, Any]):
    """Single dispatcher for all semantic operations."""
    op = message.get("op")
    
    if not op:
        raise HTTPException(400, "Missing 'op' field")
    
    handler = HANDLERS.get(op)
    if not handler:
        raise HTTPException(400, f"Unknown operation: {op}")
    
    # Structured logging for observability
    logger.info("semantic_api", op=op, message_keys=list(message.keys()))
    
    try:
        result = await handler(_mg, message)
        return result
    except Exception as e:
        logger.error("semantic_api_error", op=op, error=str(e))
        raise
```

**Observability:**
```
# Logs show operation type
POST /mg 200 145ms op=search artifact=uuid-123
POST /mg 200 2340ms op=continue token=abc123

# Metrics per operation
metrics.increment(f"mg.{op}.count")
metrics.timing(f"mg.{op}.duration", duration)
```

## Part 3: External Client Libraries

For external apps that want native API instead of raw HTTP:

### Python Client

```python
# memogarden/client.py
from typing import Optional, List
import requests

class MemoGardenClient:
    """Network client for external applications."""
    
    def __init__(self, 
                 uri: str = 'http://localhost:8080',
                 *,
                 token: Optional[str] = None,
                 timeout: int = 30):
        """
        Connect to MemoGarden HTTP server.
        
        Args:
            uri: Server endpoint URL
            token: Authentication token
            timeout: Request timeout in seconds
        """
        self.uri = uri.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'
    
    # Semantic API methods (use /mg)
    def search(self, /, **kwargs) -> SearchResult:
        """Execute semantic search."""
        response = self.session.post(
            f'{self.uri}/mg',
            json={'op': 'search', **kwargs},
            timeout=self.timeout
        )
        response.raise_for_status()
        return SearchResult(**response.json())
    
    def continue_search(self, token: str, /, *, 
                        refine: Optional[dict] = None) -> SearchResult:
        """Continue previous search."""
        response = self.session.post(
            f'{self.uri}/mg',
            json={'op': 'continue', 'token': token, 'refine': refine},
            timeout=self.timeout
        )
        response.raise_for_status()
        return SearchResult(**response.json())
    
    def relate(self, from_uuid: str, to_uuid: str, rel_type: str, /, *,
               horizon: Optional[str] = None) -> Relation:
        """Create relation."""
        response = self.session.post(
            f'{self.uri}/mg',
            json={
                'op': 'relate',
                'from_uuid': from_uuid,
                'to_uuid': to_uuid,
                'rel_type': rel_type,
                'horizon': horizon
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return Relation(**response.json())
    
    # REST API methods (use /apps/{app_id}/...)
    def add_item_to_app(self, app_id: str, type: str, content: dict, /, *,
                        metadata: Optional[dict] = None) -> Item:
        """Create item via REST API (app-scoped)."""
        response = self.session.post(
            f'{self.uri}/apps/{app_id}/items',
            json={'type': type, 'content': content, 'metadata': metadata},
            timeout=self.timeout
        )
        response.raise_for_status()
        return Item(**response.json())
    
    # Connection management
    def ping(self) -> bool:
        """Test if server is reachable."""
        try:
            response = self.session.get(f'{self.uri}/health', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def close(self) -> None:
        """Close session."""
        self.session.close()
```

**Usage:**
```python
from memogarden.client import MemoGardenClient

# Connect to server
mg = MemoGardenClient(uri='http://localhost:8080')

# Use semantic API
results = mg.search(artifact='uuid-123', effort='quick')
more = mg.continue_search(results.token)

# Use REST API (app-scoped)
item = mg.add_item_to_app('budgeting-app', 'Transaction', {...})

mg.close()
```

### TypeScript/Dart Clients

Similar pattern - separate classes for network clients, same API surface as Python client.

## Internal vs External API Summary

### Internal API (`memogarden` package)

**Who uses it:**
- `memogarden-api` HTTP server
- Internal modules (agents, importers)
- Admin tools, testing scripts

**Characteristics:**
- Direct SQLite access
- Filesystem operations
- Profile detection
- Full transaction control
- Database administration

**Constructor:**
```python
mg = MemoGarden()  # Auto-detect profile
mg = MemoGarden(profile='device', options={...})
```

### External API (HTTP + Client Libraries)

**Who uses it:**
- External applications (budgeting, calendar, studio)
- Mobile apps
- Third-party integrations

**Characteristics:**
- HTTP/WebSocket protocol
- Authentication/authorization
- No filesystem access
- Network resilience (retries, timeouts)

**Constructor:**
```python
mg = MemoGardenClient(uri='http://...', token='...')
```

## Cross-Language Portability

### Design for FFI

The Internal Python API is designed to eventually map to C functions:

```c
// Hypothetical future C API
typedef struct mg_handle mg_handle;

mg_handle* mg_open(const char* profile, const char* options_json);
void mg_close(mg_handle* mg);

char* mg_add_item(mg_handle* mg, const char* type, 
                  const char* content_json, const char* metadata_json);
char* mg_search(mg_handle* mg, const char* params_json);
```

### Portability Rules

1. **Simple types at boundaries** - JSON-serializable only
2. **Consistent method names** - Same vocabulary across languages
3. **Null/None for missing** - Universal absence representation
4. **Flat namespace** - No nested resource objects
5. **Synchronous core** - Async wrappers per language

### Language-Specific Idioms

Each language uses natural patterns while maintaining semantic equivalence:

**Python:**
```python
with MemoGarden() as mg:
    item = mg.add_item('Email', {'text': '...'}, metadata={'tags': ['work']})
    results = mg.search(artifact=item.uuid, effort='quick')
```

**TypeScript:**
```typescript
const mg = new MemoGarden();
try {
  const item = mg.addItem('Email', {text: '...'}, {tags: ['work']});
  const results = mg.search({artifact: item.uuid, effort: 'quick'});
} finally {
  mg.close();
}
```

**Dart:**
```dart
final mg = MemoGarden();
try {
  final item = mg.addItem('Email', {'text': '...'}, metadata: {'tags': ['work']});
  final results = mg.search(artifact: item.uuid, effort: 'quick');
} finally {
  mg.close();
}
```

## Open Questions

1. **Schema system** - Full design for registration, inheritance, validation enforcement
2. **Transaction semantics** - Cross-database consistency (Soil + Core), rollback strategy
3. **Configuration management** - Runtime config, environment variables, precedence rules
4. **Error handling** - Complete exception taxonomy, error codes for cross-language consistency
5. **Context mechanism integration** - API surface for RFC-003 context capture
6. **Fossilization API** - API surface for RFC-002 time horizons and fossilization
7. **Multi-handle coordination** - Concurrent access patterns, lock contention handling
8. **Authentication/authorization** - For HTTP APIs (REST and Semantic)
9. **Rate limiting** - Per-app, per-operation policies
10. **Async wrappers** - For internal API (sync core + async wrappers)

## Future Extensions

1. **WebSocket subscriptions** - Real-time entity change notifications
2. **Graph traversal operations** - BFS, DFS, shortest path, subgraph extraction
3. **Query builder** - Fluent interface for complex search construction
4. **Streaming results** - Yield results incrementally for large queries
5. **Backup/restore API** - Handle-level database operations
6. **Statistics API** - Query execution stats, storage usage, index health
7. **Migration tools** - Schema evolution and data transformation

## References

- RFC-001 v4: Security & Operations Architecture
- RFC-002 v5: Relation Time Horizon & Fossilization
- RFC-003 v2: Context Capture Mechanism
- RFC-004 v1: Package Structure & Deployment
- PRD v0.10.0: MemoGarden Personal Information System
- SQLite C API: https://www.sqlite.org/c3ref/intro.html
- Python DB-API 2.0: https://peps.python.org/pep-0249/
- GraphQL: https://graphql.org/
- JSON-RPC 2.0: https://www.jsonrpc.org/

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-02 | Initial dual-interface design (REST + message-passing) |
| 2.0 | 2026-02-02 | Complete Python API specification with cross-language portability |
| 3.0 | 2026-02-02 | Internal vs External API distinction, /mg endpoint, single server architecture |
| 3.1 | 2026-02-02 | Transaction API clarification: cross-DB atomicity note, reference to RFC-008 |

---

**Status:** Draft  
**Next Steps:**
1. Review and approve three-interface design
2. Implement Internal API (MemoGarden class)
3. Implement HTTP server with REST and Semantic APIs
4. Implement External Client (MemoGardenClient class)
5. Write comprehensive tests for all three interfaces
6. Document usage patterns and migration guides

---

**END OF RFC**
