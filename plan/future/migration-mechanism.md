# Migration Mechanism

> **Status:** Future Design Work
> **Last Updated:** 2025-12-24
> **Related Documents:** [schema-extension-design.md](./schema-extension-design.md) | [soil-design.md](./soil-design.md)

---

## Overview

This document describes how to migrate from one extension to another in MemoGarden.

### Extension Migration

**Definition:** The process of changing the active extension from version A to version B.

**Examples:**
- Migrating from `20250411` (tags table) to `20250415` (tags + workflows)
- Rolling back from `20250412` to `20250411` (forward-only rollback)
- Upgrading base schema from `v1.0` to `v1.1` (rare, base schema changes)

### Key Principles

1. **Query existing database** for current schema
2. **Check version match** with `/schema` files
3. **Export** current extension data as JSON
4. **Apply** new extension.sql (DDL changes)
5. **Validate** exported data against new schema
6. **Transform** data (apply defaults, deconflict)
7. **Import** validated data into new extension
8. **Update** `_schema_metadata`
9. **Archive** old extension to memogarden-soil

---

## Migration Workflow

### High-Level Algorithm

```python
def migrate_extension(from_version: str, to_version: str):
    """
    Migrate from extension A to extension B

    Args:
        from_version: Current extension version (e.g., "20250411")
        to_version: Target extension version (e.g., "20250415")
    """

    # Step 1: Query existing database for current schema
    current_schema = get_current_schema()
    if current_schema['extension'] != from_version:
        raise MigrationError(f"Expected {from_version}, found {current_schema['extension']}")

    # Step 2: Check version match with /schema files
    new_schema_json = load_extension_schema_json(to_version)
    new_schema_sql = load_extension_schema_sql(to_version)

    # Step 3: Export current extension data as JSON
    exported_data = export_extension_data()

    # Step 4: Apply new extension.sql (DDL changes)
    apply_extension_sql(new_schema_sql)

    # Step 5: Validate exported data against new schema
    conflicts = validate_schema_compatibility(current_schema, new_schema_json)
    if conflicts:
        raise MigrationError(f"Schema conflicts: {conflicts}")

    # Step 6: Transform data (apply defaults, deconflict)
    transformed_data = []
    for entity_data in exported_data:
        # Apply defaults for new fields
        entity_data = apply_defaults(entity_data, new_schema_json)
        # Validate against new schema
        validate_data(entity_data, new_schema_json)
        transformed_data.append(entity_data)

    # Step 7: Import validated data into new extension
    import_extension_data(transformed_data)

    # Step 8: Update _schema_metadata
    update_schema_metadata(to_version)

    # Step 9: Archive old extension to memogarden-soil
    archive_extension_to_soil(from_version)
```

---

## Pre-Migration: Compatibility Check

### Agent-Assisted Review

**Recommended:** Users should have an agent review proposed extensions for compatibility with existing schema.

**Future:** Automated validation scripts will be provided.

### Deconfliction Rules

| Change Type | Rule | Action | Example |
|-------------|------|--------|---------|
| **Field type change** | ❌ Conflict | Abort, manual resolution | String → Integer |
| **Field removal** | ⚠️ Warning | User confirmation required | Removing `priority` field |
| **Field addition** | ✅ OK | Apply default value | Adding `urgent` boolean |
| **Optional → required** | ⚠️ Warning | Apply default if available | Making `tags` required |
| **Required → optional** | ✅ OK | No action needed | Making `priority` optional |
| **Table dropped** | ❌ Conflict | Abort, manual resolution | Dropping `tags` table |
| **Table added** | ✅ OK | No impact on existing data | Adding `workflows` table |
| **Table schema change** | ⚠️ Warning | Data migration required | Adding `parent_id` to `tags` |

### Validation Algorithm

