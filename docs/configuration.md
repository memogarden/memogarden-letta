# MemoGarden Configuration Reference

**Last Updated:** 2026-02-11
**Version:** RFC-004 v2

Complete reference for MemoGarden environment variables and configuration.

## Environment Variables

### Path Variables (RFC-004 Section 5.3)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MEMOGARDEN_SOIL_DB` | Path | `{data_dir}/soil.db` | Soil database file path |
| `MEMOGARDEN_CORE_DB` | Path | `{data_dir}/core.db` | Core database file path |
| `MEMOGARDEN_DATA_DIR` | Path | (verb-based) | Shared data directory |
| `MEMOGARDEN_CONFIG_DIR` | Path | (verb-based) | Configuration directory |
| `MEMOGARDEN_LOG_DIR` | Path | (verb-based) | Log directory |

**Verb-Based Defaults:**

| Verb | `MEMOGARDEN_DATA_DIR` | `MEMOGARDEN_CONFIG_DIR` | `MEMOGARDEN_LOG_DIR` |
|------|----------------------|------------------------|---------------------|
| `serve` | `/var/lib/memogarden` | `/etc/memogarden` | `/var/log/memogarden` |
| `run` | `~/.local/share/memogarden` | `~/.config/memogarden` | `~/.local/state/memogarden/logs` |
| `deploy` | `/data` | `/config` | (stdout only) |

### Runtime Variables (RFC-004 Section 5.3)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MEMOGARDEN_VERB` | String | `run` | Deployment verb: `serve`, `run`, or `deploy` |
| `MEMOGARDEN_CONFIG` | Path | (verb-based) | Explicit config file path override |
| `MEMOGARDEN_RESOURCE_PROFILE` | String | `standard` | Resource profile: `embedded` or `standard` |
| `MEMOGARDEN_LOG_LEVEL` | String | (profile) | Logging level: `debug`, `info`, `warning`, `error` |

### Network Variables (RFC-004 Section 5.3)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MEMOGARDEN_BIND_ADDRESS` | IP | `127.0.0.1` | Bind address for API server |
| `MEMOGARDEN_BIND_PORT` | Port | `8080` | Bind port for API server |

### Security Variables (RFC-004 Section 5.3)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MEMOGARDEN_ENCRYPTION` | String | `disabled` | Encryption mode: `disabled`, `optional`, `required` |
| `FLASK_SECRET_KEY` | String | (auto-generated) | Flask session signing key |
| `JWT_SECRET_KEY` | String | (auto-generated) | JWT token signing key |
| `API_KEY_*` | String | - | API keys for external access |

### Precedence Order (RFC-004)

Environment variables take precedence over TOML configuration:

```
Environment Variable > TOML Config > Built-in Default
```

---

## TOML Configuration

### Configuration File Location

By deployment verb:

| Verb | Config Location |
|------|-----------------|
| `serve` | `/etc/memogarden/config.toml` |
| `run` | `~/.config/memogarden/config.toml` |
| `deploy` | `/config/config.toml` |

### Configuration Sections

#### `[runtime]` Section

Runtime parameters and resource profile (RFC-004 Section 5.1):

```toml
[runtime]
resource_profile = "standard"  # "embedded" | "standard"

# Optional: Override individual profile settings
max_view_entries = 1000
max_search_results = 100
fossilization_threshold = 0.90
wal_checkpoint_interval = 60
log_level = "info"
```

**Resource Profile Defaults:**

**embedded** (Raspberry Pi, low-power systems):
- `max_view_entries`: 100
- `max_search_results`: 20
- `fossilization_threshold`: 0.80
- `wal_checkpoint_interval`: 300
- `log_level`: "warning"

**standard** (servers, workstations):
- `max_view_entries`: 1000
- `max_search_results`: 100
- `fossilization_threshold`: 0.90
- `wal_checkpoint_interval`: 60
- `log_level`: "info"

#### `[paths]` Section

Optional path overrides (RFC-004 Section 5.1):

```toml
[paths]
data_dir = "/var/lib/memogarden"
config_dir = "/etc/memogarden"
log_dir = "/var/log/memogarden"
```

#### `[network]` Section

Network configuration:

```toml
[network]
bind_address = "127.0.0.1"
bind_port = 8080
```

#### `[security]` Section

Security settings:

```toml
[security]
encryption = "disabled"
jwt_secret_key = "change-me-in-production"
jwt_expiry_days = 30
bypass_localhost_check = false
bcrypt_work_factor = 12
```

#### `[api]` Section

API-specific settings:

