# RFC-004: Package Structure & Deployment

**Version:** 2.0  
**Status:** Draft  
**Author:** MemoGarden Project  
**Created:** 2026-01-30  
**Updated:** 2026-02-02

## Abstract

This RFC specifies the package structure for MemoGarden's codebase and how development artifacts map to deployed systems. MemoGarden uses explicit command verbs (`serve`, `run`, `deploy`) to determine configuration sources and file locations, with operator-declared resource profiles controlling runtime behavior.

## Motivation

RFC-001 defines security architecture but does not specify:
- How source code is organized in the repository
- How Python packages are structured and distributed
- Where files live after installation per command verb
- How resource profiles affect configuration
- Schema deployment and access patterns

This RFC fills those gaps, enabling consistent development and deployment practices.

**Related:** RFC-006 specifies runtime operations and the installation process. This document focuses on static structure.

---

## 1. Package Architecture

### 1.1 Core Principles

1. **Unified System Package**: Soil and Core are layers within one system, not separate products
2. **Minimal Dependencies**: Core system depends only on Python stdlib
3. **Verb-Based Deployment**: Command verb determines config location and defaults
4. **Schema Bundling**: Schemas distributed as package resources, not separate files
5. **Clear Boundaries**: Each package has well-defined responsibility and dependencies

### 1.2 Package Hierarchy

```
memogarden-system     (core functionality)
    â†“ depends on
memogarden-api        (HTTP interface)
    â†“ used by
applications          (budget app, etc.)
```

---

## 2. Development Structure

### 2.1 Repository Layout

```
/memogarden/                          # Git repository root
â”‚
â”œâ”€â”€ memogarden-system/                # Python package: core system
â”‚   â”œâ”€â”€ pyproject.toml
â”‚   â”œâ”€â”€ system/                       # Import as "system"
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ soil/                     # Immutable record layer
â”‚   â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”‚   â”œâ”€â”€ items.py              # Item CRUD operations
â”‚   â”‚   â”‚   â”œâ”€â”€ relations.py          # SystemRelation operations
â”‚   â”‚   â”‚   â””â”€â”€ database.py           # Soil DB connection
â”‚   â”‚   â”œâ”€â”€ core/                     # Mutable belief layer
â”‚   â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”‚   â”œâ”€â”€ entities.py           # Entity CRUD operations
â”‚   â”‚   â”‚   â”œâ”€â”€ relations.py          # UserRelation operations
â”‚   â”‚   â”‚   â”œâ”€â”€ context.py            # ContextFrame operations
â”‚   â”‚   â”‚   â””â”€â”€ database.py           # Core DB connection
â”‚   â”‚   â”œâ”€â”€ host/                     # OS interface abstraction
â”‚   â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”‚   â”œâ”€â”€ environment.py        # Path resolution
â”‚   â”‚   â”‚   â”œâ”€â”€ filesystem.py         # File operations
â”‚   â”‚   â”‚   â”œâ”€â”€ supervision.py        # Readiness signaling
â”‚   â”‚   â”‚   â””â”€â”€ time.py               # Time utilities
â”‚   â”‚   â”œâ”€â”€ schemas/                  # Bundled schemas (copied during build)
â”‚   â”‚   â”‚   â”œâ”€â”€ sql/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ soil.sql
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ core.sql
â”‚   â”‚   â”‚   â””â”€â”€ types/
â”‚   â”‚   â”‚       â”œâ”€â”€ items/
â”‚   â”‚   â”‚       â””â”€â”€ entities/
â”‚   â”‚   â”œâ”€â”€ schemas.py                # Schema access utilities
â”‚   â”‚   â””â”€â”€ utils/                    # Shared utilities
â”‚   â”‚       â”œâ”€â”€ __init__.py
â”‚   â”‚       â”œâ”€â”€ uid.py                # UUID generation
â”‚   â”‚       â”œâ”€â”€ hashing.py            # Hash chain utilities
â”‚   â”‚       â””â”€â”€ validation.py         # JSON Schema validation
â”‚   â””â”€â”€ tests/
â”‚
â”œâ”€â”€ api/                              # Python package: HTTP API
â”‚   â”œâ”€â”€ pyproject.toml
â”‚   â”œâ”€â”€ api/                          # Import as "api"
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ main.py                   # FastAPI app factory
â”‚   â”‚   â”œâ”€â”€ v1/                       # API version 1
â”‚   â”‚   â”‚   â”œâ”€â”€ soil/                 # Soil endpoints
â”‚   â”‚   â”‚   â””â”€â”€ core/                 # Core endpoints
â”‚   â”‚   â”œâ”€â”€ middleware/               # Auth, validation
â”‚   â”‚   â””â”€â”€ schemas/                  # Request/response schemas
â”‚   â””â”€â”€ tests/
â”‚
â”œâ”€â”€ schemas/                          # Schema source (copied during build)
â”‚   â”œâ”€â”€ sql/
â”‚   â”‚   â”œâ”€â”€ soil.sql
â”‚   â”‚   â””â”€â”€ core.sql
â”‚   â””â”€â”€ types/
â”‚       â”œâ”€â”€ items/
â”‚       â”‚   â”œâ”€â”€ email.schema.json
â”‚       â”‚   â””â”€â”€ note.schema.json
â”‚       â””â”€â”€ entities/
â”‚           â”œâ”€â”€ artifact.schema.json
â”‚           â””â”€â”€ transaction.schema.json
â”‚
â”œâ”€â”€ providers/                        # Optional provider implementations
â”‚   â””â”€â”€ <provider-name>/
â”‚       â”œâ”€â”€ pyproject.toml
â”‚       â””â”€â”€ <provider>/
â”‚
â”œâ”€â”€ apps/                             # Optional example applications
â”‚   â””â”€â”€ <app-name>/
â”‚
â”œâ”€â”€ scripts/                          # Development utilities
â”œâ”€â”€ docs/                             # Documentation, RFCs
â””â”€â”€ README.md
```

