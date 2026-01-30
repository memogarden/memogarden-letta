# RFC-004: Package Structure & Deployment

**Version:** 1.0  
**Status:** Draft  
**Author:** MemoGarden Project  
**Created:** 2026-01-30

## Abstract

This RFC specifies the package structure for MemoGarden's codebase and how development artifacts map to deployed systems across different profiles (Device, System, Personal, Container). It complements RFC-001 by providing implementation details for software distribution and installation.

## Motivation

RFC-001 defines security architecture and deployment profiles but does not specify:
- How source code is organized in the repository
- How Python packages are structured and distributed
- Where files live after installation per profile
- How runtime path resolution works across profiles
- Schema deployment and access patterns

This RFC fills those gaps, enabling consistent development and deployment practices.

---

## 1. Package Architecture

### 1.1 Core Principles

1. **Unified System Package**: Soil and Core are layers within one system, not separate products
2. **Minimal Dependencies**: Core system depends only on Python stdlib
3. **Profile-Agnostic Code**: Path resolution happens at runtime based on detected/configured profile
4. **Schema Bundling**: Schemas distributed as package resources, not separate files
5. **Clear Boundaries**: Each package has well-defined responsibility and dependencies

### 1.2 Package Hierarchy

```
memogarden-system     (core functionality)
    ↓ depends on
memogarden-api        (HTTP interface)
    ↓ used by
applications          (budget app, etc.)
```

---

## 2. Development Structure

### 2.1 Repository Layout

```
/memogarden/                          # Git repository root
│
├── memogarden-system/                # Python package: core system
│   ├── pyproject.toml
│   ├── system/                       # Import as "system"
│   │   ├── __init__.py
│   │   ├── soil/                     # Immutable record layer
│   │   │   ├── __init__.py
│   │   │   ├── items.py              # Item CRUD operations
│   │   │   ├── relations.py          # SystemRelation operations
│   │   │   └── database.py           # Soil DB connection
│   │   ├── core/                     # Mutable belief layer
│   │   │   ├── __init__.py
│   │   │   ├── entities.py           # Entity CRUD operations
│   │   │   ├── relations.py          # UserRelation operations
│   │   │   ├── context.py            # ContextFrame operations
│   │   │   └── database.py           # Core DB connection
│   │   ├── host/                     # OS interface abstraction
│   │   │   ├── __init__.py
│   │   │   ├── environment.py        # Path resolution, profile detection
│   │   │   ├── filesystem.py         # File operations
│   │   │   ├── time.py               # Time utilities
│   │   │   └── process.py            # Process management
│   │   ├── schemas/                  # Bundled schemas (copied during build)
│   │   │   ├── sql/
│   │   │   │   ├── soil.sql
│   │   │   │   └── core.sql
│   │   │   └── types/
│   │   │       ├── items/
│   │   │       └── entities/
│   │   ├── schemas.py                # Schema access utilities
│   │   └── utils/                    # Shared utilities
│   │       ├── __init__.py
│   │       ├── uid.py                # UUID generation
│   │       ├── hashing.py            # Hash chain utilities
│   │       └── validation.py         # JSON Schema validation
│   └── tests/
│
├── api/                              # Python package: HTTP API
│   ├── pyproject.toml
│   ├── api/                          # Import as "api"
│   │   ├── __init__.py
│   │   ├── main.py                   # Flask/FastAPI app factory
│   │   ├── v1/                       # API version 1
│   │   │   ├── soil/                 # Soil endpoints
│   │   │   └── core/                 # Core endpoints
│   │   ├── middleware/               # Auth, validation
│   │   └── schemas/                  # Request/response schemas
│   └── tests/
│
├── schemas/                          # Schema source (copied during build)
│   ├── sql/
│   │   ├── soil.sql
│   │   └── core.sql
│   └── types/
│       ├── items/
│       │   ├── email.schema.json
│       │   └── note.schema.json
│       └── entities/
│           ├── artifact.schema.json
│           └── transaction.schema.json
│
├── providers/                        # Optional provider implementations
│   └── <provider-name>/
│       ├── pyproject.toml
│       └── <provider>/
│
├── apps/                             # Optional example applications
│   └── <app-name>/
│
├── scripts/                          # Development utilities
├── docs/                             # Documentation, RFCs
└── README.md
```

