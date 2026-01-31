# RFC-004 Implementation Plan (Simplified)

**Version:** 1.1
**Status:** Draft
**Created:** 2026-01-31
**Last Updated:** 2026-01-31
**Author:** MemoGarden Project

## Executive Summary

Simplified implementation plan for achieving RFC-004 (Package Structure & Deployment) compliance.

**Approach:** Config-based path resolution with environment variable overrides. Profile detection deferred.

**Current Compliance:** ~50%
- ✅ Core package structure (system.soil, system.core, system.utils)
- ✅ Provider packages (mbox-importer, gmail-importer)
- ✅ Repository layout matches RFC-004 Section 2.1
- ❌ Schema bundling (system.schemas missing)
- ❌ Config-based path resolution (system.host incomplete)

**Target Compliance:** ~80% (simplified - defer profile detection)

**Estimated Effort:** 1 day for core functionality

---

## Simplified Approach

### Philosophy

**KISS Principle:** Keep it simple, config-based, extensible later.

1. **Config-based paths** - Use environment variables for path overrides
2. **Simple defaults** - Use sensible defaults (`./{layer}.db`)
3. **Defer complexity** - Profile auto-detection can wait
4. **Future-proof** - Structure allows config files, TOML, etc. later

### What We're NOT Doing (Yet)

- ❌ Profile auto-detection (detecting Docker, systemd, etc.)
- ❌ Profile enum (DEVICE, SYSTEM, PERSONAL, CONTAINER)
- ❌ Complex profile-specific logic
- ❌ CLI initialization module
- ❌ Multiple config sources (env vars, TOML, YAML)

These can be added later without breaking the simple approach.

---

## Current State Analysis

### What's Already Implemented ✅

| RFC-004 Requirement | Status | Location |
|-------------------|--------|----------|
| Repository structure (Section 2.1) | ✅ Complete | `/memogarden/memogarden-system/` with `system/` package |
| `system/soil/` layer | ✅ Complete | database.py with Item, SystemRelation, Soil classes |
| `system/core/` layer | ✅ Complete | entity.py, database.py with Core class |
| `system/utils/` utilities | ✅ Complete | uid.py, hashing.py |
| `system/host/` directory | ⚠️ Partial | Exists but needs path resolution functions |
| `system/schemas/` directory | ⚠️ Partial | Files exist but not bundled as resources |

### What's Missing ❌

| RFC-004 Requirement | Priority | Status |
|-------------------|----------|--------|
| **Config-based path resolution** (get_db_path with env var support) | HIGH | Not implemented |
| **system/schemas.py** (get_sql_schema) | HIGH | Not implemented |
| **Schema bundling** (copy schemas to package) | MEDIUM | Manual step for now |
| **Default paths in Soil/Core** | HIGH | Not implemented |

### Partial Implementation Details

**system/host/ exists with:**
- ✅ `environment.py` - Only has `get_env()` function
- ✅ `filesystem.py` - Has `resolve_path()`, `ensure_dir()` functions
- ✅ `time.py` - Has `now_utc()`, `now_iso()` functions
- ❌ **Missing**: `get_db_path()` function with env var support

**system/schemas/ exists with:**
- ✅ SQL schemas: `soil.sql`, `core.sql`
- ✅ JSON schemas: email, note, message, transaction
- ❌ **Missing**: `schemas.py` module for runtime access

---

## Implementation Plan

### Phase 1: Config-Based Path Resolution (HIGH PRIORITY - 1 hour)

**Goal:** Simple environment variable-based path resolution.

#### 1.1: Implement get_db_path() Function

**File:** `memogarden-system/system/host/environment.py` (extend existing)

```python
from pathlib import Path
import os

def get_db_path(layer: str) -> Path:
    """Get database path for Soil or Core with env var override.

    Resolution order:
        1. MEMOGARDEN_{LAYER}_DB env var (explicit override)
        2. MEMOGARDEN_DATA_DIR env var (shared data directory)
        3. Current directory (./{layer}.db)

    Args:
        layer: 'soil' or 'core' (case-insensitive)

    Returns:
        Path to database file

    Raises:
        ValueError: If layer is not 'soil' or 'core'

    Examples:
        >>> # Explicit override
        >>> os.environ['MEMOGARDEN_SOIL_DB'] = '/custom/soil.db'
        >>> get_db_path('soil')
        Path('/custom/soil.db')

        >>> # Shared data directory
        >>> os.environ['MEMOGARDEN_DATA_DIR'] = '/data'
        >>> get_db_path('soil')
        Path('/data/soil.db')

        >>> # Default (current directory)
        >>> get_db_path('soil')
        Path('./soil.db')
    """
    layer = layer.lower()
    if layer not in ('soil', 'core'):
        raise ValueError(f"Invalid layer: {layer}. Must be 'soil' or 'core'.")

    # 1. Explicit database path override
    env_var = f"MEMOGARDEN_{layer.upper()}_DB"
    if path := os.getenv(env_var):
        return Path(path)

    # 2. Shared data directory
    if data_dir := os.getenv("MEMOGARDEN_DATA_DIR"):
        return Path(data_dir) / f"{layer}.db"

    # 3. Default to current directory
    return Path(f"{layer}.db")
```