### 2.2 Import Patterns

```python
# Within system package
from system.soil import Item, SystemRelation, Soil
from system.core import Entity, UserRelation, Core
from system.host.environment import get_data_dir, resolve_context
from system.schemas import get_sql_schema, get_type_schema

# From API package
from system.soil import Item, Soil
from system.core import Entity, Core

# From provider package
from system.soil import Item, Soil
from system.host.environment import get_data_dir
```

### 2.3 Package Dependencies

```
memogarden-system:
  - Python >=3.9
  - No external dependencies (stdlib only)

memogarden-api:
  - memogarden-system
  - FastAPI
  - pydantic
  - uvicorn (ASGI server)

<provider>:
  - memogarden-system
  - Provider-specific dependencies
```

---

## 3. Deployment Mapping

### 3.1 Command Verbs and Configuration Sources

MemoGarden uses explicit command verbs to determine configuration locations:

| Verb | Config Source | Use Case |
|------|--------------|----------|
| `serve` | `/etc/memogarden/config.toml` | System daemon (systemd-managed) |
| `run` | `~/.config/memogarden/config.toml` | User process (development, personal use) |
| `deploy` | Environment variables or `/config/config.toml` | Container (orchestrator-managed) |

**Override:** All verbs accept `--config <path>` to override default location.

### 3.2 Installation Locations by Verb

#### serve (System Daemon)

| Component | Installation Path | Method |
|-----------|-------------------|--------|
| Binary | `/opt/memogarden/bin/memogarden` | Copied by installer |
| Python packages | `/opt/memogarden/venv/lib/python3.x/site-packages/` | venv + pip |
| Databases | `/var/lib/memogarden/soil.db`, `core.db` | Auto-created on init |
| Config | `/etc/memogarden/config.toml` | Created by installer |
| Logs | `/var/log/memogarden/` | Created by installer |
| systemd units | `/etc/systemd/system/memogarden.service` | Copied by installer |
| Runtime state | `/run/memogarden/` | Created by systemd |

