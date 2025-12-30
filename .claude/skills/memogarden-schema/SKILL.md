---
name: memogarden-schema
description: SQLite schema modification workflow, data model reference, and conventions for MemoGarden Core. Use when adding tables, modifying columns, changing database structure, or referencing the data model.
---

# Working with SQLite Schema

## Schema Modification Workflow

Follow this step-by-step process when modifying the database schema:

### 1. Edit Schema File

Edit [memogarden_core/schema/schema.sql](../../memogarden/memogarden-core/memogarden_core/schema/schema.sql):

```sql
-- Example: Adding a new column to transactions table
ALTER TABLE transactions ADD COLUMN tags TEXT;
```

### 2. Create Migration Script (if needed)

If the database already exists in production, create a migration script:

```bash
# Migrations are stored in db/migrations/
mkdir -p /home/kureshii/memogarden/memogarden-core/memogarden_core/db/migrations
```

Create migration file: `db/migrations/001_add_tags_to_transactions.sql`

```sql
-- Migration: Add tags column to transactions
-- Date: 2025-12-24

ALTER TABLE transactions ADD COLUMN tags TEXT;
```

**Note:** For the complete migration framework with deconfliction, validation, and rollback strategies, see `/plan/future/migration-mechanism.md`.

### 3. Update Seed Data (if tables changed)

If you modified tables referenced in seed data, update:

[memogarden_core/schema/seed.sql](../../memogarden/memogarden-core/memogarden_core/schema/seed.sql)

### 4. Update Pydantic Schemas

Update API request/response schemas to match schema:

```python
# memogarden_core/api/v1/schemas/transaction.py
class TransactionCreate(BaseModel):
    ...
    tags: str | None = Field(None, description="Optional tags")
```

### 5. Update Core Operations (if needed)

Update operations classes if schema changes affect database operations:

[memogarden_core/db/transaction.py](../../memogarden/memogarden-core/memogarden_core/db/transaction.py)

```python
def create(self, entity_id: str, amount: float, ..., tags: str | None = None):
    ...
    sql = """
        INSERT INTO transactions (id, amount, ..., tags, created_at, updated_at)
        VALUES (?, ?, ..., ?, ?, ?)
    """
    ...
```

### 6. Test with Fresh Database

Always test schema changes with a fresh database:

```bash
cd /home/kureshii/memogarden/memogarden-core

# Remove existing database
rm -f data/memogarden.db

# Reinitialize
poetry run python -c "from memogarden_core.db import init_db; init_db()"

# Run tests
poetry run pytest
```

## Schema Conventions

### Column Naming

- **Primary keys**: `id` (TEXT, UUID v4)
- **Foreign keys**: `<table>_id` (e.g., `account_id`, `category_id`)
- **Timestamps**: `created_at`, `updated_at` (TEXT, ISO 8601 UTC)
- **Dates**: `<entity>_date` (e.g., `transaction_date`) (TEXT, ISO 8601 date)
- **Booleans**: `is_<action>` (e.g., `is_active`) (INTEGER, 0 or 1)

### Data Types

```sql
-- Identifiers (UUIDs)
TEXT PRIMARY KEY

-- Foreign keys
TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE

-- Numeric values
REAL NOT NULL

-- Text content
TEXT

-- ISO 8601 timestamps
TEXT NOT NULL  -- Format: '2025-12-24T10:30:00Z'

-- ISO 8601 dates
TEXT NOT NULL  -- Format: '2025-12-24'

-- Boolean flags
INTEGER NOT NULL DEFAULT 0  -- 0 = false, 1 = true
```

### Constraints

```sql
-- Foreign key with cascade
FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE

-- Unique constraint
UNIQUE(email, username)

-- Check constraint
CHECK (amount >= 0)

-- Not null with default
TEXT NOT NULL DEFAULT 'SGD'
```

### Entity Registry Pattern

All major entities must have entries in `entity_registry`:

```sql
-- When creating a transaction
-- 1. Create entity registry entry first
INSERT INTO entity_registry (id, entity_type, created_at, updated_at)
VALUES (?, 'transactions ?, ?);

-- 2. Then create the transaction
INSERT INTO transactions (id, amount, ...)
VALUES (?, ...);
```