#### 1.2: Update Soil to Use Config-Based Paths

**File:** `memogarden-system/system/soil/database.py`

Update Soil.__init__:

```python
class Soil:
    """Soil database for immutable Items and System Relations."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize Soil database with config-based default path.

        Args:
            db_path: Optional explicit path override. If None, uses get_db_path('soil')
                      which checks environment variables and defaults to './soil.db'

        Examples:
            >>> # Use default (respects env vars, defaults to ./soil.db)
            >>> soil = Soil()

            >>> # Explicit path
            >>> soil = Soil('/custom/soil.db')

            >>> # Via environment variable
            >>> os.environ['MEMOGARDEN_SOIL_DB'] = '/data/soil.db'
            >>> soil = Soil()  # Uses env var
        """
        if db_path is None:
            # Import here to avoid circular dependency
            from system.host.environment import get_db_path
            db_path = get_db_path("soil")

        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
```

#### 1.3: Update Core to Use Config-Based Paths

**File:** `memogarden-system/system/core/database.py`

Apply same pattern to Core class.

---

### Phase 2: Schema Access Utilities (HIGH PRIORITY - 0.5 hour)

**Goal:** Simple schema access without full bundling complexity.

#### 2.1: Implement system.schemas Module

**File:** `memogarden-system/system/schemas.py` (new file)

```python
"""Schema access utilities for MemoGarden System.

Provides runtime access to SQL schemas. Falls back to file reading if
bundled resources are not available (development mode).

Future: Can be extended to use importlib.resources for full RFC-004 compliance.
"""

from __future__ annotations

from pathlib import Path
import sys

def get_sql_schema(layer: str) -> str:
    """Get SQL schema for Soil or Core.

    Resolution order:
        1. Bundled resources (importlib.resources) - when installed as package
        2. Source tree (system/schemas/sql/) - development mode

    Args:
        layer: 'soil' or 'core'

    Returns:
        SQL schema as string

    Raises:
        FileNotFoundError: If schema file not found

    Examples:
        >>> schema = get_sql_schema('soil')
        >>> conn.executescript(schema)
    """
    layer = layer.lower()
    if layer not in ('soil', 'core'):
        raise ValueError(f"Invalid layer: {layer}. Must be 'soil' or 'core'.")

    # Try bundled resources first (when installed as package)
    try:
        from importlib.resources import files
        ref = files("system") / "schemas" / "sql" / f"{layer}.sql"
        return ref.read_text()
    except Exception:
        # Fall back to source tree (development mode)
        schema_path = Path(__file__).parent / "schemas" / "sql" / f"{layer}.sql"
        if not schema_path.exists():
            raise FileNotFoundError(
                f"SQL schema for '{layer}' not found. "
                f"Tried bundled resources and {schema_path}"
            )
        return schema_path.read_text()
```

#### 2.2: Update Soil/Core to Use Schema Access

**File:** `memogarden-system/system/soil/database.py`

Update init_schema():

```python
def init_schema(self):
    """Initialize database schema from bundled or source schemas."""
    from system.schemas import get_sql_schema

    schema_sql = get_sql_schema('soil')
    conn = self._get_connection()
    conn.executescript(schema_sql)
    conn.commit()
```

Apply same pattern to Core.

---

### Phase 3: Update Package Exports (LOW PRIORITY - 15 minutes)

**Goal:** Export new functions from system.host.

**File:** `memogarden-system/system/host/__init__.py`

```python
"""Host interface for MemoGarden System.

Provides abstractions for host platform operations (filesystem, environment, time).
"""

from .filesystem import resolve_path, ensure_dir
from .environment import get_env, get_db_path
from .time import now_utc, now_iso

__all__ = [
    # Filesystem
    "resolve_path",
    "ensure_dir",
    # Environment
    "get_env",
    "get_db_path",
    # Time
    "now_utc",
    "now_iso",
]
```

