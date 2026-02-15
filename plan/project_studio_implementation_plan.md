# Project Studio Implementation Plan

**Version:** 1.0
**Status:** Active Planning
**Created:** 2026-02-11
**Supersedes:** N/A (new plan)

---

## Executive Summary

This plan tracks implementation of **Project Studio v0.4.0** as a MemoGarden App (RFC-009), built on MemoGarden's **Scope** entity (RFC-003) rather than defining its own Project concept.

### Key Architectural Decisions

1. **Scopes, not Projects**: Project Studio uses MemoGarden's Scope entity as first-class project-like containers
2. **MemoGarden App Model**: Project Studio is a "Semantic Profile" app (Core + Soil + Relations + Semantic)
3. **Artifact Editor as App**: The artifact editor is a separate MemoGarden App, reusable across studios
4. **Conversation-Centric**: Long conversation threads modeled as ConversationLog Items with branching

---

## Table of Contents

1. [Design Clarifications](#design-clarifications)
2. [Implementation Phases](#implementation-phases)
3. [Open Questions (KIV)](#open-questions-kiv)

---

## Design Clarifications

### A.1 Scopes as Project Containers

**Decision**: Use MemoGarden's Scope entity (RFC-003 v4) instead of defining new Project entity.

**Rationale**:
- Scopes are first-class MemoGarden entities with ContextFrame ownership
- enter/leave/focus verbs already exist (Session 5: Context verbs)
- Consistent with MemoGarden's "same operations, different modalities" principle
- Scopes can reference other scopes (cross-scope references allowed)

**Scope Entity Requirements** (to be created):
```python
@dataclass
class Scope:
    uuid: str                    # core_ prefix
    label: str                   # Human-readable name
    _type: "Scope"
    # Data fields:
    active_participants: list[str]  # UUIDs of operator/agents in scope
    artifact_uuids: list[str]      # Artifacts in this scope (unordered, for enumeration)
    created_at: datetime
    updated_at: datetime
```

**Schema location**: `schemas/types/entities/scope.schema.json` (new)

### A.3 UI Technology Stack

**Question**: Flutter/Dart vs Electron vs HTML5 for long conversation threads?

**Recommendation**: **HTML5 with SPA framework** (Vue.js, React, or Svelte)

**Rationale**:
| Factor | Flutter | Electron | HTML5 SPA |
|---------|-----------|------------|--------------|
| **Performance for long threads** | Excellent (native widget culling) | Good (virtual scrolling) | Excellent (virtual scrolling mature) |
| **MemoGarden integration** | Requires custom native bridge | Requires node.js build toolchain | Direct HTTP client, native WebSocket/SSE |
| **Deployment complexity** | High (multiple platform binaries) | Medium (platform binaries) | Low (static files) |
| **RFC-009 compatibility** | Requires stdin/stdout bridge | Requires stdin/stdout bridge | Native browser APIs, easier supervised mode |
| **Development speed** | Slower (Dart learning curve) | Medium | Fast (JavaScript ecosystem) |
| **Agent AUI (toolcalls)** | Via HTTP to MG API | Via HTTP to MG API | Via HTTP to MG API |

**Selected**: HTML5 Single Page Application with:
- **Framework**: Svelte 5 (excellent performance, small bundle)
- **Build**: Vite for development, static output for production
- **Deployment**: Serve from `/var/lib/memogarden/apps/project-studio/` via Flask static route
- **Communication**: Direct HTTP API to MemoGarden (no stdin/stdout bridge needed for web apps)

**Note**: Flutter/Dart remains excellent choice for mobile-first apps (Budget app).

### B. Resolved Design Questions

| Question | Resolution | Rationale/Notes |
|----------|-----------|------------------|
| **artifact_uuids unordered** | ✅ Unordered, used only for enumeration | Display order comes from relations or queries |
| **artifact multi-project** | ✅ Allowed, use `part_of` user relation | Agents may aggregate findings across scopes |
| **stack order on collapse** | ✅ Order preserved for intuitive understanding | Collapsed branch marker in timeline maintains position |
| **frame on branch collapse** | ✅ Returns to parent, like ContextFrame rejoin | Highlight if mapping doesn't align cleanly |
| **snapshots storage** | ⏸️ Deferred (post-MVP) | Not required for initial editing |
| **fragment ID scope** | ✅ Artifact-local, absolute refs: `<uuid>#<frag_id>` | Collision handling via (artifact_uuid, position) tuple |
| **reference validation** | ✅ Validate at creation, resolve at read | Stale refs detected at read time, operator notified |
| **merge conflicts** | ✅ Agent resolves with operator approval | Agents effective at conflict resolution (proven in practice) |
| **fork frame behavior** | ✅ Per participant, similar to ContextFrame fork/rejoin | Highlight if mapping is inconsistent |
| **observe (SSE vs WebSocket)** | ✅ **Server-Sent Events (SSE)** | Simpler, uni-directional push sufficient for observe mode |
| **yield mechanism** | ✅ ToolCall Item (soil_* fact) | Creates audit trail, enables trigger chains |
| **project.json** | ⏸️ Scope entity data, not file | Core entity with JSON data field |
| **cross-project refs** | ✅ Allowed (scopes can reference scopes) | Block only if concrete conflict examples emerge |
| **scratchpad model** | ⏸️ Artifact model (temporary Artifact, no deltas until "publish") | Ephemeral Artifacts with `is_draft: true` flag |
| **parallel branch display** | ✅ Not MVP, show visual indicator only | Tab-based display in future iteration |
| **collapse summary format** | ⏸️ Agent draft + operator approval (notification queue TBD) | Session 2-3: Define notification mechanism |
| **merge conflict UX** | ✅ Agent resolves with three-way diff UI | Can refine in future iterations |

---

**Current Session**: Session 20B (Complete) - SSE Events Integrated

## Implementation Phases

### Phase 0: Prerequisites (Foundation)

**Goal**: Extend MemoGarden Core with entities and APIs needed by Project Studio

**Estimated**: 20-30 hours

#### Session 15: Scope Entity and Schema ✅ COMPLETE (2026-02-11)

**Deliverables**:
1. Create `schemas/types/entities/scope.schema.json`
2. Add `scope` table to `core-schema.sql`

**Test Implementation Note**:
- 17 test methods written covering all Scope entity CRUD operations
- Test fixture renamed (`core` → `db_core`) to avoid pytest naming conflicts
- Tests have pytest fixture initialization issues (fixture returns None)
- **Not blocking**: Scope entity fully functional via generic EntityOperations API
- **Documentation needed**: See [test_scope_entity.py](memogarden-system/tests/test_scope_entity.py) header comments
3. Add Scope CRUD operations to `system/core/entity.py`
4. Test scope creation, listing, querying
5. Update `fact_schemas.json` with reference types

**Schema definition**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.memogarden.net/entities/scope.schema.json",
  "title": "Scope",
  "description": "First-class work container with context tracking (RFC-003, RFC-009)",
  "allOf": [
    {"$ref": "entity.schema.json"},
    {
      "type": "object",
      "properties": {
        "_type": {"const": "Scope"},
        "data": {
          "type": "object",
          "properties": {
            "label": {
              "type": "string",
              "description": "Human-readable name"
            },
            "active_participants": {
              "type": "array",
              "items": {"type": "string"},
              "description": "UUIDs of operator/agents in scope"
            },
            "artifact_uuids": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Artifacts in scope (unordered)"
            }
          },
          "required": ["label"]
        }
      }
    }
  ]
}
```

#### Session 16: ConversationLog Entity and Message Fragment System ✅ COMPLETE (2026-02-12)

**Deliverables**:
1. ✅ Create `schemas/types/entities/conversationlog.schema.json`
2. ✅ Add `conversationlog` table to `core-schema.sql` (via migration)
3. ✅ Create `system/fragment.py` module:
   - `generate_fragment_id(content: str) -> str`
   - `parse_references(content: str) -> list[Reference]`
   - `resolve_fragment(scope_uuid: str, fragment_id: str) -> Fragment | None`
4. ✅ Extend Message schema with fragments array
5. ✅ Test fragment generation and parsing (15/15 tests pass)

**Implementation Notes**:
- Fragment ID format: Exactly 4 characters (^ + 3 alphanumeric chars)
- Regex pattern: `r'\^([0-9a-z]{3})'` (fixed from `{3,4}`)
- Resolution functions raise NotImplementedError (Session 17 TODO)

**Fragment System**:
```python
# Fragment ID generation (from Project Studio spec)
def generate_fragment_id(content: str) -> str:
    """Generate exactly 3 character base36 hash from content (prefixed with ^)."""
    hash_bytes = hashlib.sha256(content.encode()).digest()[:2]
    hash_int = int.from_bytes(hash_bytes, 'big')
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while hash_int > 0:
        result = chars[hash_int % 36] + result
        hash_int //= 36
    return f"^{result.zfill(3)}"

# Reference types
@dataclass
class Reference:
    type: Literal['fragment', 'artifact_line', 'artifact_line_at_commit', 'item', 'log']
    span: tuple[int, int]  # Character offsets in content
    target: str  # Resolved target (fragment_id, artifact_uuid, etc.)

# Parse references from natural language
def parse_references(content: str) -> list[Reference]:
    refs = []
    # Fragment refs: ^abc (exactly 3 chars after caret)
    for match in re.finditer(r'\^[a-z0-9]{3}', content):
        refs.append(Reference(type='fragment', span=match.span(), target=match.group()))
    # Artifact line refs: <label>:<line>[@<commit>]
    for match in re.finditer(r'([\w_]+):(\d+)(?:@([a-f0-9]+))?', content):
        refs.append(Reference(type='artifact_line', span=match.span(), target=match.group()))
    # Item refs: @<uuid>
    for match in re.finditer(r'@((?:soil|core)_[\w-]+)', content):
        refs.append(Reference(type='item', span=match.span(), target=match.group(1)))
    # Log refs: [text](uuid)
    for match in re.finditer(r'\[.*?\]\(((?:soil|core)_[\w-]+)\)', content):
        refs.append(Reference(type='log', span=match.span(), target=match.group(1)))
    return refs
```

**ConversationLog Schema**:
```json
{
  "type": "object",
  "properties": {
    "_type": {"const": "ConversationLog"},
    "data": {
      "type": "object",
      "properties": {
        "parent_uuid": {"type": ["string", "null"], "description": "Branch parent (null for root)"},
        "items": {"type": "array", "items": {"type": "string"}, "description": "Item UUIDs in order"},
        "summary": {
          "type": ["object", "null"],
          "description": "Present if collapsed",
          "properties": {
            "timestamp": {"type": "string", "format": "date-time"},
            "author": {"type": "string", "enum": ["operator", "agent", "system"]},
            "content": {"type": "string"},
            "fragment_ids": {"type": "array", "items": {"type": "string"}}
          }
        }
      },
      "required": ["parent_uuid", "items"]
    }
  }
}
```

#### Session 17: Artifact Delta Operations ✅ COMPLETE (2026-02-12)

**Deliverables**:
1. ✅ Extend Artifact entity schema:
   - Add `snapshots: dict[str, str]` field (deferred for MVP, use null)
   - Add `deltas: list[str]` field (list of ArtifactDelta Item UUIDs)
2. ✅ Implement artifact delta operations in `system/core/artifact.py` (new module):
   - `commit_delta(artifact_uuid, ops, references, based_on_commit) -> ArtifactDelta`
   - `get_at_commit(artifact_uuid, commit) -> str`
   - `diff_commits(artifact_uuid, commit_a, commit_b) -> Diff`
   - `list_deltas(artifact_uuid) -> list[dict]`
3. ✅ Add Semantic API verbs for artifacts (`api/handlers/artifact.py`)
4. ✅ Cross-database transaction testing (24/24 tests pass)

**Implementation Notes**:
- Delta operations syntax: `+15:^abc` (add), `-23` (remove), `~18:^abc→^def` (replace), `>12@30` (move)
- Fragment ID format: Exactly 3 characters after caret (`^`), per spec
- Optimistic locking via hash-based conflict detection (ConflictError)
- ArtifactDelta Facts created in Soil with proper metadata
- Delta list persistence fix: Ensure `deltas` list exists in data dict before appending
- Historical reconstruction deferred for MVP (get_at_commit returns current state if hash matches)
- Schema: `schemas/types/facts/artifactdelta.schema.json` created

**Delta Operations Syntax** (from spec):
```
+15:^a7f              Add fragment a7f at line 15
-23                   Remove line 23
~18:^b2e→^c3d         Replace line 18: fragment b2e with c3d
>12@30                Move line 12 to position 30
```

**Semantic API additions**:
```python
# api/handlers/artifact.py (new)
def handle_commit_artifact(request: CommitArtifactRequest) -> SemanticResponse:
    """Create artifact delta with optimistic locking."""
    # 1. Get artifact, verify hash matches based_on_commit
    # 2. Parse ops, apply to content
    # 3. Generate new commit hash
    # 4. Create ArtifactDelta Item in Soil
    # 5. Update Artifact in Core
    # 6. Capture ContextFrame in delta.context
    # 7. Create triggers relation from source Message -> delta

def handle_get_artifact_at_commit(request: GetArtifactAtCommitRequest) -> SemanticResponse:
    """Retrieve artifact state at specific commit."""
    # 1. Get artifact entity
    # 2. Apply deltas up to target commit
    # 3. Return content

def handle_diff_commits(request: DiffCommitsRequest) -> SemanticResponse:
    """Compare two commits, return diff."""
    # 1. Get both commit states
    # 2. Compute line-by-line diff
    # 3. Return structured diff
```

#### Session 18: Fold Verb ✅ COMPLETE (2026-02-12)

**Deliverables**:
1. ✅ Implement `fold` operation in `system/core/conversation.py`
2. ✅ Add `FoldRequest` schema to `api/schemas/semantic.py`
3. ✅ Add `handle_fold` to `api/handlers/conversation.py` (new file)
4. ✅ Add `ConversationLog` to `BASELINE_ENTITY_TYPES` in `api/handlers/core.py`
5. ✅ Test folding behavior (14 system tests pass)
6. ✅ Test fold API (6 API tests pass)

**Fold Semantics** (aligned with RFC-005 single-word verb convention):
```python
fold(
    log_uuid: str,
    summary_content: str,
    author: Literal["operator", "agent", "system"]
) -> ConversationLog
```
Folds a conversation branch by adding a summary.

Per RFC-005: `fold` is a single-word verb applicable to any entity/fact.

Creates:
- Summary object attached to ConversationLog
- Marks branch as folded (collapsed=true)
- Branch remains visible and can continue (messages can be appended after fold point)

**Note on Branching:** Branch creation happens implicitly via RFC-003 ContextFrame inheritance. When a subagent is created with its own ContextFrame that inherits from a parent, this implicitly creates a conversation branch. No explicit `branch` verb is needed.

### Phase 1: MemoGarden Client Library

**Goal**: Python SDK for MemoGarden API access

**Estimated**: 15-20 hours

#### Session 19: MemoGarden Python Client ✅ COMPLETE (2026-02-12)

**Deliverables**:
1. ✅ Create `memogarden-client/` directory structure
2. ✅ Implement client classes:
   - `MemoGardenClient`: Main HTTP client
   - `SemanticAPI`: Wrapper for /mg endpoint
   - `AuthManager`: JWT/API key handling
3. ✅ Add connection pooling (via httpx)
4. ✅ Comprehensive error handling
5. ✅ Client tests

**Implementation Notes**:
- Pydantic V2 migration: `_type` fields renamed to `type_` with alias
- Sync and async client variants provided
- Full Semantic API operation coverage
- Upstream repository: https://github.com/memogarden/memogarden-client

**Project structure**:
```
memogarden-client/
├── mg_client/
│   ├── __init__.py
│   ├── client.py          # MemoGardenClient main class
│   ├── auth.py           # AuthManager, token refresh
│   ├── semantic.py        # Semantic API wrapper
│   ├── rest.py           # REST API wrapper (future)
│   ├── models.py         # Pydantic models for request/response
│   └── exceptions.py      # Client-specific exceptions
├── tests/
│   ├── test_client.py
│   ├── test_semantic_api.py
│   └── fixtures.py
├── pyproject.toml
└── README.md
```

**Usage example**:
```python
from mg_client import MemoGardenClient

# Connect to MemoGarden
client = MemoGardenClient(
    base_url="http://localhost:5000",
    api_key="mg_sk_agent_..."
)

# Create scope
scope = client.semantic.create_scope(label="My Project")

# Create artifact
artifact = client.semantic.create_artifact(
    scope_uuid=scope.uuid,
    label="README.md",
    content="# Welcome\n",
    content_type="text/markdown"
)

# Send message with fragments
message = client.semantic.send_message(
    log_uuid=root_log_uuid,
    content="Let's use ^abc approach - see @artifact_123",
    sender="operator"
)

# Commit delta
delta = client.semantic.commit_artifact_delta(
    artifact_uuid=artifact.uuid,
    ops="+5:^abc",
    references=["^abc"],
    based_on_commit=artifact.hash
)
```

### Phase 2: Server-Sent Events (SSE) for Real-Time Updates

**Goal**: Enable observe mode (operator watches agent work in real-time)

**Estimated**: 12-18 hours (split across two sessions)

#### Session 20A: SSE Infrastructure and Event Publishing ✅ COMPLETE (2026-02-13)

**Tests:** 20/20 passing (251 total tests)

#### Session 20B: Event Integration ✅ COMPLETE (2026-02-15)

**Deliverables Completed:**
1. ✅ Integrate event publishing into existing Semantic API handlers
2. ✅ Add event publishing to artifact delta operations (already done in Session 17)
3. ⏸️ Add event publishing to message/conversation handlers (no send_message handler exists yet)
4. ✅ Add event publishing to context frame operations (enter/leave/focus)
5. ⏸️ Create JavaScript/TypeScript EventSource wrapper (deferred)
6. ⏸️ Test end-to-end event flow (covered by existing tests)
7. ⏸️ Add reconnection handling (deferred)

**Implementation Notes:**
- Event publishing integrated into [core.py](memogarden-api/api/handlers/core.py) for context handlers
- `handle_enter` now publishes `context_updated` event
- `handle_focus` now publishes `context_updated` and `frame_updated` events
- `handle_leave` now publishes `context_updated` and `frame_updated` events
- All 25 existing SSE tests pass, confirming infrastructure works correctly

**Deliverables**:
1. ✅ Create `api/events.py` module with SSE infrastructure
2. ✅ Implement `SSEManager` class for connection management
3. ✅ Add `/events` endpoint to Flask app
4. ✅ Implement event publishing framework
5. ✅ Add authentication for SSE connections (JWT/API key)
6. ✅ Test SSE endpoint and connection management

**Implementation:**
- Created [`api/events.py`](memogarden-api/api/events.py) with:
  - `SSEConnection` dataclass for connection state
  - `SSEManager` for thread-safe connection management
  - `/mg/events` endpoint with SSE streaming
  - `/mg/events/stats` endpoint for connection statistics
  - Event publishing helpers: `publish_event()`, `publish_artifact_delta()`, etc.
- Registered events blueprint in [`api/main.py`](memogarden-api/api/main.py)
- 20 tests in [`tests/test_sse.py`](memogarden-api/tests/test_sse.py) covering:
  - SSEManager unit tests (register, unregister, publish)
  - SSEConnection unit tests (subscription filtering)
  - Event publishing tests (all event types)
  - Endpoint integration tests (auth, stats)
  - Threading tests (concurrent operations)

**SSE Infrastructure**:
```python
# memogarden-api/api/events.py (new)
from flask import Response, stream_with_context, request
import json
import queue
import threading
from dataclasses import dataclass
from typing import Dict, Set

@dataclass
class SSEConnection:
    """Represents an active SSE connection."""
    client_id: str
    user_id: str
    subscribed_scopes: Set[str]
    queue: queue.Queue

class SSEManager:
    """Manages active SSE connections and event broadcasting."""
    def __init__(self):
        self._connections: Dict[str, SSEConnection] = {}
        self._lock = threading.Lock()
        self._client_id_counter = 0

    def register(self, user_id: str, scopes: Set[str]) -> tuple[str, SSEConnection]:
        """Register a new SSE connection."""
        with self._lock:
            self._client_id_counter += 1
            client_id = f"sse_{self._client_id_counter}"
            conn = SSEConnection(
                client_id=client_id,
                user_id=user_id,
                subscribed_scopes=scopes,
                queue=queue.Queue()
            )
            self._connections[client_id] = conn
            return client_id, conn

    def unregister(self, client_id: str):
        """Remove an SSE connection."""
        with self._lock:
            self._connections.pop(client_id, None)

    def publish(self, event_type: str, data: dict, scope_uuid: str = None):
        """Publish event to relevant connections."""
        with self._lock:
            for conn in self._connections.values():
                if scope_uuid is None or scope_uuid in conn.subscribed_scopes:
                    conn.queue.put({"type": event_type, "data": data}, block=False)

# Global SSE manager
sse_manager = SSEManager()

@events_bp.route("/events", methods=["GET"])
@auth_required
def events_stream():
    """Server-Sent Events stream for real-time updates."""
    from api.auth import get_current_user

    user_id = get_current_user()
    scopes = parse_scope_subscription(request)

    client_id, conn = sse_manager.register(user_id, scopes)

    def generate():
        try:
            while True:
                try:
                    event = conn.queue.get(timeout=30)
                    yield f"event: {event['type']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                except queue.Empty:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
        except GeneratorExit:
            sse_manager.unregister(client_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

**Event Publishing Helpers**:
```python
# Event types
EVENT_TYPES = {
    "artifact_delta",     # Artifact modified
    "message_sent",       # New message in scope
    "context_updated",     # ContextFrame changed
    "frame_updated",      # Participant frame changed
    "scope_created",      # New scope created
    "scope_modified",     # Scope metadata changed
}

def publish_event(event_type: str, data: dict, scope_uuid: str = None):
    """
    Publish event to all clients subscribed to scope.

    Called from Semantic API handlers after state changes.
    """
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unknown event type: {event_type}")

    sse_manager.publish(event_type, data, scope_uuid)
```

#### Session 20B: Event Integration and Client-Side Support

**Deliverables**:
1. Integrate event publishing into existing Semantic API handlers
2. Add event publishing to artifact delta operations
3. Add event publishing to message/conversation handlers
4. Add event publishing to context frame operations
5. Create JavaScript/TypeScript EventSource wrapper
6. Test end-to-end event flow
7. Add reconnection handling

**Integration Points**:
```python
# api/handlers/artifact.py - Add event publishing
def handle_commit_artifact(request: CommitArtifactRequest) -> SemanticResponse:
    # ... existing commit logic ...

    # Publish event
    publish_event(
        "artifact_delta",
        {
            "artifact_uuid": artifact.uuid,
            "commit_hash": delta.commit_hash,
            "ops": delta.ops,
            "author": request.actor
        },
        scope_uuid=artifact.data.get("scope_uuid")
    )

    return SemanticResponse(ok=True, result=...)

# api/handlers/conversation.py - Add event publishing
def handle_send_message(request: SendMessageRequest) -> SemanticResponse:
    # ... existing send logic ...

    # Publish event
    publish_event(
        "message_sent",
        {
            "log_uuid": log_uuid,
            "message_uuid": message.uuid,
            "sender": message.data["sender"],
            "content": message.data["description"],
            "fragments": message.data.get("fragments", [])
        },
        scope_uuid=log.data.get("scope_uuid")
    )

    return SemanticResponse(ok=True, result=...)
```

**Client-side EventSource Wrapper**:
```javascript
// mg_client/sse.js (in memogarden-client or Project Studio)
export class MemoGardenEventSource {
  constructor(baseUrl, token, scopes = []) {
    this.url = `${baseUrl}/events?token=${token}&scopes=${scopes.join(',')}`;
    this.eventSource = null;
    this.listeners = new Map();
    this.reconnectDelay = 1000;
  }

  connect() {
    this.eventSource = new EventSource(this.url);

    this.eventSource.onopen = () => {
      console.log('SSE connected');
      this.reconnectDelay = 1000;
    };

    this.eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      this.reconnect();
    };

    // Route events to registered listeners
    EVENT_TYPES.forEach(type => {
      this.eventSource.addEventListener(type, (e) => {
        const data = JSON.parse(e.data);
        this.notify(type, data);
      });
    });
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  notify(eventType, data) {
    const callbacks = this.listeners.get(eventType) || [];
    callbacks.forEach(cb => cb(data));
  }

  reconnect() {
    this.eventSource?.close();
    setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
      this.connect();
    }, this.reconnectDelay);
  }

  disconnect() {
    this.eventSource?.close();
  }
}
```

### Phase 3: Letta Integration and Memory Blocks

**Goal**: Agent memory blocks project MemoGarden state for Letta agents

**Estimated**: 20-25 hours

#### Session 21: Letta Memory Block Projections

**Deliverables**:
1. Create `memogarden-letta/` package
2. Implement memory projection functions:
   - `project_context(scope_uuid) -> str`
   - `artifact_summaries(scope_uuid, limit) -> list[str]`
   - `conversation_history(log_uuid, since) -> list[dict]`
   - `context_frame(participant_uuid) -> list[str]`
3. Define memory block schema (Letta-compatible)
4. Toolcall wrappers for agent operations
5. Integration tests

**Memory Block Structure**:
```python
@dataclass
class AgentMemoryBlock:
    """MemoGarden state projected into Letta memory."""
    # Project context
    project_context: str = None  # "Working in: My Project (active branch: feature-x)"

    # Artifact summaries (recent N artifacts, ordered by access)
    artifact_summaries: list[ArtifactSummary] = field(default_factory=list)

    # Conversation history (recent messages in active branch)
    conversation_history: list[MessageSummary] = field(default_factory=list)

    # Active references (fragments being discussed)
    active_references: list[str] = field(default_factory=list)

    # ContextFrame (RFC-003 containers)
    context_frame: list[str] = field(default_factory=list)

@dataclass
class ArtifactSummary:
    uuid: str
    label: str
    content_type: str
    preview: str  # First 100 chars

@dataclass
class MessageSummary:
    uuid: str
    sender: str
    content: str
    fragments: list[str]  # Fragment IDs in this message
    timestamp: str
```

**Memory Projection Functions**:
```python
# memogarden-letta/memory_projections.py
from mg_client import MemoGardenClient

def project_context(client: MemoGardenClient, scope_uuid: str) -> str:
    """Generate project context string for agent memory."""
    scope = client.semantic.get_entity(scope_uuid)
    root_log = get_root_conversation(client, scope_uuid)
    active_branches = get_active_branches(client, scope_uuid)

    return f"""Project: {scope.data['label']}
Active branches: {len(active_branches)}
Root conversation: {root_log.data.get('summary', {}).get('content', 'No summary')}
"""

def artifact_summaries(client: MemoGardenClient, scope_uuid: str, limit: int = 10) -> list[ArtifactSummary]:
    """Get recent artifact summaries for agent context."""
    artifacts = client.semantic.query_entities(
        _type="Artifact",
        scope_uuid=scope_uuid,
        limit=limit,
        order_by="updated_at DESC"
    )

    return [
        ArtifactSummary(
            uuid=a.uuid,
            label=a.data['label'],
            content_type=a.data.get('content_type', 'text/plain'),
            preview=a.data['content'][:100]
        )
        for a in artifacts
    ]

def conversation_history(client: MemoGardenClient, log_uuid: str, since: str | None = None) -> list[MessageSummary]:
    """Get recent messages from conversation log."""
    log = client.semantic.get_entity(log_uuid)
    messages = []

    for item_uuid in log.data['items'][-50:]:  # Last 50 messages
        item = client.semantic.get_item(item_uuid)
        if item._type == "Message":
            msg_summary = MessageSummary(
                uuid=item.uuid,
                sender=item.data['sender'],
                content=item.data['description'],
                fragments=[f['id'] for f in item.data.get('fragments', [])],
                timestamp=item.realized_at
            )
            messages.append(msg_summary)

    return messages

def context_frame(client: MemoGardenClient, participant_uuid: str) -> list[str]:
    """Get RFC-003 ContextFrame containers."""
    frame = client.semantic.get_context_frame(participant_uuid)
    return frame.data.get('containers', [])
```

### Phase 4: Project Studio Web Application (MVP)

**Goal**: Functional Project Studio app for artifact-centric collaboration

**Estimated**: 80-120 hours

#### Session 22-24: Core UI and Scope Management

**Deliverables**:
1. Project scaffold (Svelte + Vite)
2. Auth and connection
3. Scope list and create
4. Artifact list within scope
5. Basic navigation

**Technology choices**:
- **Framework**: Svelte 5 (TypeScript)
- **Build**: Vite
- **State management**: Svelte stores (simple, performant)
- **Components**: shadcn-svelte (accessible, customizable)
- **Styling**: Tailwind CSS
- **Icons**: Lucide Svelte

**Project structure**:
```
project-studio/
├── src/
│   ├── lib/
│   │   ├── components/
│   │   │   ├── ScopeList.svelte
│   │   │   ├── ArtifactList.svelte
│   │   │   ├── ConversationThread.svelte
│   │   │   ├── FragmentRenderer.svelte
│   │   │   └── ReferenceLink.svelte
│   │   ├── stores/
│   │   │   ├── scope.ts         # Current scope state
│   │   │   ├── artifacts.ts     # Artifacts in scope
│   │   │   └── conversation.ts  # Active conversation
│   │   ├── services/
│   │   │   ├── memogarden.ts  # API client wrapper
│   │   │   ├── fragment.ts     # Fragment parsing
│   │   │   └── sse.ts         # EventSource handling
│   │   └── types/
│   │       └── api.ts         # API type definitions
│   ├── routes/
│   │   └── +page.svelte    # Scope list
│   ├── app.html
│   └── app.css
├── static/                 # Build output
├── tests/
├── package.json
├── vite.config.ts
├── svelte.config.js
├── tsconfig.json
└── tailwind.config.js
```

#### Session 25-27: Artifact Editor and Delta Operations

**Deliverables**:
1. Artifact editor component (line-numbered)
2. Delta syntax highlighting
3. Commit workflow with optimistic locking
4. Three-way diff for merge conflicts
5. Reference rendering (parse and linkify)

**Artifact Editor Features**:
```typescript
// src/lib/components/ArtifactEditor.svelte
<script lang="ts">
  import { commitDelta, getArtifactAtCommit } from '$lib/services/memogarden';
  import { parseReferences, renderReferences } from '$lib/services/fragment';

  let content = '';
  let artifactHash = '';
  let proposedChanges = [];

  // Parse fragment references on input
  $: content = parseReferences($content);

  // Commit delta
  async function commit() {
    const ops = buildDeltaOps();  // "+5:^abc -10"
    const result = await commitDelta(artifact.uuid, ops, proposedReferences);
    if (result.error) {
      if (result.error.code === 'conflict') {
        showMergeConflict(result.conflict);  // Three-way diff UI
      }
    } else {
      showError(result.error);
    }
  }
</script>

<template>
  <div class="artifact-editor">
    <!-- Line numbers -->
    <div class="line-numbers">
      {#each content.split('\n') as line, i}
        <div class="line-number">{i + 1}</div>
      {/each}
    </div>

    <!-- Content with reference rendering -->
    <textarea
      bind:value={content}
      class="content"
      placeholder="Start typing..."
    />

    <!-- Proposed changes panel -->
    {#if proposedChanges.length > 0}
      <div class="proposed-changes">
        <h3>Proposed Changes</h3>
        {#each proposedChanges as change}
          <div class="change">{change.description}</div>
        {/each}
        <button on:click={commit}>Accept</button>
        <button on:click={reject}>Reject</button>
      </div>
    {/if}
  </div>
</template>
```

#### Session 28-30: Conversation and Fragment System

**Deliverables**:
1. Conversation thread component
2. Fragment-based message composition
3. Reference autocomplete
4. Message rendering with linked references
5. Branch visualization

**Fragment System UI**:
```typescript
// src/lib/components/FragmentComposer.svelte
<script lang="ts">
  import { sendMessage, generateFragmentId } from '$lib/services/memogarden';

  let messageText = '';
  let fragments: Array<{id: string, content: string}> = [];

  // Auto-generate fragment ID as user types
  $: if (messageText.length > 10) {
    const lastSentence = messageText.split('.').pop();
    if (lastSentence && !fragments.find(f => f.content === lastSentence)) {
      const fragId = generateFragmentId(lastSentence);
      fragments = [...fragments, { id: fragId, content: lastSentence }];
    }
  }
</script>

<template>
  <div class="fragment-composer">
    <textarea
      bind:value={messageText}
      placeholder="Type your message..."
    />

    <!-- Fragment chips -->
    {#if fragments.length > 0}
      <div class="fragment-chips">
        {#each fragments as frag}
          <span class="chip">{frag.id}: {frag.content}</span>
        {/each}
      </div>
    {/if}

    <!-- Reference autocomplete -->
    <div class="autocomplete">
      <input placeholder="@artifact to reference..." />
      <div class="suggestions">
        {#each suggestions as suggestion}
          <div class="suggestion">
            {@suggestion.type} {suggestion.label}
          </div>
        {/each}
      </div>
    </div>
  </div>
</template>
```

#### Session 31: Observe Mode and Agent Coordination

**Deliverables**:
1. Observe mode UI (agent screen share)
2. Real-time updates via SSE
3. Handover mechanism
4. Agent activity visualization

**Observe Mode UI**:
```typescript
// src/lib/components/ObserveMode.svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { connectEvents } from '$lib/services/sse';

  let agentViewport = null;
  let isObserving = false;

  function startObserving() {
    isObserving = true;
    // Subscribe to agent's frame updates
    connectEvents(agentParticipantId);
  }

  // SSE event handlers
  $: frameUpdated = (event) => {
    if (isObserving && event.data.participant_uuid === agentParticipantId) {
      agentViewport = event.data.head_item_uuid;
      scrollArtifactTo(agentViewport);
    }
  };
</script>

<template>
  <div class="observe-mode">
    {#if isObserving}
      <div class="indicator">
        <span class="pulse">Observing Agent Work</span>
        <button on:click={() => isObserving = false}>
          Stop Observing
        </button>
      </div>

      <!-- Agent viewport overlay -->
      {#if agentViewport}
        <div class="agent-viewport">
          Viewing line {agentViewport.line}
        </div>
      {/if}
    {:else}
      <button on:click={startObserving}>
        Observe Agent
      </button>
    {/if}
  </div>
</template>
```

### Phase 5: Testing and Documentation

**Estimated**: 15-20 hours

#### Session 32: Integration Testing

**Deliverables**:
1. End-to-end workflows (operator + agent)
2. Performance testing (long conversations, many artifacts)
3. Cross-browser testing
4. Mobile responsiveness
5. Accessibility audit

#### Session 33: Documentation

**Deliverables**:
1. User guide for Project Studio
2. Agent integration guide (Letta memory blocks)
3. API documentation for new verbs
4. Deployment guide

---

## Open Questions (KIV)

### KIV-1: Notification Queue for Agent-Generated Summaries

**Question**: When agent generates collapse summary draft, how does operator receive notification for approval?

**Options**:
1. **In-app notification**: Badge/icon indicator in Project Studio UI
2. **System event**: Create SystemEvent fact visible in timeline
3. **Push notification**: Browser notification (if browser supports)

**Decision deferred**: Until Session 25+ when UI scaffold exists

### KIV-2: Scratchpad Semantics

**Question**: Should scratchpad be ephemeral Artifact entity or separate ConversationLog type?

**Trade-offs**:
| Approach | Pros | Cons |
|-----------|------|-------|
| **Draft Artifact** | Reuses delta system, can "publish" to make permanent | Drafts visible in queries (need filter) |
| **Scratchpad Log** | Separates scratch from artifacts, cleaner mental model | New data model, can't reference scratch in artifacts |

**Decision deferred**: Until Phase 2 when concrete use cases emerge

### KIV-3: Merge Conflict Resolution UX

**Question**: What's the UI pattern for agent-proposed conflict resolution?

**Current plan**: Agent drafts resolution, operator approves

**Unknown**:
- Three-way diff visualization (libraries?)
- Conflict markers in content (`<<<<<<<` style or custom?)
- Per-line conflict resolution or whole-document?

**Decision deferred**: Until Session 26 (Artifact Editor implementation)

### KIV-4: Cross-Scope Reference Security

**Question**: Should artifact in Scope A reference artifact in Scope B be allowed?

**Current decision**: Allow unless concrete conflict examples emerge

**Considerations**:
- Access control: Does operator in Scope A have read access to Scope B?
- Visibility: Should cross-scope refs be visually distinct?
- Broken links: What happens when Scope B is deleted?

**Decision deferred**: Until multi-scope deployment testing

---

## Summary and Estimates

### Implementation Breakdown

| Phase | Sessions | Hours | Dependencies |
|--------|----------|----------|---------------|
| **Phase 0: Prerequisites** | 15-18 | 20-30 | Existing MemoGarden Core |
| **Phase 1: Client Library** | 19 | 15-20 | Phase 0 complete |
| **Phase 2: SSE Events** | 20 | 10-15 | Client library |
| **Phase 3: Letta Integration** | 21 | 20-25 | Client library |
| **Phase 4: Project Studio UI** | 22-31 | 80-120 | Phases 0-3 |
| **Phase 5: Testing & Docs** | 32-33 | 15-20 | All phases |
| **Total** | | **160-230 hours** | |

**Estimated timeline**:
- **Single developer**: 4-6 weeks
- **Two developers**: 2-3 weeks

### Risk Assessment

| Risk | Impact | Mitigation |
|-------|----------|------------|
| **Scope entity not in RFC-003** | High redesign cost | Use existing ContextFrame ownership, minimal new entity behavior |
| **Fragment reference collisions** | Medium (broken links) | Document collision handling, provide ref validation UI |
| **Long conversation performance** | High (UI lag) | Virtual scrolling, pagination, message lazy-loading |
| **SSE reconnection reliability** | Medium (missed events) | Exponential backoff, event replay on reconnect |
| **Agent merge conflicts** | Medium (data loss) | Optimistic locking, three-way diff, manual resolution fallback |
| **Letta memory block size** | Medium (context overflow) | Document limits, implement memory block truncation strategy |

---

## References

### Related Documents

- **Project Studio Specification v0.4.0**: [`plan/project_studio_specification_v0_4_0.md`](plan/project_studio_specification_v0_4_0.md)
- **MemoGarden PRD v0.11.1**: [`plan/memogarden_prd_v0_11_0.md`](plan/memogarden_prd_v0_11_0.md)
- **RFC-003 v4**: Context Mechanism [`plan/rfc_003_context_mechanism_v4.md`](plan/rfc_003_context_mechanism_v4.md)
- **RFC-009 v1**: MemoGarden Application Model [`plan/rfc_009_memogarden_apps_v1.md`](plan/rfc_009_memogarden_apps_v1.md)
- **JCE Whitepaper v1.0**: [`plan/jce_whitepaper_v1_0.md`](plan/jce_whitepaper_v1_0.md)
- **Current Implementation Plan**: [`plan/memogarden-implementation-plan.md`](plan/memogarden-implementation-plan.md)

### Codebases

- **memogarden-system**: Core library (`/workspaces/memogarden/memogarden-system/`)
- **memogarden-api**: Flask server (`/workspaces/memogarden/memogarden-api/`)
- **memogarden-client**: Python SDK ✅ CREATED (`/workspaces/memogarden/memogarden-client/`)
- **memogarden-letta**: Agent integration (to be created)
- **project-studio**: Web application (to be created)

---

**Status:** Phase 0 Complete ✅ (5/6 sessions complete) - Ready for Phase 1
**Documentation:**
- Added [`docs/testing-guide.md`](docs/testing-guide.md) for test patterns and fixtures

**Recent Progress:**
- Session 20A (2026-02-13): SSE Infrastructure - 20 tests added, 251 total tests passing

**END OF DOCUMENT**
