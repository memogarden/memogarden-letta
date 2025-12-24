# Schema Extension Design

> **Status:** Future Design Work
> **Last Updated:** 2025-12-24
> **Related Documents:** [migration-mechanism.md](./migration-mechanism.md) | [soil-design.md](./soil-design.md)

---

## Overview

MemoGarden uses a **two-tier schema system**:

1. **Base Schema** - Stable, public, versioned core data model
2. **Extensions** - Personal, experimental, customizable additions

### Philosophy

- **Base schema is published and immutable** (except version bumps)
- **Extensions are personal and idiosyncratic** (no two systems need share the same extension)
- **Single active extension** at any point in time
- **Two extension mechanisms:** Structured (SQL tables) + JSON (flexible data)
- **Forward compatibility required** - newer extensions must not break older systems
- **Backward compatibility not required** - upgraded systems may reject old entities

### Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Predictability** | Extensions cannot ALTER existing base tables (new tables only) |
| **Simplicity** | One extension active at a time, no dependency graphs |
| **Personalization** | Extensions are experimental and expected to evolve |
| **Interpretability** | Extensions can be shared for understanding, not compatibility |
| **Archival** | All extension history preserved in Memogarden Soil |

---

## File Structure

```
memogarden-core/memogarden_core/schema/
├── schema.sql                    # Base schema (immutable except version bumps)
├── extension.sql                 # Active structured extension
└── extension.schema.json         # JSON schema for extension.data column
```

**Notes:**
- Only **one active extension** at a time (`extension.sql` and `extension.schema.json`)
- No dated folders (e.g., `extensions/20250411/`) - extension version is in the files
- Archived extensions stored in **memogarden-soil** (see [soil-design.md](./soil-design.md))

---

## Base Schema

### Definition

The base schema is the **published, non-customizable core** of MemoGarden.

### Versioning

**Format:** Semantic versioning (`v1.0`, `v1.1`, `v2.0`)

- **v1.0 → v1.1** (Clarification/Refinement)
  - Adds precision to existing specifications
  - Documents implicit assumptions
  - Adds compatible constraints
  - Does NOT require data migration
  - Backward compatible

- **v1 → v2** (Breaking Change)
  - Adds/removes tables or columns
  - Changes field types
  - Requires data migration
  - NOT backward compatible

### Base Schema Contents

**Includes:**
- Core tables (entity registry, transactions, recurrences, relations, deltas)
- Core indexes (foreign keys, PRD-defined query patterns)
- `extension` table (first-class, not an "add-on")
- `_schema_metadata` table (version tracking)
- `_extension_metadata` table (extension metadata)

**Excludes:**
- Implementation-specific indexes (workload-dependent)
- Domain-specific features (tags, workflows, etc.)
- User-specific customizations

### Base Schema Refinement Rules (v1.0 → v1.1)

| Change Type | Allowed? | Examples |
|-------------|----------|----------|
| **Specification clarity** | ✅ Yes | Add timezone precision (`transaction_date` must be ISO8601 with UTC+0000) |
| **Compatible constraints** | ✅ Yes | Add `CHECK` constraint satisfied by all existing data |
| **Documentation** | ✅ Yes | Add comments, usage examples |
| **Core indexes** | ✅ Yes | Add indexes for PRD-defined workflows |
| **Implementation indexes** | ❌ No | Use extension (workload-specific) |
| **New tables/columns** | ❌ No | Use v2.0 or extension |
| **Type changes** | ❌ No | Use v2.0 |
| **Relationship changes** | ❌ No | Use v2.0 |
| **Migration required** | ❌ No | Use v2.0 |

### Decision Tree for Base Schema Changes

```
Does this change affect the structure of base schema tables?
├─ Yes → Does it require data migration?
│   ├─ Yes → v2.0 (breaking change)
│   └─ No → Can it be expressed as a clarification/constraint?
│       ├─ Yes → v1.1 (refinement)
│       └─ No → v2.0 (breaking change)
└─ No → Is it purely documentation or indexing?
    └─ Yes → v1.1 (clarification) or implementation (no version bump)
```

---

## Extension Mechanisms

MemoGarden provides **two mechanisms** for extensions, serving different use cases.

### Mechanism A: Structured Extensions (extension.sql)

**Purpose:** Create new tables with type safety, referential integrity, and efficient querying.

**Rules:**
- ✅ CREATE TABLE (new tables only)
- ✅ CREATE INDEX (any index)
- ✅ CREATE VIEW (undefined behavior, future work)
- ✅ Foreign keys (to base tables or other extension tables)
- ❌ ALTER TABLE on existing base tables (keeps base schema predictable)
- ❌ DROP TABLE from base schema

**Example:**
```sql
-- extension.sql
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_id TEXT,
    color TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES tags(id)
);

CREATE TABLE entity_tags (
    entity_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (entity_id, tag_id),
    FOREIGN KEY (entity_id) REFERENCES entity(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX idx_tags_parent ON tags(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_entity_tags_entity ON entity_tags(entity_id);
CREATE INDEX idx_entity_tags_tag ON entity_tags(tag_id);
```