### 2.2 Import Patterns

```python
# Within system package
from system.soil import Item, SystemRelation, Soil
from system.core import Entity, UserRelation, Core
from system.host.environment import get_data_dir, detect_profile
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
  - Flask or FastAPI
  - pydantic

<provider>:
  - memogarden-system
  - Provider-specific dependencies
```

---

## 3. Deployment Mapping

### 3.1 Installation Locations by Profile

#### Device Profile

| Component | Installation Path | Method |
|-----------|-------------------|--------|
| Python packages | `/opt/memogarden/venv/lib/python3.x/site-packages/` | venv + pip |
| Databases | `/var/lib/memogarden/soil.db`, `core.db` | Auto-created on init |
| Config | `/etc/memogarden/config.toml` | Created by installer |
| Logs | `/var/log/memogarden/` | Created by installer |
| systemd units | `/etc/systemd/system/memogarden-*.service` | Copied by installer |
| Runtime state | `/run/memogarden/` | Created by systemd |

#### System Profile

| Component | Installation Path | Method |
|-----------|-------------------|--------|
| Python packages | `/opt/memogarden/venv/lib/python3.x/site-packages/` | venv + pip |
| Databases | `/var/lib/memogarden/soil.db`, `core.db` | Auto-created on init |
| Config | `/etc/memogarden/config.toml` | Created by installer |
| Logs | `/var/log/memogarden/` | Created by installer |
| systemd units | `/etc/systemd/system/memogarden-*.service` | Copied by installer |

#### Personal Profile

| Component | Installation Path | Method |
|-----------|-------------------|--------|
| Python packages | `~/.local/lib/python3.x/site-packages/` | pip install --user |
| Databases | `~/.local/share/memogarden/soil.db`, `core.db` | Auto-created on init |
| Config | `~/.config/memogarden/config.toml` | Created on first run |
| Logs | `~/.local/state/memogarden/logs/` | Created on first run |
| systemd units | `~/.config/systemd/user/memogarden-*.service` | Copied by installer |

#### Container Profile

| Component | Installation Path | Method |
|-----------|-------------------|--------|
| Python packages | `/usr/local/lib/python3.x/site-packages/` | pip in Dockerfile |
| Databases | `/data/soil.db`, `core.db` | Volume mount from host |
| Config | `/config/config.toml` or env vars | ConfigMap or env |
| Logs | stdout | Captured by container runtime |

### 3.2 Schema Deployment

Schemas are **bundled into the `memogarden-system` Python package** during build:

```
Source:     /memogarden/schemas/
            ├── sql/
            └── types/

Build:      Copy into package during `python -m build`

Installed:  /opt/memogarden/venv/lib/python3.x/site-packages/system/schemas/
            ├── sql/
            └── types/

Access:     Via importlib.resources in system.schemas module
```

**No separate schema installation required.** Schemas travel with the package.

---

## 4. Path Resolution

### 4.1 Profile Detection

Profiles are detected at runtime via `system.host.environment.detect_profile()`:

```python
def detect_profile() -> Profile:
    """Auto-detect deployment profile.
    
    Priority:
    1. MEMOGARDEN_PROFILE env var (explicit override)
    2. Container indicators (/.dockerenv, K8S env vars)
    3. System service indicators (running as service user, /var/lib/memogarden exists)
    4. Personal (default)
    """
    if profile := os.getenv("MEMOGARDEN_PROFILE"):
        return Profile(profile)
    
    if Path("/.dockerenv").exists() or os.getenv("KUBERNETES_SERVICE_HOST"):
        return Profile.CONTAINER
    
    if os.geteuid() != 0 and Path("/var/lib/memogarden").exists():
        return Profile.SYSTEM
    
    return Profile.PERSONAL
```

