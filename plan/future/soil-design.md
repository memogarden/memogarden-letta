# Memogarden Soil Design

> **Status:** Future Design Work
> **Last Updated:** 2025-12-24
> **Related Documents:** [schema-extension-design.md](./schema-extension-design.md) | [migration-mechanism.md](./migration-mechanism.md)

---

## Overview

### What is Memogarden Soil?

**Memogarden Soil** is the **immutable append-only storage layer** for MemoGarden. It serves as the long-term memory and archival system for:
- Schema snapshots
- Extension migrations
- Entity deltas (change history)
- Documents (emails, PDFs, statements)
- Archived extensions

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Archive** | Store document in Soil (read-only, append-only) |
| **Fossilize** | Lossy compaction of long-unused archived documents (future mechanism) |
| **TTF** | Time to Fossilization (undetermined, future design work) |
| **Fossil** | Compacted document in Soil (lossy, may not allow full reconstruction) |

### Design Principles

1. **Append-only** - Documents are never mutated, only added
2. **Read-only** - Once archived, documents cannot be modified
3. **Immutable** - Archived content never changes (new versions = new documents)
4. **Retrievable** - Historical states can be reconstructed
5. **Lossy over time** - Fossils may compact data to reduce storage (future)

---

## Directory Structure

```
memogarden-soil/
│
├── core-migration/              # Schema and extension history
│   ├── snapshots/               # Full schema snapshots
│   │   ├── 20251223-initial-schema.sql
│   │   ├── 20250411-add-tags.sql
│   │   ├── 20250415-add-workflows.sql
│   │   └── ...
│   │
│   ├── extensions/              # Archived extensions
│   │   ├── 20250411/
│   │   │   ├── extension.sql
│   │   │   ├── extension.schema.json
│   │   │   └── extension.notes.md (optional)
│   │   ├── 20250415/
│   │   │   ├── extension.sql
│   │   │   ├── extension.schema.json
│   │   │   └── extension.notes.md
│   │   ├── 20250420/
│   │   └── fossilized/          # Compacted extensions (future)
│   │       ├── 20250408/
│   │       │   └── summary.json  # Lossy summary
│   │       └── 20250411/
│   │           └── summary.json
│   │
│   └── migrations/              # Migration scripts
│       ├── 20250411-to-20250415/
│       │   ├── migrate.sql
│       │   ├── transform.py (optional)
│       │   └── rollback.sql (optional)
│       ├── 20250415-to-20250420/
│       └── 20250420-to-20250425/
│
├── core-delta/                  # Entity change history
│   └── YYYYMMDD/
│       └── {entity_id}/
│           └── {delta_id}.json
│
├── documents/                   # Mutable docs with ongoing changes
│   ├── user-manual.md
│   ├── api-reference.md
│   └── ...
│
├── artifacts/                   # Immutable objects
│   ├── emails/
│   │   └── {message_id}.eml
│   ├── pdfs/
│   │   └── {document_id}.pdf
│   ├── statements/
│   │   └── {statement_id}.pdf
│   └── images/
│       └── {image_id}.png
│
└── fossils/                     # Compacted/archived artifacts (future)
    ├── emails/
    │   └── compacted/
    │       └── 2025-01-emails-summary.json  # Lossy summary
    ├── pdfs/
    │   └── thumbnails/
    │       └── {document_id}-thumb.png
    └── statements/
        └── aggregated/
            └── 2025-01-statement-summary.json
```

### Directory Purposes

| Directory | Purpose | Mutable? |
|-----------|---------|----------|
| `core-migration/snapshots/` | Full schema snapshots | No (append-only) |
| `core-migration/extensions/` | Archived extensions | No (append-only) |
| `core-migration/migrations/` | Migration scripts | No (append-only) |
| `core-delta/` | Entity change history | No (append-only) |
| `documents/` | Ongoing documentation | Yes (mutable) |
| `artifacts/` | Immutable source documents | No (append-only) |
| `fossils/` | Compacted artifacts | No (append-only) |

---

## Archiving Workflow

### When Extension Becomes Inactive

