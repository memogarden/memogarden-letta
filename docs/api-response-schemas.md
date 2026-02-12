# MemoGarden API Response Schemas

**Version:** 1.0
**Created:** 2026-02-12
**For:** Python Client Library (Session 19)

This document defines all response formats from the MemoGarden Semantic API (`/mg` endpoint). All responses follow the standard envelope format defined in RFC-005 v7.

---

## Response Envelope

All Semantic API responses use a consistent envelope format:

```json
{
  "ok": true,
  "actor": "usr_550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": { ... },
  "error": null
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|-------|-------------|
| `ok` | boolean | `true` if operation succeeded, `false` if failed |
| `actor` | string | UUID of authenticated user/agent performing the operation |
| `timestamp` | string | ISO 8601 timestamp of response |
| `result` | object/null | Operation-specific result payload (present on success) |
| `error` | object/null | Error details (present on failure) |

---

## Error Response Format

When `ok: false`, the `error` field contains structured error information:

```json
{
  "ok": false,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": null,
  "error": {
    "type": "ResourceNotFound",
    "message": "Entity not found",
    "details": { "uuid": "core_abc123" }
  }
}
```

**Error Types:**

| Type | HTTP Status | Description |
|------|-------------|-------------|
| `ValidationError` | 400 | Request validation failed (see details for field errors) |
| `AuthenticationError` | 401 | Invalid or missing credentials |
| `ResourceNotFound` | 404 | Entity/fact/relation not found |
| `ConflictError` | 409 | Optimistic locking conflict (e.g., artifact commit) |
| `InternalServerError` | 500 | Unexpected server error |

---

## Operation Response Schemas

### Core Bundle

#### create

Creates a new entity.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "core_550e8400-e29b-41d4-a716-446655440000",
    "_type": "Transaction",
    "data": { ... },
    "created_at": "2026-02-12T10:30:00Z",
    "updated_at": "2026-02-12T10:30:00Z"
  }
}
```

#### get

Retrieves an entity by UUID.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "core_xxx",
    "_type": "Transaction",
    "data": { ... },
    "created_at": "2026-02-12T10:30:00Z",
    "updated_at": "2026-02-12T10:30:00Z"
  }
}
```

#### get_conversation

Retrieves a ConversationLog entity (Project Studio).

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "core_xxx",
    "_type": "ConversationLog",
    "data": {
      "parent_uuid": null,
      "items": ["soil_msg1", "soil_msg2", ...],
      "summary": null
    },
    "created_at": "2026-02-12T10:30:00Z",
    "updated_at": "2026-02-12T10:30:00Z"
  }
}
```

#### edit

Modifies an entity using set/unset semantics.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "core_xxx",
    "_type": "Transaction",
    "data": { ... },
    "created_at": "2026-02-12T10:00:00Z",
    "updated_at": "2026-02-12T10:30:00Z"
  }
}
```

#### forget

Soft deletes an entity.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "core_xxx",
    "forgotten_at": "2026-02-12T10:30:00Z"
  }
}
```

#### query

Queries entities with filters.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "results": [
      {
        "uuid": "core_xxx",
        "_type": "Transaction",
        "data": { ... },
        "created_at": "2026-02-12T10:00:00Z",
        "updated_at": "2026-02-12T10:30:00Z"
      }
    ],
    "total": 42,
    "start_index": 0,
    "count": 20
  }
}
```

---

### Soil Bundle

#### add

Adds a new fact (Item) to Soil.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "soil_550e8400-e29b-41d4-a716-446655440000",
    "_type": "Message",
    "data": {
      "description": "Message content",
      "fragments": []
    },
    "realized_at": "2026-02-12T10:30:00Z",
    "canonical_at": "2026-02-12T10:30:00Z"
  }
}
```

#### amend

Amends a fact (creates superseding fact).

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "soil_xxx",
    "_type": "Message",
    "data": { ... },
    "realized_at": "2026-02-12T10:30:00Z",
    "canonical_at": "2026-02-12T10:30:00Z",
    "supersedes": "soil_yyy"
  }
}
```

#### get_fact

Retrieves a fact (Item) by UUID.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "soil_xxx",
    "_type": "Message",
    "data": { ... },
    "realized_at": "2026-02-12T10:30:00Z",
    "canonical_at": "2026-02-12T10:30:00Z"
  }
}
```

#### query_facts

