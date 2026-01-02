# MemoGarden Budget App — Product Requirements Document (Updated)

## Purpose

A lightweight personal expenditure capture and review system, inspired by Monefy’s fast, low-friction UI, but deeply integrated into MemoGarden so that human users and agents operate over the same financial belief layer.

This is **not** a budgeting or accounting product. It is a memory system for money-related events, optimized for recall, reconciliation, and later interpretation.

---

## Core Principles

1. **Single Source of Truth**
   All transactions are written via MemoGarden Core. The Budget app and agents share the same API and data model.

2. **Single-User/Household Context**
   MemoGarden Core is designed for single-user or household deployments. Data access is permitted through:
   - **External apps** (Budget app, web UI) via JWT authentication
   - **Local agents** (Letta-based, running on the same server) via API keys
   - **External agents** (future, mechanism TBD) may be supported for remote workflows

3. **Transactions Are Beliefs**
   A transaction represents the user's understanding at the time of payment, not the bank's ledger. Reconciliation is a later act of alignment, not mutation of history.

4. **UI Simplicity, Core Completeness**
   The Budget app intentionally exposes a subset of fields. All metadata remains editable through Core APIs and agent/admin tooling.

5. **Mutable Snapshot, Immutable Memory**
   MemoGarden Core presents a current, human-queryable snapshot. All changes emit deltas, enabling partial reconstruction of the past.

6. **Document-Centric Traceability**
   Every transaction may be linked to one or more immutable Soil artifacts (emails, invoices, statements) via relations.

7. **Schema as Living Document**
   The data model evolves over time. Users may have different schema versions (reconcilable drift). Fresh databases use current schema; existing databases migrate forward-only. Schema history is preserved in Soil for agent understanding and data archaeology.

---

## In Scope

### UUID System

MemoGarden uses **separate UUID namespaces** for different systems:

| System | Prefix | Database | Mutability |
|--------|--------|----------|------------|
| **Core Entities** | `entity_` | Core DB | Mutable |
| **Soil Items** | `item_` | Soil DB | Immutable (future) |

**Budget MVP** uses `entity_` prefix only (e.g., `entity_a1b2c3d4-e5f6-7890-abcd-ef1234567890`).

**Future**: When Soil is implemented for agent workflows, `item_` prefix will be used for archived documents.

### Daily Workflows

* Add transactions quickly
* Classify by account (e.g. Household / Personal)
* Categorize spending
* Set amount, currency, and transaction date (UTC)
* Review spending by day / month / year
* Create and maintain recurring transactions

### Agent-Assisted Workflows - **Future Feature**

* Digest bank and credit card statements
* Reconcile statements against logged transactions
* Scan emails/invoices and propose transactions
* Flag missing, duplicated, or unreconciled items

**Note:** Agent-assisted workflows are **NOT part of Budget MVP**. They require:
- Soil Items (email, PDF archival)
- Relations (document linking)
- Deltas (change tracking)
- Email parsing and classification

Budget MVP is user-manual only. Agents will be considered in future iterations.

---

## Out of Scope

* Budget limits or forecasting
* Tax reporting
* Double-entry accounting
* Offline-first guarantees (reliable sync with MemoGarden is preferred)

---

## Data Model (Budget-Relevant)

### Transactions (MemoGarden Core)

```
id
amount
currency              -- default SGD
transaction_date      -- UTC, day-level semantics
description           -- short title (e.g., "Coffee at Starbucks")
account               -- Label: e.g., "Household", "Personal"
category              -- Label: e.g., "Food", "Transport"
author                -- derived from auth context
recurrence_id?        -- nullable
notes?                -- longer optional details
created_at
updated_at
```

Notes:

* Transactions **do not** have validity windows.
* Corrections, splits, or invalidations are expressed via deltas + new transactions.
* **Accounts and categories are labels**, not relational entities. They exist in the user's mind as classification strings, not as separate database objects with their own lifecycle.
* **Description vs Notes**: `description` is a required short title for quick identification, while `notes` is an optional field for longer details. This separation improves UX by distinguishing quick labels from detailed annotations.

---

### Recurrences (MemoGarden Core)

```
id
rrule                  -- iCal-compatible
entities: []           -- JSON descriptors (e.g. transaction templates)
created_at
valid_from
valid_until?
```

Notes:

* Recurrences generate expectations, not obligations.
* Recurrences are time-bounded and must be reviewed periodically.

---

### Relations (MemoGarden Core) - **Backend Feature**

**Note:** Relations are a **backend agent feature**, not managed through the Budget app UI.

```
id
core_id                -- e.g. transaction_id (entity_ prefix)
ref_id                 -- Soil Item ID (item_ prefix)
ref_type               -- source | reconciliation | other
notes?
created_at
revoked_on?
```