**Trigger:** User/agent switches to a new extension (migration occurs).

**Steps:**

1. **Copy extension files** to Soil
   ```bash
   cp memogarden-core/schema/extension.sql \
      memogarden-soil/core-migration/extensions/{date}/extension.sql

   cp memogarden-core/schema/extension.schema.json \
      memogarden-soil/core-migration/extensions/{date}/extension.schema.json
   ```

2. **Create full schema snapshot**
   ```bash
   # Dump entire database schema (base schema + active extension)
   sqlite3 data/memogarden.db .schema > \
      memogarden-soil/core-migration/snapshots/{date}.sql
   ```

3. **Update `_schema_metadata`** to track archival
   ```sql
   INSERT INTO _schema_metadata (key, value, updated_at)
   VALUES ('archived_extensions', json_append(
       (SELECT value FROM _schema_metadata WHERE key = 'archived_extensions'),
       '20250411'
   ), datetime('now'));
   ```

4. **(Future) After TTF expires**, fossilize (see [Fossilization](#fossilization))

### Archival During Migration

See [migration-mechanism.md](./migration-mechanism.md) for complete migration workflow.

**Summary:**
1. Export current extension data
2. Apply new extension
3. Archive old extension to Soil
4. Update metadata

---

## Fossilization (Future)

### Definition

**Fossilization** is the **lossy compaction** of archived documents that haven't been referenced in a long time.

**Purpose:** Reduce storage requirements while preserving essential information.

### Time to Fossilization (TTF)

**Definition:** How long a document must be unused before fossilization.

**Status:** **Undetermined (future design work)**

**Factors to consider:**
- Document type (schemas vs. emails vs. deltas)
- Access frequency (hot vs. cold data)
- Storage cost vs. reconstruction value
- User preferences (keep everything vs. aggressive compaction)

**Possible approaches:**
- Fixed time (e.g., 1 year of non-use)
- Storage threshold (fossilize when disk > 90% full)
- Machine learning (predict which documents won't be needed)
- Manual trigger (user explicitly requests fossilization)

### Examples of Lossy Compaction

#### Schema Snapshots

**Original:** `snapshots/20250411-add-tags.sql` (500 lines)
```sql
-- Full DDL for all tables
CREATE TABLE entity (...);
CREATE TABLE transactions (...);
CREATE TABLE tags (...);
-- ... hundreds of lines ...
```

**Fossil:** `fossilized/20250411/summary.json` (20 lines)
```json
{
    "schema_version": "memogarden-core-v1+20250411",
    "date": "2025-04-11",
    "summary": "Added tags table with hierarchy support",
    "tables_added": ["tags", "entity_tags"],
    "key_columns": {
        "tags": ["id", "name", "parent_id", "color"],
        "entity_tags": ["entity_id", "tag_id"]
    },
    "previous_schema": "memogarden-core-v1+20250408",
    "next_schema": "memogarden-core-v1+20250415"
}
```

**Loss:** Full DDL removed, only structural summary retained.

**Recovery:** Can reconstruct approximate schema (but not exact DDL).

---

#### Entity Deltas

**Original:** `core-delta/20250411/txn-abc/delta-001.json`
```json
{
    "entity_id": "txn-abc",
    "delta_id": "delta-001",
    "field": "amount",
    "old_value": 100.0,
    "new_value": 150.0,
    "timestamp": "2025-04-11T10:30:00Z",
    "author": "user-1",
    "rationale": "Corrected amount from receipt"
}
```

**Fossil:** `fossils/deltas/2025-04/txn-abc-summary.json`
```json
{
    "entity_id": "txn-abc",
    "period": "2025-04",
    "change_count": 15,
    "fields_modified": ["amount", "description", "category"],
    "final_state": {
        "amount": 150.0,
        "description": "Coffee at Starbucks",
        "category": "Food"
    }
}
```

**Loss:** Individual deltas merged into summary, intermediate states lost.

**Recovery:** Can see final state, but not full change history.

---

#### Emails

**Original:** `artifacts/emails/msg-123.eml` (50 KB)
```email
From: merchant@example.com
To: user@example.com
Subject: Receipt #12345
Date: Mon, 11 Apr 2025 10:30:00 +0000
Message-ID: <msg-123@example.com>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset=utf-8

Thank you for your purchase...
[Full email body]

--boundary123
Content-Type: application/pdf
Content-Transfer-Encoding: base64

JVBERi0xLjQKJeLjz9MK... (PDF attachment)
```

**Fossil:** `fossils/emails/compacted/2025-04/msg-123-summary.json` (2 KB)
```json
{
    "message_id": "msg-123@example.com",
    "date": "2025-04-11T10:30:00Z",
    "from": "merchant@example.com",
    "subject": "Receipt #12345",
    "extracted_data": {
        "amount": 15.50,
        "merchant": "Starbucks",
        "transaction_date": "2025-04-11"
    },
    "attachments_count": 1,
    "has_pdf": true
}
```

**Loss:** Full email body removed, attachments discarded, only metadata retained.

**Recovery:** Can see transaction details, but not full email content.

---

### Fossilization Process

**Proposed workflow (future):**

```python
def fossilize_document(doc_path: str, doc_type: str):
    """
    Fossilize a document (lossy compaction).

    Args:
        doc_path: Path to document in Soil
        doc_type: Type of document (schema, delta, email, etc.)
    """
    # Check TTF (Time to Fossilization)
    if not is_fossilization_ready(doc_path):
        return

    # Determine compaction strategy based on doc_type
    strategy = get_compaction_strategy(doc_type)

    # Extract key information (lossy)
    summary = strategy.extract_summary(doc_path)

    # Write fossil to fossils/ directory
    fossil_path = get_fossil_path(doc_path)
    write_fossil(fossil_path, summary)

    # Verify fossil was written successfully
    if verify_fossil(fossil_path, summary):
        # Delete original (or move to cold storage)
        delete_or_archive(doc_path)

        # Update fossilization log
        log_fossilization(doc_path, fossil_path)
```

### Recovery from Fossils

**Lossy recovery:**
- Fossils provide summaries, not full reconstruction
- Some information permanently lost
- Trade-off: storage efficiency vs. data fidelity

**Example recovery:**
```python
# Query: "What did the schema look like on 2025-04-11?"
fossil = read_fossil("fossils/extensions/20250411/summary.json")

# Result: Approximate schema structure (but not exact DDL)
print(fossil)
{
    "tables_added": ["tags", "entity_tags"],
    "key_columns": {...}
    # Can reconstruct structure, but not exact CREATE TABLE statements
}
```

---

## Retrieval and Reconstruction

### Purpose

Enable **historical analysis and data archaeology**:
- "What did the schema look like on date X?"
- "Reconstruct entity Y as of date Z"
- "Show all changes to entity between dates A and B"
- "Which extension was active on date X?"

### Reconstruction Mechanism

**Combine sources:**
1. **Base schema** (`schema.sql`)
2. **Extension snapshots** (`core-migration/snapshots/`)
3. **Entity deltas** (`core-delta/`)
4. **Current database** (for latest state)

### Example: Reconstruct Historical Schema

**Query:** "What was the full schema on 2025-04-15?"

```python
def reconstruct_schema(as_of_date: str) -> str:
    """
    Reconstruct full schema as of a given date.

    Args:
        as_of_date: Date string (YYYY-MM-DD)

    Returns:
        Full DDL for schema as of that date
    """
    # 1. Find base schema version
    base_schema = get_base_schema_as_of(as_of_date)

    # 2. Find extension active on that date
    extension = get_extension_as_of(as_of_date)

    # 3. Combine base + extension
    snapshot_path = f"soil/core-migration/snapshots/{extension['date']}.sql"
    full_schema = read_file(snapshot_path)

    return full_schema
```

### Example: Reconstruct Entity History

**Query:** "Show transaction 'abc-123' as it evolved over time"

```python
def reconstruct_entity_history(entity_id: str) -> list[dict]:
    """
    Reconstruct full history of an entity.

    Args:
        entity_id: Entity UUID

    Returns:
        List of historical states (chronological)
    """
    # 1. Get current entity state
    current_state = get_entity(entity_id)

    # 2. Get all deltas for this entity
    deltas = get_entity_deltas(entity_id)

    # 3. Replay deltas backwards to reconstruct historical states
    history = []
    state = current_state

    for delta in reversed(deltas):
        history.append({
            'timestamp': delta['timestamp'],
            'state': state.copy()
        })
        # Apply reverse delta
        state = apply_reverse_delta(state, delta)

    # Return chronological history
    return list(reversed(history))
```

---

## Access Patterns

### Reading from Soil

**Soil is read-only** (except for the `documents/` directory).

**Access methods:**
- **Direct file access** (for local deployments)
- **S3-compatible API** (for cloud storage)
- **FUSE filesystem** (mount Soil as directory)

### Writing to Soil

**Append-only:**
- New documents added (never overwrite existing)
- New versions = new documents (with timestamps)
- File names include identifiers (UUIDs, dates, etc.)

**Example:**
```python
# Archiving a new extension
archive_path = f"soil/core-migration/extensions/{date}/extension.sql"
write_file(archive_path, extension_sql)
# File written once, never modified
```

---

## Storage Considerations

### Append-Only Growth

**Problem:** Soil grows indefinitely (append-only).

**Mitigations:**
1. **Fossilization** (future) - Lossy compaction
2. **Manual archival** - Move cold data to external storage
3. **Compression** - Compress old files
4. **Retention policies** - Delete documents older than X years (user preference)

### Storage Backends

**Supported:**
- **Local filesystem** (default, simple)
- **S3-compatible** (AWS S3, MinIO, etc.)
- **SFTP/SSH** (remote server)
- **FUSE mounting** (custom filesystem)

**Configuration:**
```toml
# config.toml
[soil]
backend = "local"  # or "s3", "sftp", "fuse"
path = "/path/to/memogarden-soil"

[soil.s3]
bucket = "memogarden-soil"
region = "us-east-1"
access_key = "${AWS_ACCESS_KEY_ID}"
secret_key = "${AWS_SECRET_ACCESS_KEY}"
```

---

## Future Work

### Undetermined Design Questions

| Question | Status | Priority |
|----------|--------|----------|
| **TTF (Time to Fossilization)** | Undetermined | Medium |
| **Fossilization triggers** | Undetermined | Medium |
| **Compaction strategies** | Partially defined | Low |
| **Reconstruction APIs** | Undetermined | Low |
| **Storage backends** | Defined (local, S3) | Low |
| **Retention policies** | Undetermined | Low |
| **Automated archival** | Not implemented | Low |

### Implementation Phases

**Phase 1:** Basic archival (current design)
- Copy extensions to Soil
- Create schema snapshots
- Manual fossilization (user-triggered)

**Phase 2:** Automated archival
- Auto-archive extensions on migration
- Auto-create schema snapshots
- Track access patterns for TTF

**Phase 3:** Fossilization (future)
- Implement TTF mechanism
- Automatic fossilization triggers
- Compaction strategies
- Recovery APIs

---

## Summary

| Aspect | Specification |
|--------|---------------|
| **Purpose** | Immutable append-only storage for MemoGarden |
| **Key concepts** | Archive (store), Fossilize (lossy compact), TTF (time to fossilize) |
| **Directories** | core-migration/, core-delta/, documents/, artifacts/, fossils/ |
| **Archival workflow** | Copy files → Create snapshot → Update metadata |
| **Fossilization** | Lossy compaction (future, TTF undetermined) |
| **Reconstruction** | Combine base schema + snapshots + deltas |
| **Access patterns** | Read-only (except documents/) |
| **Storage backends** | Local, S3, SFTP, FUSE |
| **Append-only growth** | Mitigated by fossilization (future) |

---

**Related Documents:**
- [schema-extension-design.md](./schema-extension-design.md) - Extension system architecture
- [migration-mechanism.md](./migration-mechanism.md) - Migration workflow
- [../prd.md](../prd.md) - Product Requirements Document