**Start command:** `systemctl start memogarden`

#### run (User Process)

| Component | Installation Path | Method |
|-----------|-------------------|--------|
| Binary | `~/.local/bin/memogarden` | Copied by installer |
| Python packages | `~/.local/lib/python3.x/site-packages/` | pip install --user |
| Databases | `~/.local/share/memogarden/soil.db`, `core.db` | Auto-created on init |
| Config | `~/.config/memogarden/config.toml` | Created on first run |
| Logs | `~/.local/state/memogarden/logs/` | Created on first run |
| systemd units | `~/.config/systemd/user/memogarden.service` | Optional |

**Start command:** `memogarden run` or `systemctl --user start memogarden`

#### deploy (Container)

| Component | Installation Path | Method |
|-----------|-------------------|--------|
| Binary | `/usr/local/bin/memogarden` | Copied in Dockerfile |
| Python packages | `/usr/local/lib/python3.x/site-packages/` | pip in Dockerfile |
| Databases | `/data/soil.db`, `core.db` | Volume mount from host |
| Config | `/config/config.toml` or env vars | ConfigMap or env |
| Logs | stdout | Captured by container runtime |

**Start command:** Container entrypoint defaults to `memogarden deploy`

### 3.3 Schema Deployment

Schemas are **bundled into the `memogarden-system` Python package** during build:

```
Source:     /memogarden/schemas/
            â”œâ”€â”€ sql/
            â””â”€â”€ types/

Build:      Copy into package during `python -m build`

Installed:  /opt/memogarden/venv/lib/python3.x/site-packages/system/schemas/
            â”œâ”€â”€ sql/
            â””â”€â”€ types/

Access:     Via importlib.resources in system.schemas module
```

**No separate schema installation required.** Schemas travel with the package.

---

## 4. Path Resolution

### 4.1 Context Resolution

Contexts are determined by command verb, not auto-detection:

```python
def resolve_context(verb: str, config_override: Optional[Path] = None) -> RuntimeContext:
    """
    Map verb to resource locations.
    
    Args:
        verb: Command verb (serve, run, deploy)
        config_override: Optional explicit config path
        
    Returns:
        RuntimeContext with paths, signal method, and defaults
    """
    
    if config_override:
        return RuntimeContext.from_config(config_override)
    
    if verb == "serve":
        return RuntimeContext(
            verb="serve",
            data_dir=Path("/var/lib/memogarden"),
            config_dir=Path("/etc/memogarden"),
            log_dir=Path("/var/log/memogarden"),
            signal_method="systemd"
        )
    
    elif verb == "run":
        return RuntimeContext(
            verb="run",
            data_dir=Path.home() / ".local/share/memogarden",
            config_dir=Path.home() / ".config/memogarden",
            log_dir=Path.home() / ".local/state/memogarden/logs",
            signal_method="stdout"
        )
    
    elif verb == "deploy":
        return RuntimeContext(
            verb="deploy",
            data_dir=Path("/data"),
            config_dir=Path("/config"),
            log_dir=None,  # stdout only
            signal_method="none"  # orchestrator probes /health
        )
```

### 4.2 Path Resolution API

```python
# system/host/environment.py

def get_data_dir(context: RuntimeContext) -> Path:
    """Return data directory for given context."""
    return context.data_dir

def get_db_path(context: RuntimeContext, db_name: str) -> Path:
    """
    Return database file path.
    
    Args:
        context: Runtime context from resolve_context()
        db_name: Database name ('soil' or 'core')
        
    Returns:
        Path to database file
    """
    return context.data_dir / f"{db_name}.db"

def get_config_path(context: RuntimeContext) -> Path:
    """Return config file path."""
    return context.config_dir / "config.toml"

def get_log_dir(context: RuntimeContext) -> Optional[Path]:
    """Return log directory path (None for container)."""
    return context.log_dir
```

---

## 5. Configuration

### 5.1 Config File Format