**Scope:**
- **Backend**: Agents create Relations to link invoices/emails to transactions
- **Budget app**: Does NOT expose Relations management UI
- **Purpose**: Document provenance tracking, statement reconciliation

**User Experience:**
- User adds transactions manually in Budget app
- Agent (running on backend/server) processes emails and PDFs
- Agent creates Relations between Items (emails) and Entities (transactions)
- User sees reconciliation results, not Relations directly

---

### Items (MemoGarden Soil)

* **Immutable documents** (emails, PDFs, statements, OCR outputs)
* **Not used in Budget MVP** - Future agent workflows will bridge Items → Entities
* Append-only, lossy over long horizons by design
* Organized into buckets by fixity level:
  * `artifacts/` - Immutable objects (emails, PDFs, statements)
  * `core-migration/` - Schema snapshots and applied migrations (for agent reference and data archaeology)
  * `core-delta/` - Transaction change history (future)
  * `documents/` - Mutable docs with ongoing changes (future, Project System)
  * `fossils/` - Compacted/archived items (future)
* Read-only to agents and humans; written by special `soil` user
* Enables historical reconstruction without cluttering Core implementation

**Note:** Budget MVP uses user-inputted Entities only. Items will be integrated when agent-assisted workflows are added (email parsing, statement reconciliation).

---

### Deltas (MemoGarden Memory Log) - **Future Feature**

* Record all mutations to Core snapshot
* Field-level changes with rationale
* Atomic grouping (e.g. transaction split)
* Not optimized for querying; optimized for reconstruction

**Note:** Deltas are **NOT part of Budget MVP**. They will be implemented when audit trail/history reconstruction features are needed. Budget MVP uses Core database directly without change tracking.

---

## Budget App Local Database

### Architecture Decision: Local-First with Optional Sync

The Budget app uses a **local SQLite database** with the following design principles:

1. **Integer Primary Keys**: Local auto-increment IDs for performance
2. **MemoGarden Sync Optional**: Local-only use cases fully supported
3. **Extension Pattern**: MemoGarden-specific data stored in JSON `extension` column
4. **No Migrations for Features**: New fields added via `metadata` JSON to avoid schema churn

### Local Schema

```sql
CREATE TABLE transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- Core data fields
  amount REAL NOT NULL,
  currency TEXT NOT NULL DEFAULT 'SGD',
  transaction_date TEXT NOT NULL,    -- YYYY-MM-DD
  description TEXT NOT NULL DEFAULT '',
  account TEXT NOT NULL,
  category TEXT,
  notes TEXT,

  -- Recurrence link (NULL = manual/realized, NOT NULL = pending/projection)
  recurrence_id INTEGER,

  -- App-specific features
  tags TEXT,
  attachment_url TEXT,

  -- Timestamps
  created_at TEXT NOT NULL,          -- ISO 8601
  updated_at TEXT NOT NULL,          -- ISO 8601

  -- Extension data (JSON) - MemoGarden sync data
  extension TEXT,                    -- {"memogarden": {"uuid": "...", "last_sync_hash": "...", "version": 5}}

  -- App metadata (JSON) - Experimental/future features
  metadata TEXT                      -- {"custom_field": "value"}
);

CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_recurrence ON transactions(recurrence_id);

CREATE TABLE recurrences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- iCal RRULE (validated client-side via `rrule` Dart package)
  rrule TEXT NOT NULL,               -- "FREQ=MONTHLY;BYDAY=2FR;COUNT=12"

  -- Transaction template (JSON)
  template TEXT NOT NULL,            -- {"amount": 50.0, "description": "Allowance", ...}

  -- Validity window
  valid_from TEXT NOT NULL,          -- ISO 8601 date
  valid_until TEXT,                  -- ISO 8601 date or NULL (forever)

  -- State management
  is_active INTEGER DEFAULT 1,       -- 0 = paused, 1 = active

  -- Occurrence tracking (local-only, for UI)
  last_generated_date TEXT,          -- Last date we generated a transaction
  next_occurrence_date TEXT,         -- Pre-computed next occurrence (for UI display)

  -- Timestamps
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,

  -- Extension data (JSON) - MemoGarden sync data
  extension TEXT,                    -- {"memogarden": {"uuid": "...", "version": 2}}

  -- App metadata (JSON) - Excluded dates, custom settings
  metadata TEXT                      -- {"excluded_dates": ["2025-02-15"], ...}
);

CREATE INDEX idx_recurrences_active ON recurrences(is_active);
CREATE INDEX idx_recurrences_next ON recurrences(next_occurrence_date);
```

### Key Design Decisions

**1. Integer PK with Optional MemoGarden UUID**
- Local ID: Auto-increment INTEGER for performance
- MemoGarden UUID: Stored in `extension.memogarden.uuid` (nullable)
- Local-only users: `extension` is NULL or empty
- Sync users: `extension.memogarden.uuid` contains Core entity UUID