### 4.2 Path Resolution API

```python
# system/host/environment.py

def get_data_dir(profile: Profile = None) -> Path:
    """Get data directory for databases.
    
    Checks (in order):
    1. MEMOGARDEN_DATA_DIR env var
    2. Profile-specific default
    """
    if profile is None:
        profile = detect_profile()
    
    if path := os.getenv("MEMOGARDEN_DATA_DIR"):
        return Path(path)
    
    return {
        Profile.DEVICE: Path("/var/lib/memogarden"),
        Profile.SYSTEM: Path("/var/lib/memogarden"),
        Profile.PERSONAL: Path.home() / ".local" / "share" / "memogarden",
        Profile.CONTAINER: Path("/data"),
    }[profile]

def get_config_dir(profile: Profile = None) -> Path:
    """Get config directory."""
    if profile is None:
        profile = detect_profile()
    
    if path := os.getenv("MEMOGARDEN_CONFIG_DIR"):
        return Path(path)
    
    return {
        Profile.DEVICE: Path("/etc/memogarden"),
        Profile.SYSTEM: Path("/etc/memogarden"),
        Profile.PERSONAL: Path.home() / ".config" / "memogarden",
        Profile.CONTAINER: Path("/config"),
    }[profile]

def get_log_dir(profile: Profile = None) -> Path | None:
    """Get log directory. Returns None for Container (uses stdout)."""
    if profile is None:
        profile = detect_profile()
    
    if path := os.getenv("MEMOGARDEN_LOG_DIR"):
        return Path(path)
    
    if profile == Profile.CONTAINER:
        return None  # Use stdout
    
    return {
        Profile.DEVICE: Path("/var/log/memogarden"),
        Profile.SYSTEM: Path("/var/log/memogarden"),
        Profile.PERSONAL: Path.home() / ".local" / "state" / "memogarden" / "logs",
    }[profile]

def get_db_path(layer: str, profile: Profile = None) -> Path:
    """Get database path for Soil or Core.
    
    Args:
        layer: 'soil' or 'core'
        profile: Optional profile override
    
    Returns:
        Path to database file
    """
    data_dir = get_data_dir(profile)
    return data_dir / f"{layer}.db"
```

### 4.3 Usage in Code

```python
# system/soil/database.py

from system.host.environment import get_db_path

class Soil:
    def __init__(self, db_path: Path = None, profile: str = None):
        """Initialize Soil database connection.
        
        Args:
            db_path: Explicit path override, or None for profile default
            profile: Explicit profile override
        """
        if db_path is None:
            db_path = get_db_path("soil", profile)
        
        self.db_path = db_path
        self._ensure_directories()
        self.conn = sqlite3.connect(db_path)
        self._initialize_schema()
    
    def _ensure_directories(self):
        """Create data directory if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
```

---

## 5. Schema Access

### 5.1 Schema Bundling

Schemas are copied into the package during build:

```toml
# memogarden-system/pyproject.toml

[tool.setuptools.package-data]
system = [
    "schemas/sql/*.sql",
    "schemas/types/**/*.json"
]
```

Build script:
```bash
#!/bin/bash
# scripts/build-system.sh

cd memogarden-system

# Copy schemas into package
mkdir -p system/schemas
cp -r ../schemas/sql system/schemas/
cp -r ../schemas/types system/schemas/

# Build package
python -m build

# Cleanup (schemas remain in source)
rm -rf system/schemas
```

### 5.2 Schema Access API