```toml
# /etc/memogarden/config.toml (serve)
# or ~/.config/memogarden/config.toml (run)

[runtime]
# Resource profile: explicit operator choice
# Options: "embedded" | "standard"
resource_profile = "standard"

# Individual overrides (optional)
# Defaults derived from resource_profile, but can be overridden:
# max_view_entries = 1000          # embedded: 100, standard: 1000
# max_search_results = 100         # embedded: 20, standard: 100
# fossilization_threshold = 0.90   # embedded: 0.80, standard: 0.90
# wal_checkpoint_interval = 60     # embedded: 300, standard: 60
# log_level = "info"               # embedded: "warning", standard: "info"

[paths]
# Path overrides (optional, defaults from verb context)
# data_dir = "/var/lib/memogarden"
# config_dir = "/etc/memogarden"
# log_dir = "/var/log/memogarden"

[network]
bind_address = "127.0.0.1"
bind_port = 8080

[security]
encryption = "disabled"  # "disabled" | "optional" | "required"
# key_file = "/etc/memogarden/encryption.key"  # If encryption enabled
```

### 5.2 Resource Profiles

Resource profiles control operational parameters. Profiles are **operator-declared**, not hardware-detected.

**embedded:**
- Target: Raspberry Pi, embedded systems, low-power hardware (<2GB RAM)
- Characteristics:
  - `max_view_entries`: 100
  - `max_search_results`: 20
  - `fossilization_threshold`: 0.80 (80% capacity)
  - `wal_checkpoint_interval`: 300 seconds
  - `log_level`: "warning"

**standard (default):**
- Target: Laptops, desktops, servers, containers (â‰¥2GB RAM)
- Characteristics:
  - `max_view_entries`: 1000
  - `max_search_results`: 100
  - `fossilization_threshold`: 0.90 (90% capacity)
  - `wal_checkpoint_interval`: 60 seconds
  - `log_level`: "info"

**Setting:** Declared in `config.toml` or via `--resource-profile` flag. Individual parameters can be overridden.

### 5.3 Container Configuration via Environment

Container deployments prefer environment variables over config files:

| Variable | Purpose | Example |
|----------|---------|---------|
| `MEMOGARDEN_RESOURCE_PROFILE` | Set resource profile | `standard` |
| `MEMOGARDEN_BIND_ADDRESS` | Override bind address | `0.0.0.0` |
| `MEMOGARDEN_BIND_PORT` | Override bind port | `8080` |
| `MEMOGARDEN_LOG_LEVEL` | Override log level | `info` |
| `MEMOGARDEN_ENCRYPTION` | Encryption mode | `disabled` |

Environment variables take precedence over config file values.

---

## 6. systemd Unit Templates

### 6.1 System Service Unit

Created at `/etc/systemd/system/memogarden.service` by `memogarden install`:

```ini
[Unit]
Description=MemoGarden Personal Information System
Documentation=https://docs.memogarden.org
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=memogarden
Group=memogarden

# Resource profile read from /etc/memogarden/config.toml
ExecStart=/opt/memogarden/bin/memogarden serve

# Working directory
WorkingDirectory=/var/lib/memogarden

# Restart policy
Restart=on-failure
RestartSec=5s

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/memogarden /var/log/memogarden

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=memogarden

[Install]
WantedBy=multi-user.target
```

**Note:** Resource limits (MemoryMax, CPUQuota) are NOT specified in the unit file. They are applied at runtime based on `resource_profile` in config.toml if needed. See RFC-006 for details.

### 6.2 User Service Unit

Created at `~/.config/systemd/user/memogarden.service` by `memogarden install --user`:

```ini
[Unit]
Description=MemoGarden Personal Information System (User)
Documentation=https://docs.memogarden.org

[Service]
Type=simple

# Resource profile read from ~/.config/memogarden/config.toml
ExecStart=%h/.local/bin/memogarden serve

# Working directory
WorkingDirectory=%h/.local/share/memogarden

# Restart policy
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
```

---

## 7. Package Distribution

### 7.1 Build Process

