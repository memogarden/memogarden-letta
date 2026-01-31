# MemoGarden System

**MemoGarden System** provides the core business logic layers for MemoGarden: the **Soil** layer (immutable records) and **Core** layer (mutable beliefs about transactions and entities).

This is the foundational system package. For the HTTP API, see [memogarden-api](https://github.com/memogarden/memogarden-api).

## Overview

MemoGarden is a personal memory system for financial transactions. It's not traditional budgeting software—it's a belief-based transaction capture and reconciliation system designed for both human users and AI agents.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MemoGarden Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  memogarden-api (HTTP Interface)                      │   │
│  │  ├── Flask application                                  │   │
│  │  ├── Authentication (JWT + API Keys)                   │   │
│  │  └── API endpoints                                     │   │
│  └──────────────────────┬────────────────────────────────┘   │
│                         │ depends on                            │
│  ┌──────────────────────▼────────────────────────────────┐   │
│  │  memogarden-system (This Repository)                   │   │
│  │  ├── system.soil (Immutable Records Layer)             │   │
│  │  │   ├── Items (Notes, Emails, Messages...)             │   │
│  │  │   ├── SystemRelations (cites, replies_to...)        │   │
│  │  │   └── Soil Database                                 │   │
│  │  ├── system.core (Mutable Beliefs Layer)               │   │
│  │  │   ├── Entities (global registry)                     │   │
│  │  │   ├── UserRelations (engagement signals)             │   │
│  │  │   └── ContextFrames (attention tracking)             │   │
│  │  └── system.utils (UUID, hashing, validation)          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  providers/ (Email Importers)                          │   │
│  │  ├── mbox-importer (Google Takeout format)            │   │
│  │  └── gmail-importer (Gmail API - stub)                 │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Packages in This Repository

### memogarden-system (Main Package)

The core system package containing Soil and Core layers:

- **system.soil** - Immutable record storage
  - Items: Notes, Emails, Messages with strict data/metadata separation
  - SystemRelations: Immutable structural facts (cites, replies_to, triggers)
  - Email import utilities and deduplication

- **system.core** - Mutable belief layer
  - Entity registry with hash-based change tracking
  - UserRelation: Engagement signals with time-based decay
  - ContextFrame: Attention tracking per RFC-003

- **system.utils** - Shared utilities
  - UUID generation (Soil and Core prefixes)
  - Hash chain utilities for change tracking
  - Domain types (Timestamp, Date, etc.)

### providers/ (Optional Importers)

Email importers that depend on memogarden-system:

- **mbox-importer** - Import emails from mbox files (Google Takeout)
- **gmail-importer** - Import emails from Gmail API (stub for future OAuth)

## Installation

This is a library package. Install it via [Poetry](https://python-poetry.org/):

```bash
# From project root
cd memogarden-system
poetry install
```

Or via pip:

```bash
pip install memogarden-system
```

## Usage

### Using the Soil Layer (Immutable Records)

```python
from system.soil import Soil, Item, generate_soil_uuid
from datetime import datetime, timezone

# Open Soil database
soil = Soil("soil.db")
soil.init_schema()

# Create an Item
item = Item(
    uuid=generate_soil_uuid(),
    _type="Note",
    realized_at=datetime.now(timezone.utc).isoformat(),
    canonical_at=datetime.now(timezone.utc).isoformat(),
    fidelity="full",
    data={
        "description": "Remember to buy milk"
    },
    metadata={
        "source": "user_input"
    }
)

# Store it
soil.create_item(item)

# Create relations between items
from system.soil import SystemRelation

relation = SystemRelation(
    uuid=generate_soil_uuid(),
    kind="cites",
    source=item.uuid,
    source_type="item",
    target=other_item.uuid,
    target_type="item",
    created_at=2230,  # Days since epoch
    evidence={
        "source": "user_stated",
        "confidence": 1.0
    }
)
soil.create_relation(relation)
```

### Using the Core Layer (Mutable Beliefs)

```python
from system.core import Core, Entity, generate_core_uuid

# Open Core database
core = Core("core.db")
core.init_schema()

# Create an entity
entity = Entity(
    uuid=generate_core_uuid(),
    type="transaction",
    data={
        "amount": -15.50,
        "currency": "SGD",
        "description": "Coffee at Starbucks"
    }
)

# Store it
core.create_entity(entity)

# Query entities
transactions = core.list_entities(type="transaction", limit=10)
```

### Using Email Importers

```python
from system.soil import Soil
from mbox_importer import MboxImporter

# Open Soil database
soil = Soil("soil.db")
soil.init_schema()

# Import from mbox file
importer = MboxImporter(soil, mbox_path="emails.mbox")
stats = importer.import_mbox(verbose=True)
print(stats)
# Output: Processed: 1500, Imported: 1200, Skipped: 300 (duplicates)
```

## Development

### Running Tests

```bash
# From project root
PYTHONPATH=memogarden-system python -m pytest tests/ -v
```

**Test Coverage:** 30/30 tests passing (100%)

### Project Structure

```
memogarden-system/
├── system/                    # Main package (import as "system")
│   ├── __init__.py
│   ├── soil/                 # Immutable records layer
│   │   ├── __init__.py
│   │   ├── item.py           # Item, Evidence classes
│   │   ├── relation.py       # SystemRelation class
│   │   └── database.py        # Soil class
│   ├── core/                 # Mutable beliefs layer
│   │   ├── __init__.py
│   │   ├── entity.py         # Entity operations
│   │   ├── user_relation.py  # UserRelation operations
│   │   ├── context_frame.py  # ContextFrame operations
│   │   └── database.py        # Core class
│   ├── schemas/              # SQL schemas (bundled during build)
│   │   ├── sql/
│   │   │   ├── soil.sql
│   │   │   └── core.sql
│   │   └── types/
│   │       ├── items/
│   │       └── entities/
│   └── utils/                # Shared utilities
│       ├── __init__.py
│       ├── uid.py            # UUID generation
│       ├── hashing.py        # Hash chain utilities
│       └── validation.py     # JSON Schema validation
├── providers/                # Email importers (optional)
│   ├── mbox-importer/        # Google Takeout import
│   └── gmail-importer/       # Gmail API import (stub)
├── tests/                    # Characterization tests
│   └── soil_characterization_tests.py
├── schemas/                  # Schema source files
│   ├── sql/
│   └── types/
├── scripts/                  # Development utilities
├── plan/                     # RFCs and planning docs
└── README.md
```

## Technology Stack

- **Language**: Python 3.13
- **Database**: SQLite (no ORM - raw SQL only)
- **Package Manager**: Poetry

## Core Philosophy

1. **Transactions Are Beliefs** - A transaction represents the user's understanding at the time of payment, not the bank's ledger
2. **Single Source of Truth** - All entities flow through memogarden-system
3. **Immutable Snapshot, Mutable Memory** - Current state can change, but all changes are logged via deltas
4. **Document-Centric Traceability** - Transactions link to immutable artifacts (emails, invoices, statements)
5. **Agent-First Design** - Humans and agents use the same APIs

## Design Principles

- **Synchronous Execution** - SQLite for simplicity and deterministic debugging
- **No ORM** - Raw SQL queries with parameterized statements
- **Entity Registry** - Global metadata table for all entity types
- **UTC Everywhere** - All timestamps in ISO 8601 UTC format
- **Test-Driven** - Behavior-focused tests (no mocks)

## Related Packages

- **[memogarden-api](https://github.com/memogarden/memogarden-api)** - HTTP API layer
- **[mbox-importer](https://github.com/memogarden/mbox-importer)** - Email importer for Google Takeout
- **[gmail-importer](https://github.com/memogarden/gmail-importer)** - Email importer for Gmail API

## Documentation

- **[RFC-004: Package Structure & Deployment](plan/rfc_004_package_deployment_v1.md)** - Architecture and deployment profiles
- **[RFC-003: Context Capture Mechanism](plan/rfc_003_context_mechanism_v2.md)** - Attention tracking
- **[PRD v0.10.0](plan/memogarden_prd_v0_10_0.md)** - Complete platform requirements
- **[Architecture Guide](memogarden-system/docs/architecture.md)** - Technical patterns and conventions

## License

TBD