```python
# system/schemas.py

import json
from pathlib import Path
try:
    from importlib.resources import files  # Python 3.9+
except ImportError:
    from importlib_resources import files  # Backport

def get_sql_schema(layer: str) -> str:
    """Get SQL schema for Soil or Core.
    
    Args:
        layer: 'soil' or 'core'
    
    Returns:
        SQL schema as string
    
    Example:
        schema = get_sql_schema('soil')
        cursor.executescript(schema)
    """
    ref = files("system") / "schemas" / "sql" / f"{layer}.sql"
    return ref.read_text()

def get_type_schema(category: str, type_name: str) -> dict:
    """Get JSON Schema for item or entity type.
    
    Args:
        category: 'items' or 'entities'
        type_name: Type name without .schema.json suffix
    
    Returns:
        JSON Schema as dict
    
    Example:
        schema = get_type_schema('items', 'email')
        jsonschema.validate(data, schema)
    """
    ref = files("system") / "schemas" / "types" / category / f"{type_name}.schema.json"
    return json.loads(ref.read_text())

def list_type_schemas(category: str) -> list[str]:
    """List available type schemas in category.
    
    Args:
        category: 'items' or 'entities'
    
    Returns:
        List of type names (without .schema.json suffix)
    """
    schema_dir = files("system") / "schemas" / "types" / category
    schemas = []
    
    # Handle both directory and zip (when installed)
    if schema_dir.is_dir():
        for file in schema_dir.iterdir():
            if file.name.endswith('.schema.json'):
                schemas.append(file.name.replace('.schema.json', ''))
    
    return sorted(schemas)
```

### 5.3 Usage Example

```python
# Initialize database with bundled schema
from system.schemas import get_sql_schema
from system.host.environment import get_db_path

db_path = get_db_path('soil')
conn = sqlite3.connect(db_path)

schema_sql = get_sql_schema('soil')
conn.executescript(schema_sql)
```

---

## 6. Installation Procedures

### 6.1 Device Profile Installation

```bash
#!/bin/bash
# Install MemoGarden on Device profile (Raspberry Pi, dedicated server)

# 1. Create system user
sudo useradd -r -s /bin/false -d /var/lib/memogarden memogarden

# 2. Create virtual environment
sudo mkdir -p /opt/memogarden
sudo python3 -m venv /opt/memogarden/venv
sudo chown -R memogarden:memogarden /opt/memogarden

# 3. Install packages
sudo -u memogarden /opt/memogarden/venv/bin/pip install memogarden-system
sudo -u memogarden /opt/memogarden/venv/bin/pip install memogarden-api

# 4. Create directories
sudo mkdir -p /var/lib/memogarden
sudo mkdir -p /etc/memogarden
sudo mkdir -p /var/log/memogarden
sudo mkdir -p /run/memogarden

sudo chown memogarden:memogarden /var/lib/memogarden
sudo chown memogarden:memogarden /var/log/memogarden
sudo chown memogarden:memogarden /run/memogarden

# 5. Create config
sudo tee /etc/memogarden/config.toml << 'EOF'
[deployment]
profile = "device"

[paths]
# Auto-detected as device profile defaults
data_dir = "auto"
config_dir = "auto"
log_dir = "auto"

[network]
bind_address = "127.0.0.1"
bind_port = 8080
EOF

sudo chown root:memogarden /etc/memogarden/config.toml
sudo chmod 640 /etc/memogarden/config.toml

# 6. Initialize databases (creates soil.db, core.db)
sudo -u memogarden /opt/memogarden/venv/bin/python -m system.cli init

# 7. Install systemd service
sudo tee /etc/systemd/system/memogarden-api.service << 'EOF'
[Unit]
Description=MemoGarden API Server
After=network.target

[Service]
Type=simple
User=memogarden
Group=memogarden
WorkingDirectory=/opt/memogarden
Environment="PATH=/opt/memogarden/venv/bin"
ExecStart=/opt/memogarden/venv/bin/python -m api.main
Restart=on-failure
RestartSec=5s

# Resource limits
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# 8. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable memogarden-api
sudo systemctl start memogarden-api

# 9. Verify
sudo systemctl status memogarden-api
curl http://localhost:8080/health
```

### 6.2 System Profile Installation

Same as Device profile, but:
- May be installed by sysadmin (not operator)
- May run in container or on shared host
- No watchdog daemon by default