**2. Hash-Based Sync (from PRD v0.4.1)**
- `extension.memogarden.last_sync_hash`: Last known server hash
- `extension.memogarden.version`: Server version number
- Enables conflict detection without scanning full history
- See [memogarden_prd_v4.md](memogarden_prd_v4.md#entity-change-tracking)

**3. Extension vs Metadata**
- **`extension`**: Namespaced external data (`{"memogarden": {...}}`, `{"bank_sync": {...}}`)
- **`metadata`**: App-specific experimental features
- Both JSON to avoid schema migrations

**4. Recurrence Realization Pattern**
- Generated transactions have `recurrence_id NOT NULL`
- Displayed differently (italic, grey, bold) to indicate "pending/projection"
- User must "realize" transaction:
  - **Explicit**: Tap "Realize" button
  - **Implicit**: Edit transaction details
- Realization sets `recurrence_id = NULL`, detaching from recurrence
- Future occurrences regenerate fresh from template

**5. Client-Side RRULE Validation**
- Uses `rrule` Dart package (iCal RFC 5545)
- Validates recurrence syntax locally
- Enables local-only usage without MemoGarden Core

### Sync Protocol (Future)

**Optimistic locking with hash chain:**
1. Client reads entity from server (gets hash + version)
2. Client makes changes locally
3. Client sends update with `based_on_hash`
4. Server validates hash, computes new hash, returns 409 Conflict if mismatch
5. Client resolves conflict (merge, discard local, discard server)

**Local-only users:**
- Never set `extension.memogarden.uuid`
- Never set `extension.memogarden.last_sync_hash`
- Works offline forever

---

## API Requirements

* Budget app and agents use identical endpoints
* Auth context determines:

  * `author`
  * permitted fields
  * default values

Example:

```
POST /transactions
```

---

## UI Scope (Budget App)

### Exposed Fields

* amount
* description (short title)
* category
* account
* transaction_date
* notes (optional, longer details)

### Hidden / Advanced Fields

* relations
* recurrence JSON
* delta rationale
* author overrides

These are accessible via agent tooling or admin interfaces only.

### UI Layout & Navigation

**Follow Material Design guidelines** except where explicitly stated below.

#### Main Screen (Transaction List)

**Left Sidebar (Drawer):**
- Auto-hide drawer (slide from left or tap upper left hamburger icon)
- **Account Filter**: All / Household / Personal
- **Date Range Selector**: Day / Month / Year
- Drawer closes after selection

**App Bar:**
- Title: "Transactions" (or current date range)
- **Settings**: Icon inside overflow menu (three dots) - follow Material Design guidelines

**Transaction List:**
- **Group by Category**: Transactions organized into category sections
- **Sort Categories**: By total transaction amount (descending)
- **Sort Transactions within Category**: By date ascending (oldest first)
- **Account & Category Icons**: Emoji icons supported (UI-only, not synced to extensions)
  - Emoji appears in selector dropdowns
  - Emoji appears in transaction list category groups
  - Purpose: Visual identification, not part of data model
- **Category Group Headers**:
  - Show category name with emoji (if set)
  - Show total amount for category
  - Show percentage of day/month/year total
- **Transaction Items**:
  - Icon: Category emoji or default Material icon
  - Title: Description
  - Subtitle: Account • Date
  - Trailing: Amount (red for expenses, green for income)

**Floating Action Button (FAB):**
- Bottom-right: Add transaction button
- Navigates to transaction capture screen

#### Transaction Capture Screen

**Future Separation:**
- Will split into **Add Expense** and **Add Deposit** screens
- Both use same UI layout, differ only in transaction sign (negative/positive)

**Current UI (Monefy-inspired):**
- Large amount display (calculator-style)
- Number pad: 0-9, decimal point, arithmetic operators (+, -, *, /), equals
- Account dropdown
- Category dropdown (with emoji icons)
- Description text field
- Date display (today's date, selector coming later)
- Save button (green, to distinguish from calculator buttons)
- Placeholder: Future recurrence button

**UX Pattern:**
- Autosave disabled: back/close implies cancel
- Explicit save only (user must tap Save button)

#### Settings Screen (Future)

- Manage accounts (add, edit, delete, assign emoji)
- Manage categories (add, edit, delete, assign emoji)
- Currency settings
- Sync configuration (MemoGarden Core connection)
- Theme preferences

---

## Success Criteria

* Transaction capture remains sub-5 seconds
* Users can review past spending by day/month/year
* Recurring transactions work correctly
* Schema tolerates future extensions (Items, Relations, Deltas) without retroactive rewrites
* Clean separation between user-manual workflows (MVP) and future agent-assisted workflows

---

## Non-Goals

* Perfect historical fidelity
* Lossless long-term storage
* Enterprise-grade financial correctness

This system optimizes for *interpretability*, not auditability.