Queries facts with filters.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "results": [
      {
        "uuid": "soil_xxx",
        "_type": "Message",
        "data": { ... },
        "realized_at": "2026-02-12T10:00:00Z",
        "canonical_at": "2026-02-12T10:00:00Z"
      }
    ],
    "total": 100,
    "start_index": 0,
    "count": 20
  }
}
```

---

### Relations Bundle

#### link

Creates a user relation.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "rel_550e8400-e29b-41d4-a716-446655440000",
    "kind": "explicit_link",
    "source": "core_src",
    "source_type": "entity",
    "target": "core_tgt",
    "target_type": "entity",
    "created_at": "2026-02-12T10:30:00Z",
    "time_horizon": "2026-02-19T10:30:00Z",
    "is_alive": true
  }
}
```

#### unlink

Removes a user relation.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "message": "Relation unlinked successfully",
    "uuid": "rel_xxx"
  }
}
```

#### edit_relation

Modifies a relation.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "rel_xxx",
    "kind": "explicit_link",
    "source": "core_src",
    "source_type": "entity",
    "target": "core_tgt",
    "target_type": "entity",
    "created_at": "2026-02-12T10:00:00Z",
    "time_horizon": "2026-02-26T10:30:00Z",
    "is_alive": true
  }
}
```

#### get_relation

Retrieves a relation by UUID.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "uuid": "rel_xxx",
    "kind": "explicit_link",
    "source": "core_src",
    "source_type": "entity",
    "target": "core_tgt",
    "target_type": "entity",
    "created_at": "2026-02-12T10:00:00Z",
    "time_horizon": "2026-02-19T10:30:00Z",
    "is_alive": true
  }
}
```

#### query_relation

Queries relations with filters.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "results": [
      {
        "uuid": "rel_xxx",
        "kind": "explicit_link",
        "source": "core_src",
        "source_type": "entity",
        "target": "core_tgt",
        "target_type": "entity",
        "created_at": "2026-02-12T10:00:00Z",
        "time_horizon": "2026-02-19T10:30:00Z",
        "is_alive": true
      }
    ],
    "total": 5,
    "start_index": 0,
    "count": 5
  }
}
```

#### explore

Explores the relation graph from an anchor.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "nodes": [
      { "uuid": "core_a", "kind": "entity", "distance": 0 },
      { "uuid": "core_b", "kind": "entity", "distance": 1 }
    ],
    "edges": [
      {
        "uuid": "rel_xxx",
        "source": "core_a",
        "target": "core_b",
        "kind": "explicit_link"
      }
    ]
  }
}
```

---

### Context Bundle (RFC-003)

#### enter

Enters a scope (adds to active set).

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "scope": "core_xxx",
    "active_scopes": ["core_xxx", "core_yyy"],
    "primary_scope": "core_xxx"
  }
}
```

#### leave

Leaves a scope (removes from active set).

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "scope": "core_xxx",
    "active_scopes": ["core_yyy"],
    "primary_scope": "core_yyy"
  }
}
```

#### focus

Focuses a scope (sets as primary).

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "scope": "core_xxx",
    "active_scopes": ["core_xxx", "core_yyy"],
    "primary_scope": "core_xxx"
  }
}
```

---

### Track Verb

#### track

Traces causal chain from entity back to originating facts.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "entity": {
      "uuid": "core_xxx",
      "_type": "Transaction",
      "sources": [
        {
          "kind": "fact",
          "uuid": "soil_xxx",
          "_type": "Message",
          "sources": []
        }
      ]
    }
  }
}
```

---

### Search Verb

#### search

Performs fuzzy text search.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "results": [
      {
        "uuid": "core_xxx",
        "_type": "Transaction",
        "score": 0.95,
        "match_type": "content",
        "data": { ... }
      }
    ],
    "total": 10,
    "continuation_token": "abc123..."
  }
}
```

---

### Artifact Delta Bundle (Project Studio)

#### commit_artifact

Commits artifact delta with optimistic locking.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "artifact_uuid": "core_xxx",
    "commit_hash": "a1b2c3d4",
    "previous_hash": "9f8e7d6c",
    "delta_uuid": "soil_xxx",
    "content": "Updated artifact content...",
    "applied_ops": ["+5:^abc", "-10"]
  }
}
```

**Error Response (Conflict):**

```json
{
  "ok": false,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": null,
  "error": {
    "type": "ConflictError",
    "message": "Artifact was modified by another user",
    "details": {
      "expected_hash": "9f8e7d6c",
      "actual_hash": "a1b2c3d4",
      "artifact_uuid": "core_xxx"
    }
  }
}
```

#### get_artifact_at_commit

Retrieves artifact state at specific commit.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "artifact_uuid": "core_xxx",
    "commit_hash": "a1b2c3d4",
    "content": "Artifact content at commit...",
    "is_current": true
  }
}
```