```bash
# Build memogarden-system
cd memogarden-system
./scripts/copy-schemas.sh  # Copy schemas into package
python -m build
ls dist/  # memogarden_system-0.1.0-py3-none-any.whl

# Build memogarden-api
cd ../api
python -m build
ls dist/  # memogarden_api-0.1.0-py3-none-any.whl
```

### 7.2 Distribution Methods

| Method | Use Case | Command |
|--------|----------|---------|
| **PyPI** | Public release | `pip install memogarden-system` |
| **Private PyPI** | Organization-internal | `pip install --index-url=<url> memogarden-system` |
| **Wheel file** | Air-gapped systems | `pip install memogarden_system-0.1.0-py3-none-any.whl` |
| **Git** | Development | `pip install git+https://github.com/org/memogarden.git#subdirectory=memogarden-system` |

### 7.3 Version Management

```toml
# memogarden-system/pyproject.toml
[project]
name = "memogarden-system"
version = "0.1.0"  # Semantic versioning

# memogarden-api/pyproject.toml
[project]
name = "memogarden-api"
version = "0.1.0"
dependencies = [
    "memogarden-system>=0.1.0,<0.2.0"  # Pin to compatible minor version
]
```

---

## 8. Installation Overview

**Detailed installation procedures are specified in RFC-006 Section 2.** This section provides a brief summary of what gets installed.

### 8.1 System Installation

```bash
sudo memogarden install [--resource-profile {embedded|standard|auto}]
```

Creates:
- Binary at `/opt/memogarden/bin/memogarden`
- Config at `/etc/memogarden/config.toml`
- systemd unit at `/etc/systemd/system/memogarden.service`
- Directories: `/var/lib/memogarden/`, `/var/log/memogarden/`
- Service user `memogarden:memogarden`

### 8.2 User Installation

```bash
memogarden install --user [--resource-profile {embedded|standard|auto}]
```

Creates:
- Binary at `~/.local/bin/memogarden`
- Config at `~/.config/memogarden/config.toml`
- systemd unit at `~/.config/systemd/user/memogarden.service` (optional)
- Directories: `~/.local/share/memogarden/`, `~/.local/state/memogarden/logs/`
- Desktop entry at `~/.local/share/applications/memogarden.desktop` (optional)

### 8.3 Container Build

Dockerfile example:

```dockerfile
FROM python:3.11-slim

# Install MemoGarden
COPY memogarden /usr/local/bin/memogarden
RUN chmod +x /usr/local/bin/memogarden && \
    pip install memogarden-system memogarden-api

# Data volumes
VOLUME ["/data", "/config"]

# Container defaults
ENV MEMOGARDEN_BIND_ADDRESS=0.0.0.0
ENV MEMOGARDEN_BIND_PORT=8080
ENV MEMOGARDEN_RESOURCE_PROFILE=standard

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8080/health || exit 1

# Entry point
ENTRYPOINT ["/usr/local/bin/memogarden"]
CMD ["deploy"]
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# memogarden-system/tests/test_host/test_environment.py

import pytest
from system.host.environment import resolve_context, get_db_path

def test_resolve_context_serve():
    ctx = resolve_context("serve")
    assert ctx.data_dir == Path("/var/lib/memogarden")
    assert ctx.config_dir == Path("/etc/memogarden")
    assert ctx.signal_method == "systemd"

def test_resolve_context_run():
    ctx = resolve_context("run")
    assert ctx.data_dir == Path.home() / ".local/share/memogarden"
    assert ctx.signal_method == "stdout"

def test_get_db_path():
    ctx = resolve_context("serve")
    path = get_db_path(ctx, "soil")
    assert path == Path("/var/lib/memogarden/soil.db")
```

### 9.2 Integration Tests

```python
# memogarden-system/tests/test_integration/test_soil_init.py

import tempfile
from pathlib import Path
from system.soil import Soil
from system.host.environment import RuntimeContext

def test_soil_init_creates_database():
    with tempfile.TemporaryDirectory() as tmpdir:
        ctx = RuntimeContext(
            verb="test",
            data_dir=Path(tmpdir),
            config_dir=Path(tmpdir),
            log_dir=None,
            signal_method="none"
        )
        
        db_path = ctx.data_dir / "soil.db"
        soil = Soil(db_path=db_path)
        
        assert db_path.exists()
        assert soil.conn is not None
```

