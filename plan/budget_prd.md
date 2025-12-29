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

### Daily Workflows

* Add transactions quickly
* Classify by account (e.g. Household / Personal)
* Categorize spending
* Set amount, currency, and transaction date (UTC)
* Review spending by day / month / year
* Create and maintain recurring transactions

### Agent-Assisted Workflows

* Digest bank and credit card statements
* Reconcile statements against logged transactions
* Scan emails/invoices and propose transactions
* Flag missing, duplicated, or unreconciled items

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

### Relations (MemoGarden Core)

```
id
core_id                -- e.g. transaction_id
ref_id                 -- Soil artifact ID
ref_type               -- source | reconciliation | other
notes?
created_at
revoked_on?
```

Notes:

* Enables linking invoices, emails, and statements without embedding document logic into Core tables.

---

### Artifacts (MemoGarden Soil)

* Immutable documents (emails, PDFs, statements, OCR outputs)
* Append-only, lossy over long horizons by design
* Organized into buckets by fixity level:
  * `artifacts/` - Immutable objects (emails, PDFs, statements)
  * `core-migration/` - Schema snapshots and applied migrations (for agent reference and data archaeology)
  * `core-delta/` - Transaction change history
  * `documents/` - Mutable docs with ongoing changes
  * `fossils/` - Compacted/archived artifacts
* Read-only to agents and humans; written by special `soil` user
* Enables historical reconstruction without cluttering Core implementation

---

### Deltas (MemoGarden Memory Log)

* Record all mutations to Core snapshot
* Field-level changes with rationale
* Atomic grouping (e.g. transaction split)
* Not optimized for querying; optimized for reconstruction

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

---

## Success Criteria

* Transaction capture remains sub-5 seconds
* Agents can reconcile a full monthly statement without schema workarounds
* Users can review past spending without caring about reconciliation mechanics
* Schema tolerates future extensions without retroactive rewrites

---

## Non-Goals

* Perfect historical fidelity
* Lossless long-term storage
* Enterprise-grade financial correctness

This system optimizes for *interpretability*, not auditability.