```python
def validate_schema_compatibility(old_schema: dict, new_schema: dict) -> list[str]:
    """
    Check for schema conflicts between two extensions.

    Returns:
        List of conflict descriptions (empty if compatible)
    """
    conflicts = []

    # Check for type changes
    for field in old_schema.get('properties', {}):
        if field in new_schema.get('properties', {}):
            old_type = old_schema['properties'][field].get('type')
            new_type = new_schema['properties'][field].get('type')
            if old_type != new_type:
                conflicts.append(
                    f"Type change: {field} ({old_type} → {new_type})"
                )

    # Check for removed fields (violates forward compatibility)
    for field in old_schema.get('properties', {}):
        if field not in new_schema.get('properties', {}):
            conflicts.append(f"Removed field: {field}")

    # Check for table drops (structured extensions)
    old_tables = json.loads(old_schema.get('tables_added', '[]'))
    new_tables = json.loads(new_schema.get('tables_added', '[]'))
    dropped_tables = set(old_tables) - set(new_tables)
    if dropped_tables:
        conflicts.append(f"Dropped tables: {dropped_tables}")

    return conflicts
```

---

## Migration Approach: Option B (Export → Drop → Create → Import)

### For Structured Extension Changes

When extension.sql changes table structures (e.g., adding `parent_id` to `tags` table):

```sql
-- Step 1: Export data to JSON
-- (Handled by migration runner)
-- Output: [{"id": "tag-1", "name": "personal"}, ...]

-- Step 2: Drop old table
DROP TABLE IF EXISTS tags;

-- Step 3: Create new table (new schema)
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_id TEXT,  -- NEW FIELD
    color TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES tags(id)
);

-- Step 4: Import and transform data
-- Apply defaults for new fields
INSERT INTO tags (id, name, parent_id, color, created_at, updated_at)
VALUES
    ('tag-1', 'personal', NULL, NULL, '2025-04-11T10:00:00Z', '2025-04-11T10:00:00Z'),
    ('tag-2', 'work', NULL, NULL, '2025-04-11T10:00:00Z', '2025-04-11T10:00:00Z');
-- parent_id set to NULL (default) for all existing tags
```

### For JSON Extension Data

When `extension.schema.json` changes (new fields, type changes, etc.):

```python
# Export existing extension.data
exported = select_all_from_extension()
# Example: [{"uuid": "abc-123", "data": {"tags": ["personal"]}}, ...]

# Transform: Apply defaults for new fields
transformed = []
for entity in exported:
    entity_data = json.loads(entity['data'])

    # Apply defaults for new fields
    for field, spec in new_schema['properties'].items():
        if field not in entity_data and 'default' in spec:
            entity_data[field] = spec['default']

    # Example: {"tags": ["personal"], "priority": "medium"}
    # (priority added with default "medium")

    transformed.append({
        'uuid': entity['uuid'],
        'data': json.dumps(entity_data)
    })

# Validate against new schema
for entity in transformed:
    validate_json_schema(entity['data'], new_schema)
    # Raises error if validation fails

# Import
update_extension_table(transformed)
```

---

## Default Value Application

### Where: Core Layer

**Default values are applied at the Core layer** (not database, not API).

**Rationale:** Core is responsible for data transformation and validation.

### Required Rule: Forward Compatibility

**All fields must be optional OR have default values.**

**Example:**
```json
{
    "properties": {
        "tags": {
            "type": "array",
            "description": "Tag names (optional)"
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "default": "medium"  // REQUIRED for forward compatibility
        }
    },
    "required": []  // No required fields (forward compatible)
}
```

**Why:** When importing entities from a system without the new field, the default value is applied automatically.

### Application Algorithm

```python
def apply_defaults(data: dict, schema: dict) -> dict:
    """
    Apply default values for missing fields.

    Args:
        data: Entity data (may be missing new fields)
        schema: JSON schema with defaults

    Returns:
        Data with defaults applied
    """
    result = data.copy()

    for field, spec in schema.get('properties', {}).items():
        if field not in result and 'default' in spec:
            result[field] = spec['default']

    return result
```

---

## Major Extension Changes

### Recommendation: Refactor in Stages

**Major changes should be split into multiple smaller extensions.**