### 9.3 Verb-Specific Tests

Tests should verify correct behavior for each verb:

```python
@pytest.mark.parametrize("verb,expected_signal", [
    ("serve", "systemd"),
    ("run", "stdout"),
    ("deploy", "none"),
])
def test_context_resolution_per_verb(verb, expected_signal):
    ctx = resolve_context(verb)
    assert ctx.signal_method == expected_signal
```

---

## 10. Migration Path

### 10.1 From v1.0 Structure

v1.0 had profile auto-detection and less explicit verb mapping. Migration:

1. **Update `system.host.environment`** to use verb-based resolution
2. **Remove hardware detection** from profile logic
3. **Update config.toml** to include explicit `resource_profile` parameter
4. **Update systemd units** to use verb commands (`memogarden serve`)
5. **Test installation** on each verb type
6. **Update documentation** (README, installation guides)

### 10.2 Backward Compatibility

Old configs without `resource_profile` default to `standard`:

```python
def load_config(path: Path) -> Config:
    """Load config with backward compatibility."""
    config = toml.load(path)
    
    if "runtime" not in config:
        config["runtime"] = {}
    
    if "resource_profile" not in config["runtime"]:
        # Legacy config: default to standard
        config["runtime"]["resource_profile"] = "standard"
    
    return Config(**config)
```

---

## 11. Open Questions

1. **Multi-package versioning**: Should memogarden-system and memogarden-api share version numbers or evolve independently?
   - **Recommendation:** Independent versions, with API declaring compatible system version range

2. **Schema versioning**: How to handle schema evolution across package versions?
   - **Deferred:** Will address in Schema Migration RFC (future work)

3. **Provider registration**: Should providers be discovered via entry points or explicit configuration?
   - **Recommendation:** Entry points for discovery, config for enabling/disabling

4. **Wheel bundling**: Should we provide meta-packages that install system + api together?
   - **Recommendation:** Yes, create `memogarden` meta-package for convenience

5. **Offline installation**: What's the recommended process for air-gapped environments?
   - **Answered:** Wheel file distribution (Section 7.2)

---

## 12. Future Work

### 12.1 Schema Migrations

Alembic-style migration system:

```
system/schemas/migrations/
â”œâ”€â”€ 001_initial.sql
â”œâ”€â”€ 002_add_fidelity.sql
â””â”€â”€ 003_add_context_frames.sql
```

### 12.2 Provider Plugin System

Entry point-based provider discovery:

```toml
# provider package pyproject.toml
[project.entry-points."memogarden.providers"]
gmail = "gmail_provider:GmailProvider"
```

### 12.3 Multi-Platform Binary Distribution

- Pre-built binaries for Linux (x86_64, ARM)
- macOS packages (.pkg, Homebrew)
- Windows installers (.msi, chocolatey)

---

## References

- RFC-001 v4: Security & Operations Architecture
- RFC-002 v5: Relation Time Horizon & Fossilization
- RFC-003 v2: Context Capture Mechanism
- RFC-006 v1: Runtime Operations & Installation (this document's companion)
- PRD v0.10.0: MemoGarden Personal Information System
- Python Packaging User Guide: https://packaging.python.org/

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-30 | Initial draft |
| 2.0 | 2026-02-02 | **Major revision**: Verb-based deployment, explicit resource profiles, removed hardware detection, added systemd unit templates, clarified config structure |

---

**Status:** Draft  
**Next Steps:**
1. Review and approve verb-based deployment model
2. Review resource profile declarations (embedded/standard)
3. Implement `system.host.environment.resolve_context()`
4. Update build scripts for schema bundling
5. Test installation on all verbs
6. See RFC-006 for runtime operations and installation procedures

---

**END OF RFC**