### 6.3 Personal Profile Installation

```bash
#!/bin/bash
# Install MemoGarden on Personal profile (laptop, desktop)

# 1. Install packages to user site-packages
pip install --user memogarden-system
pip install --user memogarden-api

# 2. Initialize (auto-creates ~/.local/share/memogarden/)
python -m system.cli init

# 3. Create config (optional, uses defaults if missing)
mkdir -p ~/.config/memogarden
cat > ~/.config/memogarden/config.toml << 'EOF'
[deployment]
profile = "personal"

[network]
bind_address = "127.0.0.1"
bind_port = 8080
EOF

# 4. Run as systemd user service
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/memogarden-api.service << 'EOF'
[Unit]
Description=MemoGarden API Server
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/python -m api.main
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable memogarden-api
systemctl --user start memogarden-api

# 5. Verify
systemctl --user status memogarden-api
curl http://localhost:8080/health
```

### 6.4 Container Installation

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install packages
RUN pip install --no-cache-dir memogarden-system memogarden-api

# Create directories (will be mounted)
RUN mkdir -p /data /config

# Environment
ENV MEMOGARDEN_PROFILE=container
ENV MEMOGARDEN_DATA_DIR=/data
ENV MEMOGARDEN_CONFIG_DIR=/config

# Initialize schemas (bundled in package)
RUN python -m system.cli init --dry-run