---

## Extended Implementation (Deferred)

The following can be added later without breaking the simple approach:

### Future: Config File Support

Add support for reading from config files (TOML, YAML, INI):

```python
def _read_config_file():
    """Read config from ~/.config/memogarden/config.toml (if exists)."""
    import toml
    config_path = Path.home() / ".config" / "memogarden" / "config.toml"
    if config_path.exists():
        return toml.load(config_path)
    return {}
```

### Future: Profile Detection

Add profile auto-detection (Docker, systemd, etc.):

```python
def detect_profile():
    """Auto-detect deployment profile."""
    if Path("/.dockerenv").exists():
        return "container"
    if os.geteuid() != 0 and Path("/var/lib/memogarden").exists():
        return "system"
    return "personal"
```

### Future: CLI Module

Add command-line initialization:

```python
def init_databases():
    """Initialize Soil and Core databases with schema."""
    from system.host.environment import get_db_path
    from system.soil import Soil
    from system.core import Core

    for layer in ['soil', 'core']:
        db_path = get_db_path(layer)
        db = Soil(db_path) if layer == 'soil' else Core(db_path)
        db.init_schema()
        db.close()
```

---

#### B.1: Implement Schema Access Module

**File:** `memogarden-system/system/schemas.py` (new file)

```python
"""Schema access utilities for MemoGarden System.

Provides runtime access to bundled SQL and JSON schemas via importlib.resources
per RFC-004 Section 5.2.
"""

from __future__ annotations

import json
from pathlib import Path

try:
    from importlib.resources import files  # Python 3.9+
except ImportError:
    from importlib_resources import files  # Backport

def get_sql_schema(layer: str) -> str:
    """Get SQL schema for Soil or Core from bundled resources.

    Args:
        layer: 'soil' or 'core'

    Returns:
        SQL schema as string

    Raises:
        FileNotFoundError: If schema file not found in package

    Example:
        >>> schema = get_sql_schema('soil')
        >>> conn.executescript(schema)
    """
    try:
        ref = files("system") / "schemas" / "sql" / f"{layer}.sql"
        return ref.read_text()
    except Exception as e:
        raise FileNotFoundError(
            f"SQL schema for '{layer}' not found in bundled resources. "
            f"Ensure memogarden-system package is installed. Error: {e}"
        )

def get_type_schema(category: str, type_name: str) -> dict:
    """Get JSON Schema for item or entity type from bundled resources.

    Args:
        category: 'items' or 'entities'
        type_name: Type name without .schema.json suffix

    Returns:
        JSON Schema as dict

    Raises:
        FileNotFoundError: If schema file not found

    Example:
        >>> schema = get_type_schema('items', 'email')
        >>> data = {"description": "Test"}
        >>> jsonschema.validate(data, schema)
    """
    try:
        ref = files("system") / "schemas" / "types" / category / f"{type_name}.schema.json"
        return json.loads(ref.read_text())
    except Exception as e:
        raise FileNotFoundError(
            f"JSON schema for '{type_name}' not found in {category}. "
            f"Error: {e}"
        )

def list_type_schemas(category: str) -> list[str]:
    """List available type schemas in category.

    Args:
        category: 'items' or 'entities'

    Returns:
        List of type names (without .schema.json suffix)
    """
    try:
        schema_dir = files("system") / "schemas" / "types" / category
        schemas = []

        # Handle both directory and zip (when installed)
        if hasattr(schema_dir, "is_dir") and schema_dir.is_dir():
            for file in schema_dir.iterdir():
                if file.name.endswith('.schema.json'):
                    schemas.append(file.name.replace('.schema.json', ''))
        elif hasattr(schema_dir, "iterdir"):
            for file in schema_dir.iterdir():
                if file.name.endswith('.schema.json'):
                    schemas.append(file.name.replace('.schema.json', ''))

        return sorted(schemas)
    except Exception:
        return []
```

#### B.2: Update Soil/Core to Use Bundled Schemas

**File:** `memogarden-system/system/soil/database.py`

Update init_schema() to use bundled schemas:

```python
def init_schema(self):
    """Initialize database schema from bundled resources."""
    from system.schemas import get_sql_schema

    schema_sql = get_sql_schema('soil')
    conn = self._get_connection()
    conn.executescript(schema_sql)
    conn.commit()
```

Apply same pattern to Core.

