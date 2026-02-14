# MemoGarden Troubleshooting Guide

**Last Updated:** 2026-02-14
**Version:** 0.1.0

Common issues and solutions for MemoGarden.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Database Issues](#database-issues)
3. [API Issues](#api-issues)
4. [Authentication Issues](#authentication-issues)
5. [Performance Issues](#performance-issues)
6. [Deployment Issues](#deployment-issues)

---

## Installation Issues

### Poetry commands not found

**Symptoms:**
```
poetry: command not found
```

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.poetry/bin:$PATH"

# Verify installation
poetry --version
```

### Python version too old

**Symptoms:**
```
SyntaxError: invalid syntax
```

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.13+
# On Debian/Ubuntu:
sudo apt update
sudo apt install python3.13 python3.13-venv

# On Arch:
sudo pacman -S python3.13
```

### Dependency conflicts

**Symptoms:**
```
ResolverError: Because your project was configured with Python 3.12...
```

**Solution:**
```bash
# Clear Poetry cache
poetry cache clear pypi --all

# Update lock file
poetry lock --no-update

# Install dependencies
poetry install
```

---

## Database Issues

### Database locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

1. **Check for running processes:**
   ```bash
   # Check if API server is running
   ps aux | grep python

   # Check for other processes holding locks
   lsof | grep soil.db
   lsof | grep core.db
   ```

2. **Remove WAL files (safe):**
   ```bash
   # Stop the service first
   sudo systemctl stop memogarden

   # Remove WAL files (SQLite will recreate)
   sudo rm -f /var/lib/memogarden/*.db-wal
   sudo rm -f /var/lib/memogarden/*.db-shm

   # Restart service
   sudo systemctl start memogarden
   ```

3. **Increase timeout:**
   ```bash
   # Set longer timeout in environment
   export MEMOGARDEN_DB_TIMEOUT=30
   ```

### Database corruption

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions:**

1. **Run integrity check:**
   ```bash
   # Check database integrity
   sqlite3 /var/lib/memogarden/core.db "PRAGMA integrity_check;"

   # Check Soil database
   sqlite3 /var/lib/memogarden/soil.db "PRAGMA integrity_check;"
   ```

2. **Export and reimport:**
   ```bash
   # Stop service
   sudo systemctl stop memogarden

   # Dump database
   sqlite3 /var/lib/memogarden/core.db ".dump" > core_dump.sql

   # Create new database
   sqlite3 /var/lib/memogarden/core_new.db < core_dump.sql

   # Replace old database
   sudo mv /var/lib/memogarden/core_new.db /var/lib/memogarden/core.db

   # Restart service
   sudo systemctl start memogarden
   ```

### Cross-database inconsistency

**Symptoms:**
```
System status: inconsistent
```

**Solutions:**

1. **Check detailed status:**
   ```bash
   curl http://localhost:8080/status
   ```

2. **Run consistency check:**
   ```bash
   # From memogarden-api directory
   poetry run python -c "
   from system.transaction_coordinator import TransactionCoordinator
   from system.host.environment import get_db_path

   coordinator = TransactionCoordinator(
       soil_db_path=str(get_db_path('soil')),
       core_db_path=str(get_db_path('core'))
   )
   status = coordinator.check_consistency()
   print(f'Status: {status.value}')
   "
   ```

3. **Recovery (last resort):**
   ```bash
   # Manual repair requires analyzing the inconsistency
   # Check Session 12 documentation for recovery tools
   ```

---

## API Issues

### Server won't start

**Symptoms:**
```
Address already in use
```

**Solution:**
```bash
# Find process using port 8080
sudo lsof -i :8080
# or
sudo ss -tlnp | grep 8080

# Change port in config
export MEMOGARDEN_BIND_PORT=8081

# Or kill the conflicting process
sudo kill <PID>
```

### 404 Not Found on valid UUID

**Symptoms:**
```
GET /mg returns 404 for known valid UUID
```

**Possible Causes:**
1. Entity was soft-deleted (forgotten)
2. UUID belongs to different layer (core_ vs soil_)
3. Wrong database path (environment variable override)

**Solution:**
```bash
# Check if entity was forgotten
curl -X POST http://localhost:8080/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "query",
    "filters": {"uuid": "core_xxx"}
  }'

# Check database path
curl http://localhost:8080/status
```

### Request validation errors

**Symptoms:**
```
ValidationError: Missing required field: op
```

**Solution:**
```bash
# Check request format
# All /mg requests require "op" field
curl -X POST http://localhost:8080/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "create",
    "type": "Transaction",
    "data": {...}
  }'
```

---

## Authentication Issues

### Invalid token

**Symptoms:**
```
401 Unauthorized
```

**Solutions:**

1. **Token expired:**
   ```bash
   # Login again to get new token
   curl -X POST http://localhost:8080/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "changeme"}'
   ```

2. **Wrong token format:**
   ```bash
   # Use Bearer authentication
   curl -H "Authorization: Bearer $TOKEN"

   # NOT
   curl -H "Authorization: $TOKEN"  # Wrong!
   ```

3. **Secret key changed:**
   ```bash
   # If JWT_SECRET_KEY changed, all tokens are invalidated
   # Users must login again
   ```

### Can't register new user

**Symptoms:**
```
Permission denied: Only admins can create users
```

**Solution:**
```bash
# 1. Create admin user first (if none exists)
# Visit http://localhost:8080/admin/register

# 2. Login as admin
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}'

# 3. Create user via API
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123",
    "is_admin": false
  }'
```

---

## Performance Issues

### Slow query performance

**Symptoms:**
- Queries take >5 seconds
- Search is slow

**Solutions:**

1. **Use embedded resource profile:**
   ```bash
   export MEMOGARDEN_RESOURCE_PROFILE=embedded
   ```

2. **Reduce query limits:**
   ```bash
   # Limit results
   curl -X POST http://localhost:8080/mg \
     -d '{"op": "query", "limit": 10}'
   ```

3. **Check database size:**
   ```bash
   ls -lh /var/lib/memogarden/*.db

   # Consider fossilization for large databases
   ```

### High memory usage

**Symptoms:**
```
Out of memory: Killed
```

**Solutions:**

1. **Use embedded profile:**
   ```toml
   [runtime]
   resource_profile = "embedded"
   ```

2. **Reduce max entries:**
   ```toml
   [runtime]
   max_view_entries = 50
   max_search_results = 10
   ```

---

## Deployment Issues

### Service won't start

**Symptoms:**
```
sudo systemctl start memogarden
# Job failed
```

**Solution:**
```bash
# Check status for errors
sudo systemctl status memogarden -l

# View logs
sudo journalctl -u memogarden -n 50 --no-pager

# Common issues:
# 1. Wrong path in config
# 2. Missing directories
# 3. Wrong user permissions
```

### Wrong database paths

**Symptoms:**
```
Database created in unexpected location
```

**Solution:**
```bash
# Check environment variables
env | grep MEMOGARDEN

# Check config file location
cat /etc/memogarden/config.toml

# Verify paths
curl http://localhost:8080/status
```

### Can't access from remote host

**Symptoms:**
```
Connection refused from remote machine
```

**Solution:**
```bash
# Check bind address
# Default: 127.0.0.1 (local only)

# Allow remote connections
export MEMOGARDEN_BIND_ADDRESS=0.0.0.0

# Or in config.toml
[network]
bind_address = "0.0.0.0"
```

---

## Getting Help

If you're still stuck:

1. **Check logs:**
   ```bash
   # Development
   tail -f memogarden-api/logs/app.log

   # Production (systemd)
   sudo journalctl -u memogarden -f
   ```

2. **Enable debug logging:**
   ```bash
   export MEMOGARDEN_LOG_LEVEL=debug
   ```

3. **Check status endpoint:**
   ```bash
   curl http://localhost:8080/status
   ```

4. **Report issues:**
   - GitHub: https://github.com/memogarden/memogarden/issues
   - Include: Version, error message, steps to reproduce

---

## See Also

- [API Documentation](api.md)
- [Architecture Overview](architecture.md)
- [Deployment Guide](deployment.md)
- [Configuration Reference](configuration.md)