# Run API
CMD ["python", "-m", "api.main"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  memogarden:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - MEMOGARDEN_PROFILE=container
```

---

## 7. Configuration

### 7.1 Config File Format

```toml
# /etc/memogarden/config.toml (or ~/.config/memogarden/config.toml)

[deployment]
profile = "auto"  # "device" | "system" | "personal" | "container" | "auto"

[paths]
# Use "auto" for profile defaults (recommended)
data_dir = "auto"     # /var/lib/memogarden/ or ~/.local/share/memogarden/
config_dir = "auto"   # /etc/memogarden/ or ~/.config/memogarden/
log_dir = "auto"      # /var/log/memogarden/ or ~/.local/state/memogarden/logs/

# Or override explicitly
# data_dir = "/custom/path/data"
# config_dir = "/custom/path/config"

[network]
bind_address = "127.0.0.1"
bind_port = 8080

[security]
encryption = "disabled"  # "disabled" | "optional" | "required"

[resources]
max_memory_mb = "auto"      # Profile-specific default
max_cpu_percent = "auto"
```

### 7.2 Environment Variable Overrides

Environment variables take precedence over config file:

| Variable | Purpose | Example |
|----------|---------|---------|
| `MEMOGARDEN_PROFILE` | Force profile | `export MEMOGARDEN_PROFILE=device` |
| `MEMOGARDEN_DATA_DIR` | Override data dir | `export MEMOGARDEN_DATA_DIR=/mnt/nas/memogarden` |
| `MEMOGARDEN_CONFIG_DIR` | Override config dir | `export MEMOGARDEN_CONFIG_DIR=/etc/mg` |
| `MEMOGARDEN_LOG_DIR` | Override log dir | `export MEMOGARDEN_LOG_DIR=/var/log/mg` |

---

## 8. Package Distribution

### 8.1 Build Process

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

### 8.2 Distribution Methods

| Method | Use Case | Command |
|--------|----------|---------|
| **PyPI** | Public release | `pip install memogarden-system` |
| **Private PyPI** | Organization-internal | `pip install --index-url=<url> memogarden-system` |
| **Wheel file** | Air-gapped systems | `pip install memogarden_system-0.1.0-py3-none-any.whl` |
| **Git** | Development | `pip install git+https://github.com/org/memogarden.git#subdirectory=memogarden-system` |

### 8.3 Version Management

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

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# memogarden-system/tests/test_host/test_environment.py

import os
import pytest
from system.host.environment import detect_profile, get_data_dir, Profile

def test_detect_profile_explicit_override():
    os.environ['MEMOGARDEN_PROFILE'] = 'device'
    assert detect_profile() == Profile.DEVICE

def test_get_data_dir_device():
    path = get_data_dir(Profile.DEVICE)
    assert path == Path('/var/lib/memogarden')

def test_get_data_dir_personal():
    path = get_data_dir(Profile.PERSONAL)
    assert path == Path.home() / '.local' / 'share' / 'memogarden'
```

### 9.2 Integration Tests

```python
# memogarden-system/tests/test_integration/test_soil_init.py

import tempfile
from pathlib import Path
from system.soil import Soil

def test_soil_init_creates_database():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "soil.db"
        soil = Soil(db_path=db_path)
        
        assert db_path.exists()
        assert soil.conn is not None
```

### 9.3 Profile-Specific Tests

Tests should verify correct behavior for each profile:

```python
@pytest.mark.parametrize("profile", [
    Profile.DEVICE,
    Profile.SYSTEM,
    Profile.PERSONAL,
    Profile.CONTAINER,
])
def test_path_resolution_per_profile(profile):
    data_dir = get_data_dir(profile)
    config_dir = get_config_dir(profile)
    
    # Verify paths follow profile conventions
    assert data_dir.is_absolute()
    # ... profile-specific assertions
```

---

## 10. Migration Path

### 10.1 From Current Structure

Current structure has issues:
- Triple nesting (`/memogarden/memogarden/memogarden/`)
- Soil and Core as separate projects
- No clear deployment mapping

Migration steps:

1. **Reorganize repository** to match Section 2.1
2. **Implement `system.host.environment`** with path resolution
3. **Implement `system.schemas`** with bundled schema access
4. **Update database initialization** to use path resolution
5. **Update build process** to copy schemas into package
6. **Test installation** on each profile
7. **Update documentation** (README, installation guides)

### 10.2 Backward Compatibility

During migration, maintain compatibility:

```python
# Legacy path support (deprecated)
def get_db_path_legacy() -> Path:
    """Legacy: try old paths first."""
    old_paths = [
        Path('/memogarden/memogarden/memogarden/db/soil.db'),
        Path('./soil.db'),
    ]
    
    for path in old_paths:
        if path.exists():
            warnings.warn(f"Using legacy path {path}. Please migrate.", DeprecationWarning)
            return path
    
    # Fall back to new path resolution
    return get_db_path('soil')
```

---

## 11. Open Questions

1. **Multi-package versioning**: Should memogarden-system and memogarden-api share version numbers or evolve independently?

2. **Schema versioning**: How to handle schema evolution across package versions? (Alembic-style migrations?)

3. **Provider registration**: Should providers be discovered via entry points or explicit configuration?

4. **Wheel bundling**: Should we provide meta-packages that install system + api together?

5. **Offline installation**: What's the recommended process for air-gapped environments?

---

## 12. Future Work

### 12.1 Enhanced Profile Detection

- Detect Kubernetes vs Docker container
- Detect systemd vs other init systems
- Auto-configure based on detected environment

### 12.2 Schema Migrations

Alembic-style migration system:

```
system/schemas/migrations/
├── 001_initial.sql
├── 002_add_fidelity.sql
└── 003_add_context_frames.sql
```

### 12.3 Provider Plugin System

Entry point-based provider discovery:

```toml
# provider package pyproject.toml
[project.entry-points."memogarden.providers"]
gmail = "gmail_provider:GmailProvider"
```

---

## References

- RFC-001 v4: Security & Operations Architecture
- RFC-002 v5: Relation Time Horizon & Fossilization
- RFC-003 v2: Context Capture Mechanism
- PRD v0.9.0: MemoGarden Personal Information System
- Python Packaging User Guide: https://packaging.python.org/

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-30 | Initial draft |

---

**Status:** Draft  
**Next Steps:**
1. Review and approve package structure
2. Implement `system.host.environment` module
3. Implement `system.schemas` module
4. Update build scripts for schema bundling
5. Test installation on all profiles

---

**END OF RFC**