The Core API handles this automatically when using `core.transaction.create()`.

## Data Model Quick Reference

### Transactions (Core Entity)

```sql
id              TEXT PRIMARY KEY    -- UUID
amount          REAL                -- Numeric value
currency        TEXT                -- Default 'SGD'
transaction_date TEXT               -- ISO 8601 date (YYYY-MM-DD)
account_id      TEXT                -- FK to accounts
category_id     TEXT                -- FK to categories (nullable)
author          TEXT                -- User/agent identifier
recurrence_id   TEXT                -- FK to recurrences (nullable)
notes           TEXT                -- Optional description
created_at      TEXT                -- ISO 8601 timestamp
updated_at      TEXT                -- ISO 8601 timestamp
```

### Accounts

```sql
id          TEXT PRIMARY KEY
name        TEXT                    -- e.g., "Household", "Personal"
currency    TEXT                    -- Default 'SGD'
created_at  TEXT
updated_at  TEXT
```

### Categories

```sql
id          TEXT PRIMARY KEY
name        TEXT                    -- e.g., "Food", "Transport"
icon        TEXT                    -- Optional icon identifier
created_at  TEXT
updated_at  TEXT
```

## Common Schema Changes

### Adding a Column

```sql
ALTER TABLE transactions ADD COLUMN tags TEXT;
```

### Adding a Table

```sql
CREATE TABLE recurrences (
    id TEXT PRIMARY KEY,
    frequency TEXT NOT NULL,
    interval_value INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Adding an Index

```sql
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
```

### Adding a Foreign Key

Requires recreating table (SQLite limitation):

```sql
-- 1. Create new table with foreign key
CREATE TABLE transactions_new (
    ...
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- 2. Copy data
INSERT INTO transactions_new SELECT * FROM transactions;

-- 3. Drop old table
DROP TABLE transactions;

-- 4. Rename new table
ALTER TABLE transactions_new RENAME TO transactions;
```

## Verification

After schema changes, verify:

```bash
# Connect to database
sqlite3 /home/kureshii/memogarden/memogarden-core/data/memogarden.db

# Check schema
.schema transactions

# Verify data integrity
PRAGMA integrity_check;

# Check foreign keys are enabled
PRAGMA foreign_keys;

# Exit
.quit
```

## Important Notes

1. **No ORM**: All SQL is handwritten - schema.sql is source of truth
2. **Auto-generated IDs**: All entity IDs are plain UUID v4 strings (database storage)
   - **API layer adds prefixes**: `entity_` for Entities, `item_` for Soil Items (future)
   - Database stores plain UUIDs: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
   - API returns prefixed: `entity_a1b2c3d4-e5f6-7890-abcd-ef1234567890`
3. **UTC timestamps**: Always store timestamps as ISO 8601 UTC: `2025-12-24T10:30:00Z`
4. **Foreign keys**: Enabled via `PRAGMA foreign_keys = ON`
5. **WAL mode**: Enabled for concurrent access: `PRAGMA journal_mode = WAL`
6. **Entity vs Item**: Entities (mutable Core) vs Items (immutable Soil, future) - distinct types with different purposes

## Future Design Reference

For advanced schema topics and design decisions documented for future implementation:

- **Schema Extension System**: `/plan/future/schema-extension-design.md`
  - Base schema vs. extensions philosophy
  - Two extension mechanisms (structured SQL + JSON data)
  - Extension lifecycle and sharing between users

- **Migration Framework**: `/plan/future/migration-mechanism.md`
  - Complete migration workflow with validation
  - Deconfliction rules and conflict resolution
  - Default value application and rollback strategy
  - Soil archival for schema history

- **Memogarden Soil**: `/plan/future/soil-design.md`
  - Immutable storage architecture for emails, invoices, statements
  - Fossilization mechanism (lossy compaction)
  - Retrieval and reconstruction APIs

These documents are design references for when MemoGarden needs schema evolution, multi-user extensions, or document archival capabilities.

For database architecture details, see [architecture.md](../../memogarden/memogarden-core/docs/architecture.md).