#### diff_commits

Compares two commits with line-by-line diff.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "artifact_uuid": "core_xxx",
    "commit_a": "a1b2c3d4",
    "commit_b": "9f8e7d6c",
    "diff": [
      { "type": "add", "line": 5, "content": "^abc" },
      { "type": "remove", "line": 10, "content": "old line" },
      { "type": "replace", "line": 15, "old": "^def", "new": "^ghi" }
    ]
  }
}
```

---

### Conversation Bundle (Project Studio)

#### fold

Folds a conversation branch with summary.

```json
{
  "ok": true,
  "actor": "usr_xxx",
  "timestamp": "2026-02-12T10:30:00Z",
  "result": {
    "log_uuid": "core_xxx",
    "summary": {
      "timestamp": "2026-02-12T10:30:00Z",
      "author": "operator",
      "content": "Summary of conversation branch...",
      "fragment_ids": ["^abc", "^def"]
    },
    "collapsed": true
  }
}
```

---

## Authentication Endpoints

### POST /auth/login

Authenticates user and returns JWT token.

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "usr_550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "is_admin": true,
    "created_at": "2026-02-12T10:00:00Z"
  }
}
```

### POST /auth/logout

Logout endpoint (no-op for stateless JWT).

**Response:**

```json
{
  "message": "Logged out successfully"
}
```

### GET /auth/me

Get current user info from JWT token.

**Response:**

```json
{
  "id": "usr_550e8400-e29b-41d4-a716-446655440000",
  "username": "admin",
  "is_admin": true,
  "created_at": "2026-02-12T10:00:00Z"
}
```

### GET /api-keys/

List all API keys for authenticated user.

**Response:**

```json
[
  {
    "id": "key_xxx",
    "name": "claude-code",
    "prefix": "mg_sk_agent_",
    "expires_at": null,
    "created_at": "2026-02-12T10:00:00Z",
    "last_seen": "2026-02-12T15:45:00Z",
    "revoked_at": null
  }
]
```

### POST /api-keys/

Create a new API key (full key only shown once).

**Response:**

```json
{
  "id": "key_xxx",
  "name": "my-app",
  "key": "mg_sk_agent_9a2b8c7d...",  // Only shown once!
  "prefix": "mg_sk_agent_",
  "expires_at": "2026-12-31T23:59:59Z",
  "created_at": "2026-02-12T10:00:00Z",
  "last_seen": null,
  "revoked_at": null
}
```

### DELETE /api-keys/<key_id>

Revoke an API key.

**Response:**

```json
{
  "message": "API key revoked successfully"
}
```

---

## Common Field Types

### UUID Format

All UUIDs use a prefix to indicate their layer:

| Prefix | Layer | Example |
|--------|-------|---------|
| `core_` | Core entities | `core_550e8400-...` |
| `soil_` | Soil facts (Items) | `soil_550e8400-...` |
| `rel_` | Relations | `rel_550e8400-...` |
| `usr_` | Users | `usr_550e8400-...` |
| `agt_` | Agents | `agt_550e8400-...` |

**Note:** API operations accept UUIDs with or without prefix. The prefix is automatically detected.

### Timestamp Format

All timestamps use ISO 8601 format: `2026-02-12T10:30:00Z`

### Entity Type Names

Baseline entity types include:
- `Transaction` - Financial transactions
- `Recurrence` - Recurring transaction patterns
- `Contact` - Contact information
- `Account` - Financial accounts
- `Artifact` - Project Studio artifacts
- `Scope` - Project Studio scopes (RFC-003)
- `ConversationLog` - Project Studio conversations

### Fact Type Names (Items)

Baseline fact types include:
- `Message` - Conversation messages
- `Email` - Imported emails
- `Note` - User notes
- `ToolCall` - Agent tool invocations
- `ArtifactDelta` - Artifact change records

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (login, API key creation) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing credentials) |
| 404 | Not Found (entity/fact doesn't exist) |
| 409 | Conflict (optimistic locking) |
| 500 | Internal Server Error |

---

**END OF DOCUMENT**