**Anti-Pattern (single large migration):**
```
20250411: Add tags table with hierarchy, colors, permissions, and workflows
```
**Problems:**
- Complex migration (multiple points of failure)
- Hard to debug if something goes wrong
- Difficult to roll back partially

**Best Practice (staged migrations):**
```
20250411: Add tags table (basic)
20250415: Add tag hierarchy (parent_id)
20250420: Add tag colors (color field)
20250425: Add tag permissions (experimental)
```

**Benefits:**
- Each migration is simple and focused
- Easy to roll back specific stages
- Can pause between stages
- Better archaeology (clear evolution)

---

## Rollback Strategy

### Forward-Only Rollbacks

**Rollbacks are implemented as new migrations** that undo previous changes.

**Example:**
```sql
-- Extension 20250411: Added tags table
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

-- Extension 20250412: Rollback tags table (experimental feature failed)
DROP TABLE tags;
```

### Rollback Workflow

```python
def rollback_extension(from_version: str) -> str:
    """
    Rollback to previous extension version.

    Args:
        from_version: Current version to rollback from

    Returns:
        New rollback version (e.g., "20250412")
    """
    # Create new rollback version
    rollback_version = generate_extension_version()  # e.g., "20250412"

    # Export current data
    exported_data = export_extension_data()

    # Apply rollback (undo changes)
    apply_rollback_migration(from_version)

    # Import data (may need transformation)
    import_extension_data(exported_data)

    # Update metadata
    update_schema_metadata(rollback_version)

    # Archive rolled-back extension
    archive_extension_to_soil(from_version)

    return rollback_version
```

### Archival

**Both states are preserved in memogarden-soil:**
- `soil/core-migration/extensions/20250411/` - Original extension
- `soil/core-migration/extensions/20250412/` - Rollback extension

**Archaeology:** Full reconstruction possible at any point in history.

---

## Data Loss Prevention

### Checking for Dropped Fields

**Problem:** New extension may drop fields that existing data uses.

**Example:**
```json
// Extension 20250411
{"properties": {"tags": [...], "obsolete_field": {...}}}

// Extension 20250415
{"properties": {"tags": [...]}}  // obsolete_field removed
```

### Prevention Algorithm

```python
def check_dropped_fields(old_schema: dict, new_schema: dict, data: list) -> list[str]:
    """
    Check if dropping fields would lose data.

    Returns:
        List of fields that would lose data
    """
    dropped = set(old_schema.get('properties', {}).keys()) - set(new_schema.get('properties', {}).keys())

    fields_with_data = []
    for entity in data:
        entity_data = json.loads(entity['data'])
        for field in dropped:
            if field in entity_data:
                fields_with_data.append(field)

    return list(set(fields_with_data))


# Usage
dropped_fields = check_dropped_fields(old_schema, new_schema, exported_data)
if dropped_fields:
    if not confirm_data_loss(dropped_fields):
        raise MigrationError("Migration aborted by user")
    # Archive dropped field data to Soil before proceeding
    archive_dropped_fields(dropped_fields, exported_data)
```

### User Confirmation

**When data loss would occur:**
1. **Warn user** about fields that will be dropped
2. **Show sample data** that will be lost
3. **Require explicit confirmation** to proceed
4. **Archive to Soil** before migration (data archaeology)

---

## Entity Conversion Strategy

### Type Conversions

**Safe conversions** (when field type changes):

| From | To | Safe? | Conversion |
|------|-----|-------|------------|
| string | integer | ⚠️ Maybe | `int(value)` (may raise) |
| integer | string | ✅ Yes | `str(value)` |
| string | number | ⚠️ Maybe | `float(value)` (may raise) |
| number | string | ✅ Yes | `str(value)` |
| array | array (item type change) | ⚠️ Maybe | Per-item conversion |

