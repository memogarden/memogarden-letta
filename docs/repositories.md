# MemoGarden Repository Structure

**Last Updated:** 2026-02-11
**Status:** Session 14+

Complete reference for MemoGarden repositories and their structure.

## Core Repositories

MemoGarden consists of three core repositories that form the production system.

---

### 1. Root Repository (`/`)

**Purpose:** Planning documents, development scripts, agent configuration

**Contains:**
- `plan/` - Planning documents
  - `memogarden-implementation-plan.md` - Implementation roadmap
  - `memogarden_prd_v0_11_0.md` - Platform PRD
  - `budget_prd.md` - Budget app requirements
  - `rfc_*.md` - RFC documents (RFC-001 through RFC-009)
- `scripts/` - Development automation
  - `run.sh` - Start API server
  - `test.sh` - Run tests
  - `lint.sh` - Run ruff linter
  - `pre-commit` - Pre-commit hook
- `docs/` - User and developer documentation
  - `quickstart.md` - Getting started guide
  - `deployment.md` - Deployment guide
  - `configuration.md` - Configuration reference
  - `repositories.md` - This file
- `.claude/` - Claude Code agent configuration
  - `skills/` - Task-specific skills
  - `agents/` - Subagents for code review
- `AGENTS.md` / `CLAUDE.md` - Agent guide (symlink)

**Git:** Root repository
**Commits affect:** docs, plans, scripts, .claude/

---

### 2. System Repository (`memogarden-system/`)

**Purpose:** Core library containing Soil and Core layers

**Structure:**
```
memogarden-system/
├── system/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── exceptions.py          # MemoGarden exceptions
│   ├── schemas.py            # Schema loading utilities
│   ├── core/                # Core database operations
│   │   ├── __init__.py      # Core.get_core()
│   │   ├── entity.py        # Entity registry operations
│   │   ├── transaction.py   # Transaction operations
│   │   ├── recurrence.py    # Recurrence operations
│   │   ├── relation.py      # User relations (RFC-002)
│   │   └── context.py      # Context frames (RFC-003)
│   ├── soil/                # Soil database operations
│   │   ├── __init__.py
│   │   ├── artifact.py       # Artifact operations
│   │   └── ...
│   ├── utils/               # Shared utilities
│   │   ├── uid.py          # UUID utilities
│   │   ├── isodatetime.py  # Timestamp utilities
│   │   ├── hash_chain.py   # Hash computation
│   │   └── secret.py      # Secret generation
│   ├── schemas/             # SQL schemas
│   │   └── sql/
│   │       ├── core.sql     # Core schema
│   │       └── migrations/  # Schema migrations
│   └── host/               # Host environment utilities
│       └── environment.py   # Path resolution (RFC-004)
├── tests/
│   ├── test_transaction_coordinator.py
│   ├── test_schemas.py
│   ├── test_cross_db_experiment.py
│   └── test_rfc004_deployment.py
├── pyproject.toml
└── README.md
```

**Git:** Separate repository
**Commits affect:** system/
**Dependencies:** None (base library)

---

### 3. API Repository (`memogarden-api/`)

**Purpose:** Flask REST API and Semantic API

**Structure:**
```
memogarden-api/
├── api/
│   ├── __init__.py
│   ├── main.py              # Flask app factory
│   ├── config.py            # API configuration
│   ├── exceptions.py         # API exceptions
│   ├── validation.py        # Request validation
│   ├── semantic.py         # Semantic API (/mg endpoint)
│   ├── schemas/            # Pydantic schemas
│   ├── v1/                # REST API v1
│   │   ├── __init__.py
│   │   ├── core/           # Core endpoints
│   │   │   ├── transactions.py
│   │   │   ├── recurrences.py
│   │   │   ├── relations.py
│   │   │   └── context.py
│   │   └── soil/          # Soil endpoints
│   │       └── artifacts.py
│   ├── handlers/           # Semantic API handlers
│   ├── middleware/         # Auth, decorators
│   └── templates/         # HTML templates
├── tests/
│   ├── conftest.py        # Test fixtures
│   ├── test_transactions.py
│   ├── test_recurrences.py
│   ├── test_auth.py
│   ├── test_semantic_api.py
│   ├── test_context.py
│   ├── test_relations_bundle.py
│   ├── test_user_relations.py
│   ├── test_search.py
│   ├── test_track.py
│   ├── test_audit_facts.py
│   ├── test_path_resolution.py
│   ├── test_health_status.py
│   └── README.md
├── pyproject.toml
├── gunicorn.conf.py       # Production server config
└── README.md
```

**Git:** Separate repository
**Commits affect:** api/, tests/
**Dependencies:** memogarden-system

---

## Related Repositories

These are related to MemoGarden but not part of the core system.

### `app-budget/`

**Purpose:** Budget app (Flutter)

**Status:** Future development
**Platforms:** Web + Android

### `memogarden-devcd/`

**Purpose:** Continuous deployment infrastructure

**Contains:**
- `webhook/` - Flask webhook server
- `scripts/` - Installation and deployment
- `systemd/` - Service definitions
- `.github/workflows/` - GitHub Actions

**Use:** Automated deployment to Raspberry Pi

See [deployment.md](deployment.md) for details.

### `memogarden.github.io/`

**Purpose:** Documentation website

**Status:** Future
**Content:** Public documentation site

### `hacm/`

**Purpose:** Headless Agent Credential Manager

**Status:** Separate project
**Relation:** Manages credentials for MemoGarden and other services

---

## Path Conventions

### Repository Root

- **Development:** `/workspaces/memogarden/`
- **Production (RPi):** `/opt/memogarden/`
- **User:** `$HOME/memogarden/`

### Relative Imports

**In memogarden-system:**
```python
from system.core import get_core
from system.config import settings
from system.host.environment import get_db_path
```

**In memogarden-api:**
```python
from system.core import get_core  # from memogarden-system
from api.v1.core import transactions_bp
from api.semantic import semantic_bp
```

---

## Database Paths (RFC-004)

By deployment verb:

| Verb | Soil DB | Core DB |
|------|----------|----------|
| `serve` | `/var/lib/memogarden/soil.db` | `/var/lib/memogarden/core.db` |
| `run` | `~/.local/share/memogarden/soil.db` | `~/.local/share/memogarden/core.db` |
| `deploy` | `/data/soil.db` | `/data/core.db` |

---

## Common Operations

### Running Tests

```bash
# System package tests
cd memogarden-system
poetry run pytest

# API package tests
cd memogarden-api
poetry run pytest
# or use script from root:
./scripts/test.sh
```

### Starting Development Server

```bash
# From root
./scripts/run.sh

# Or directly
cd memogarden-api
poetry run flask run
```

### Git Workflow

```bash
# Always verify repository before committing
pwd                    # Check directory
git status --short      # Check what changes

# Commit in correct repository
cd memogarden-api      # or memogarden-system
git add .
git commit -m "message"
```

---

## See Also

- [AGENTS.md](/AGENTS.md) - Quick reference for AI agents
- [quickstart.md](quickstart.md) - Getting started
- [deployment.md](deployment.md) - Deployment guide
- [configuration.md](configuration.md) - Configuration reference