**When to use:**
- Relational data (many-to-many, hierarchies)
- Frequently queried fields (need indexes)
- Shared across entities
- Referential integrity required
- Stable, well-defined schema

---

### Mechanism B: JSON Extension Data

**Purpose:** Flexible, schema-optional data for entity-specific metadata.

**Schema:**
```sql
CREATE TABLE extension (
    uuid TEXT PRIMARY KEY,        -- References entity(id)
    schema_version TEXT NOT NULL, -- e.g., "memogarden-core-v1"
    extension_version TEXT NOT NULL, -- e.g., "20250411"
    data TEXT NOT NULL,           -- JSON extension data
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (uuid) REFERENCES entity(id) ON DELETE CASCADE
);

CREATE INDEX idx_extension_schema_version ON extension(schema_version);
CREATE INDEX idx_extension_version ON extension(extension_version);
```

**Example data:**
```json
{
    "tags": ["personal", "urgent"],
    "custom_fields": {
        "receipt_url": "https://example.com/receipt.pdf",
        "merchant_id": "12345"
    }
}
```

**When to use:**
- Entity-specific metadata (rarely queried)
- Experimental features (structure still evolving)
- Simple key-value pairs (settings, flags)
- Heterogeneous data (each entity has different fields)

**Query performance:** Not a priority for personal knowledge systems. Query efficiency can be improved by migrating frequently-used fields to structured tables (base schema or extension).

---

## JSON Schema Format

### Global Schema

MemoGarden uses a **global JSON schema** (not per-entity-type) to keep complexity small.

- Defined in `extension.schema.json`
- Applies to all entities using the `extension` table
- Forward compatible: all fields optional or have defaults
- JSON Schema Draft 07 format