**Algorithm:**
```python
def convert_entity(data: dict, old_schema: dict, new_schema: dict) -> dict:
    """
    Convert entity data from old schema to new schema.
    """
    result = data.copy()

    for field, new_spec in new_schema.get('properties', {}).items():
        if field in result and field in old_schema.get('properties', {}):
            old_type = old_schema['properties'][field].get('type')
            new_type = new_spec.get('type')

            # Safe conversions
            if old_type == 'string' and new_type == 'integer':
                try:
                    result[field] = int(result[field])
                except (ValueError, TypeError):
                    raise ConversionError(f"Cannot convert {field} to integer")
            elif old_type == 'integer' and new_type == 'string':
                result[field] = str(result[field])
            # Add more conversions as needed

    # Remove dropped fields (after confirmation)
    dropped = set(old_schema.get('properties', {}).keys()) - set(new_schema.get('properties', {}).keys())
    for field in dropped:
        if field in result:
            del result[field]

    # Apply defaults for new fields
    for field, spec in new_schema.get('properties', {}).items():
        if field not in result and 'default' in spec:
            result[field] = spec['default']

    # Validate against new schema
    validate_json_schema(result, new_schema)

    return result
```

---

## Migration Scripts

### File Organization

```
soil/core-migration/migrations/
└── {from_version}-to-{to_version}/
    ├── migrate.sql         # DDL changes
    ├── transform.py        # Data transformation (optional)
    └── rollback.sql        # Rollback script (optional)
```

### Example Migration Script

**File:** `soil/core-migration/migrations/20250411-to-20250415/migrate.sql`

```sql
-- Migration: 20250411 to 20250415
-- Description: Add tag hierarchy (parent_id field)
-- Breaking: No
-- Data Migration: Yes (export → drop → create → import)

-- Step 1: Export data to JSON
-- (Handled by migration runner, not in SQL)

-- Step 2: Drop old table
DROP TABLE IF EXISTS tags;

-- Step 3: Create new table with parent_id
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_id TEXT,
    color TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES tags(id)
);

CREATE INDEX idx_tags_parent ON tags(parent_id) WHERE parent_id IS NOT NULL;

-- Step 4: Import data (handled by migration runner)
-- parent_id set to NULL for all existing tags
```

**File:** `soil/core-migration/migrations/20250411-to-20250415/transform.py`

```python
"""
Data transformation for 20250411 → 20250415 migration.

Adds parent_id field to tags table.
"""

def transform_tags(tags_data: list[dict]) -> list[dict]:
    """
    Transform tag data for new schema.

    Args:
        tags_data: List of tag dicts from old schema

    Returns:
        List of tag dicts with parent_id added (NULL for all)
    """
    transformed = []
    for tag in tags_data:
        tag['parent_id'] = None  # New field, default NULL
        transformed.append(tag)
    return transformed
```

---

## Error Handling

### Migration Failures

**If migration fails:**
1. **Rollback database** to pre-migration state
2. **Log error** with details
3. **Preserve exported data** for manual recovery
4. **Archive failed attempt** to Soil

### Rollback on Failure

```python
def migrate_with_rollback(from_version: str, to_version: str):
    """
    Migrate with automatic rollback on failure.
    """
    # Create database savepoint
    with savepoint() as sp:
        try:
            migrate_extension(from_version, to_version)
        except Exception as e:
            # Rollback to savepoint
            sp.rollback()
            logger.error(f"Migration failed: {e}")
            # Preserve exported data for manual recovery
            archive_failed_migration(e, exported_data)
            raise
```

---

## Summary

| Aspect | Specification |
|--------|---------------|
| **Compatibility check** | Agent-assisted (automated validation future work) |
| **Migration approach** | Export → Drop → Create → Import (Option B) |
| **Default values** | Applied at Core layer |
| **Forward compatibility** | All fields optional or have defaults |
| **Major changes** | Refactor in multiple stages |
| **Rollback** | Forward-only (new migration that undoes changes) |
| **Data loss prevention** | Warn user, require confirmation, archive to Soil |
| **Type conversions** | Safe conversions only, manual for complex cases |
| **Error handling** | Rollback on failure, preserve exported data |

---

**Related Documents:**
- [schema-extension-design.md](./schema-extension-design.md) - Extension system architecture
- [soil-design.md](./soil-design.md) - Memogarden Soil (archival and fossilization)