```toml
[api]
api_v1_prefix = "/api/v1"
cors_origins = ["http://localhost:3000"]
```

---

## Environment Variable Examples

### Example 1: Development Setup

```bash
# Set data directory to current directory
export MEMOGARDEN_DATA_DIR=$(pwd)/data

# Use embedded profile for testing
export MEMOGARDEN_RESOURCE_PROFILE=embedded

# Enable debug logging
export MEMOGARDEN_LOG_LEVEL=debug

# Run server
./scripts/run.sh
```

### Example 2: Production with Custom Paths

```bash
# Use SSD for data
export MEMOGARDEN_DATA_DIR=/mnt/ssd/memogarden

# Bind to all interfaces
export MEMOGARDEN_BIND_ADDRESS=0.0.0.0
export MEMOGARDEN_BIND_PORT=8080

# Use standard profile
export MEMOGARDEN_RESOURCE_PROFILE=standard

# Start service
sudo systemctl start memogarden
```

### Example 3: Container Deployment

```bash
docker run -d \
  -v /mnt/data:/data \
  -e MEMOGARDEN_RESOURCE_PROFILE=standard \
  -e MEMOGARDEN_BIND_ADDRESS=0.0.0.0 \
  -p 8080:8080 \
  memogarden:latest
```

### Example 4: Override Specific Database Paths

```bash
# Separate databases on different disks
export MEMOGARDEN_SOIL_DB=/mnt/fast/ssd/soil.db
export MEMOGARDEN_CORE_DB=/mnt/slow/hdd/core.db

# Run application
./scripts/run.sh
```

---

## Configuration Validation

### Check Current Configuration

```bash
# View configuration
cat /etc/memogarden/config.toml

# Check environment variables
env | grep MEMOGARDEN
```

### Test Configuration

```bash
# Run with debug logging
export MEMOGARDEN_LOG_LEVEL=debug
./scripts/run.sh
```

### Validate Paths

```bash
# Check database paths
python3 -c "
from system.host.environment import get_db_path
print('Soil:', get_db_path('soil'))
print('Core:', get_db_path('core'))
"
```

---

## Common Configuration Patterns

### Pattern 1: Multi-Home Setup

```bash
# Server 1 (Home)
export MEMOGARDEN_BIND_ADDRESS=192.168.1.10
export MEMOGARDEN_DATA_DIR=/home/server1

# Server 2 (Office)
export MEMOGARDEN_BIND_ADDRESS=10.0.0.10
export MEMOGARDEN_DATA_DIR=/office/server2
```

### Pattern 2: Development vs Production

```bash
# Development
export MEMOGARDEN_RESOURCE_PROFILE=standard
export MEMOGARDEN_LOG_LEVEL=debug
export MEMOGARDEN_BIND_ADDRESS=127.0.0.1

# Production
export MEMOGARDEN_RESOURCE_PROFILE=embedded
export MEMOGARDEN_LOG_LEVEL=warning
export MEMOGARDEN_BIND_ADDRESS=0.0.0.0
```

### Pattern 3: Testing with Clean State

```bash
# Use temporary directory for testing
export MEMOGARDEN_DATA_DIR=/tmp/memogarden-test
rm -rf $MEMOGARDEN_DATA_DIR
mkdir -p $MEMOGARDEN_DATA_DIR
./scripts/run.sh
```

---

## Troubleshooting Configuration

### Issue: Configuration Not Applied

**Symptoms:** Settings in config.toml ignored

**Solutions:**
1. Check environment variables take precedence
   ```bash
   env | grep MEMOGARDEN
   ```
2. Verify config file location matches verb
   ```bash
   # For 'serve' verb
   cat /etc/memogarden/config.toml
   ```
3. Check TOML syntax
   ```bash
   python3 -c "import tomllib; tomllib.load(open('/etc/memogarden/config.toml', 'rb'))"
   ```

### Issue: Database Path Wrong

**Symptoms:** Database not found or created in wrong location

**Solutions:**
1. Check `MEMOGARDEN_DATA_DIR`
2. Check explicit `MEMOGARDEN_*_DB` variables
3. Verify path resolution order

### Issue: Port Already in Use

**Symptoms:** "Address already in use" error

**Solutions:**
1. Set different port:
   ```bash
   export MEMOGARDEN_BIND_PORT=8081
   ```
2. Or find and kill process using port:
   ```bash
   sudo lsof -i :8080
   ```

---

## See Also

- [Deployment Guide](deployment.md)
- [Quickstart Guide](quickstart.md)
- [API Reference](api.md)
- RFC-004 v2: Package Structure & Deployment