### Example Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "version": "20250411",
    "description": "Tags and custom fields for transaction categorization",
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tag names for categorization"
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "default": "medium",
            "description": "Priority level for task management"
        },
        "custom_fields": {
            "type": "object",
            "properties": {
                "receipt_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Link to receipt document"
                },
                "merchant_id": {
                    "type": "string",
                    "description": "Merchant identifier"
                }
            }
        }
    },
    "additionalProperties": true,
    "required": []
}
```

### Schema Rules

1. **All fields optional OR have defaults** (forward compatibility)
2. **No per-entity-type schemas** (global schema only, keep it simple)
3. **Additional properties allowed** (experimental fields OK)
4. **Version tracked in schema** (`"version": "20250411"`)

---

## Extension Metadata

### _extension_metadata Table

```sql
CREATE TABLE _extension_metadata (
    extension_date TEXT PRIMARY KEY,  -- e.g., "20250411"
    based_on TEXT NOT NULL,           -- e.g., "memogarden-core-v1"
    summary TEXT NOT NULL,            -- Short description
    breaking INTEGER NOT NULL DEFAULT 0,
    migration_required INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,

    -- Structured extension changes (extension.sql)
    tables_added TEXT,         -- JSON array: ["tags", "entity_tags"]
    tables_modified TEXT,      -- JSON array: MUST be [] (no ALTER TABLE)
    tables_dropped TEXT,       -- JSON array
    columns_added TEXT,        -- JSON array of objects
    columns_modified TEXT,     -- JSON array: MUST be [] (no ALTER TABLE)
    columns_dropped TEXT,      -- JSON array
    indexes_added TEXT,        -- JSON array
    constraints_added TEXT,    -- JSON array

    -- JSON schema reference
    json_schema TEXT,          -- Full JSON Schema as JSON string

    -- Free-form notes
    notes TEXT                 -- User documentation, TODOs, rationale
);
```

### Extension Version Tracking

Extension version is tracked in **two places**:

1. **extension.schema.json** - `"version": "20250411"`
2. **extension.sql** - `INSERT INTO _extension_metadata (extension_date, ...) VALUES ('20250411', ...)`

This duplication provides:
- Machine-readable version in JSON
- Queryable metadata in SQL
- Validation at both schema and data levels

---

## Capability Declaration

### Format

**Syntax:** `{base_schema}+{extension_date}`

**Examples:**
- `memogarden-core-v1+20250411` - Base v1, extension from 2025-04-11
- `memogarden-core-v1.1+20250415` - Base v1.1, extension from 2025-04-15

### Usage

**In API headers:**
```
X-Schema-Version: memogarden-core-v1+20250411
```

**In exported entities (for interpretability):**
```json
{
    "entity": {...},
    "_meta": {
        "schema": "memogarden-core-v1+20250411",
        "extension_description": "Tags table with hierarchy support"
    }
}
```

---

## Extension Sharing

### Purpose: Interpretability, Not Compatibility

Extensions may be shared between systems to **aid interpretation** of exported entities. There is **no expectation** that two systems use the same extension.

### Export Format

When exporting entities, include:
1. Entity data (with extension fields)
2. Schema capability string (for reference)
3. Extension description (for understanding)

```json
{
    "id": "abc-123",
    "amount": 100.0,
    "tags": ["personal", "urgent"],  // Extension field
    "_meta": {
        "schema": "memogarden-core-v1+20250411",
        "extension_summary": "Tags table with hierarchy support"
    }
}
```

### Import Workflow

1. **Read** extension description to understand fields
2. **Map** incoming fields to local schema (agent-assisted, manual or semi-automated)
3. **Store** using local schema + extension (recipient's extension)
4. **Archive** original entity in Soil for reference

### Key Points

- **Recipient controls schema** - no forced schema changes
- **Unknown fields ignored** (forward compatibility)
- **Foreign keys to extension tables nullable** (allows ignoring)
- **Manual merge required** when systems converge

---

## Extension Lifecycle

### Stages

1. **Create** - User/agent creates new extension
   - Write `extension.sql` (structured changes)
   - Write `extension.schema.json` (JSON schema)
   - Update `_extension_metadata`

2. **Use** - System uses extension
   - Referenced in `_schema_metadata.extension`
   - Entities can have extension data

3. **Change** - User/agent updates extension
   - Overwrite `extension.sql` and `extension.schema.json`
   - Migration required (see [migration-mechanism.md](./migration-mechanism.md))

4. **Archive** - Extension no longer active
   - Copy to `memogarden-soil/core-migration/extensions/{date}/`
   - Create schema snapshot in `soil/core-migration/snapshots/{date}.sql`
   - Update `_schema_metadata`

5. **Fossilize** (Future) - Lossy compaction after long period of non-use
   - See [soil-design.md](./soil-design.md) for fossilization mechanism

### Schema Evolution

Extensions are **semi-regularly changed** and **no stability is expected** unless desired by the user.

**Example evolution:**
```
20250411: Add tags table
20250415: Add tag hierarchy (parent_id)
20250420: Add tag colors
20250425: Rollback tag colors (experimental feature failed)
```

Each change is a new extension version (new date). All versions archived in Soil.

---

## Extension Constraints

### No ALTER TABLE on Base Tables

Extensions **cannot ALTER existing base tables**. This keeps base schema behavior predictable.

**Valid:**
```sql
✅ CREATE TABLE tags (...);
✅ CREATE INDEX idx_tags_name ON tags(name);
```

**Invalid:**
```sql
❌ ALTER TABLE transactions ADD COLUMN tags TEXT;
❌ ALTER TABLE entity ADD COLUMN custom_field TEXT;
```

**Rationale:** Prevents extensions from breaking base schema assumptions. If extension needs to modify base table behavior, include required tables in the extension itself.

### No Dependencies Between Extensions

Since only **one extension is active at a time**, extension dependencies are not supported.

**If Extension B needs tables from Extension A:** Extension B must include the table definitions in its own `extension.sql`.

**Example:**
```
Extension 20250411: Creates tags table
Extension 20250415: Needs tags table
→ Extension 20250415 includes CREATE TABLE tags in its extension.sql
```

**Rationale:** Simplicity. No dependency graphs. Extensions are self-contained.

### Extension Metadata Tracking

**tables_modified** and **columns_modified** MUST be empty JSON arrays (`[]`).

**Rationale:** Extensions cannot modify existing tables (no ALTER TABLE), so these fields should always be empty.

---

## Migration and Compatibility

See [migration-mechanism.md](./migration-mechanism.md) for:
- How to migrate from one extension to another
- Compatibility checking rules
- Deconfliction strategies
- Data transformation approach
- Rollback mechanism

---

## Archival and Fossilization

See [soil-design.md](./soil-design.md) for:
- Memogarden Soil directory structure
- How extensions are archived
- Fossilization (lossy compaction)
- Retrieval and reconstruction

---

## Summary

| Aspect | Specification |
|--------|---------------|
| **Base schema** | Public, stable, versioned (v1.0, v1.1, v2.0) |
| **Extensions** | Personal, experimental, single active at a time |
| **Structured extensions** | New tables only (extension.sql) |
| **JSON extensions** | Flexible data (extension table) |
| **JSON schema** | Global, all fields optional or have defaults |
| **Capability declaration** | `{base_schema}+{extension_date}` |
| **Extension sharing** | Interpretability only, no compatibility expectation |
| **ALTER TABLE** | Not allowed on base tables |
| **Dependencies** | Not supported (self-contained extensions) |
| **Archival** | memogarden-soil (core-migration/extensions/) |
| **Fossilization** | Future work (lossy compaction) |

---

**Related Documents:**
- [migration-mechanism.md](./migration-mechanism.md) - How to migrate between extensions
- [soil-design.md](./soil-design.md) - Memogarden Soil architecture
- [../prd.md](../prd.md) - Product Requirements Document
- [../implementation.md](../implementation.md) - Implementation Plan