#### B.3: Configure Package Data in pyproject.toml

**File:** `memogarden-system/pyproject.toml`

Add package-data configuration:

```toml
[tool.poetry]
name = "memogarden-system"
version = "0.1.0"
...
packages = [{include = "system"}]

[tool.poetry.build]
# Include schema files in package
include = [
    "system/schemas/**/*.sql",
    "system/schemas/**/*.json",
]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

---

## Timeline & Effort

| Phase | Duration | Dependencies | Complexity |
|-------|----------|--------------|------------|
| 1: Config-Based Path Resolution | 1 hour | None | Low (env var + defaults) |
| 2: Schema Access Utilities | 0.5 hour | None | Low (file reading, importlib optional) |
| 3: Update Package Exports | 0.25 hour | Phase 1 | Trivial (update __init__.py) |
| **Total** | **2 hours** | | **Low complexity** |

---

## Environment Variables

Supported environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `MEMOGARDEN_SOIL_DB` | Explicit Soil database path | `/data/soil.db` |
| `MEMOGARDEN_CORE_DB` | Explicit Core database path | `/data/core.db` |
| `MEMOGARDEN_DATA_DIR` | Shared data directory (both databases) | `/var/lib/memogarden` |

Resolution order:
1. Layer-specific override (`MEMOGARDEN_{LAYER}_DB`)
2. Shared directory (`MEMOGARDEN_DATA_DIR`)
3. Current directory default (`./{layer}.db`)

---

## Design Principles

1. **Config over Code** - Use environment variables for configuration
2. **Simple Defaults** - Use `./{layer}.db` if no config provided
3. **Future-Proof** - Structure allows TOML/YAML config files later
4. **No Magic** - Paths are explicit and traceable
5. **Backward Compatible** - Explicit `db_path` parameter still works

---

## Open Questions & Decisions

### Q1: Should we support config files?

**Decision:** Not yet. Environment variables are sufficient for now. Config files (TOML/YAML) can be added later without breaking the env var approach.

### Q2: Should we auto-detect profiles?

**Decision:** Not yet. Profile auto-detection (Docker, systemd, etc.) adds complexity. Explicit config via env vars is simpler and more predictable.

### Q3: Should migrations be bundled?

**Decision:** No. Migrations stay as SQL files in source tree. They can be bundled later if needed.

---

## Success Criteria

Phase 1 is complete when:
- [ ] `get_db_path('soil')` returns `./soil.db` by default
- [ ] `MEMOGARDEN_SOIL_DB=/custom/soil.db` overrides default
- [ ] `MEMOGARDEN_DATA_DIR=/data` applies to both databases
- [ ] Soil() and Core() use config-based paths automatically

Phase 2 is complete when:
- [ ] `get_sql_schema('soil')` returns soil.sql content
- [ ] Works in development mode (file reading)
- [ ] Works in installed mode (importlib.resources when bundled)
- [ ] Fallback mechanism works correctly

Phase 3 is complete when:
- [ ] `from system.host import get_db_path` works
- [ ] `from system.schemas import get_sql_schema` works
- [ ] All existing tests still pass
- [ ] No breaking changes to existing API

---

## Rollback Plan

If implementation breaks existing functionality:

1. Remove `get_db_path()` from system.host.__init__.py exports
2. Remove system.schemas.py module
3. Revert Soil/Core __init__ to require explicit db_path parameter
4. Delete updated code

All changes are additive - removing them restores previous behavior.

---

## Future Enhancements (Deferred)

### Config File Support

Add support for reading config from `~/.config/memogarden/config.toml`:

```toml
[databases]
soil_db = "/data/soil.db"
core_db = "/data/core.db"
# Or shared:
data_dir = "/var/lib/memogarden"
```

### Profile Auto-Detection

Auto-detect deployment environment:

```python
def detect_profile() -> str:
    """Auto-detect deployment profile."""
    if Path("/.dockerenv").exists():
        return "container"
    if Path("/var/lib/memogarden").exists():
        return "system"
    return "personal"
```

### CLI Initialization

Add `python -m system.cli init` command:

```bash
python -m system.cli init  # Initialize databases in config-based paths
```

---

## Next Steps

1. ✅ **Plan updated** - Simplified approach ready for review
2. **Await approval** - Don't start implementation yet
3. **Tackle other priorities** - Address these tasks when ready

---

**Status:** Plan updated, awaiting approval
**Estimated Effort:** 2 hours when ready to implement
**Target Compliance:** ~80% (simplified approach, defer profile detection)
