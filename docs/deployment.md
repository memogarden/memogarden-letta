# MemoGarden Deployment Guide

**Last Updated:** 2026-02-11
**Version:** 1.0
**Status:** Session 14 - RFC-004 Deployment

## Overview

This guide covers deploying MemoGarden on Raspberry Pi (RPi) and other platforms. MemoGarden uses verb-based deployment configuration following RFC-004.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation Methods](#installation-methods)
4. [Configuration](#configuration)
5. [Deployment Verbs](#deployment-verbs)
6. [Environment Variables](#environment-variables)
7. [Running the Service](#running-the-service)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Raspberry Pi Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/memogarden/memogarden.git
cd memogarden

# Run the installer
sudo ./install.sh

# Start the service
sudo systemctl start memogarden
sudo systemctl enable memogarden

# Check status
sudo systemctl status memogarden
```

### Development Installation

```bash
# Clone repositories
git clone https://github.com/memogarden/memogarden-system.git
git clone https://github.com/memogarden/memogarden-api.git

# Install system package
cd memogarden-system
poetry install

# Install API package
cd ../memogarden-api
poetry install

# Run development server
./scripts/run.sh
```

---

## Prerequisites

### Hardware Requirements

| Deployment | Minimum RAM | Storage | Notes |
|-------------|-------------|---------|-------|
| **embedded** | 512MB | 8GB SD card | Raspberry Pi Zero/3B+ |
| **standard** | 2GB | 16GB SD card | Raspberry Pi 4/5 |

### Software Requirements

**System:**
- Python 3.13 or later
- Poetry 1.8+ (for development)
- Git

**For RPi Production:**
- Raspberry Pi OS (Bookworm or later)
- systemd (system and service manager)

### Platform-Specific Notes

**Raspberry Pi:**
- Use Python 3.13 from `apt` (`sudo apt install python3.13`)
- Poetry installation: `curl -sSL https://install.python-poetry.org | python3 -`

**Arch Linux ARM:**
- `sudo pacman -S python python-pip`
- `pip install poetry`

---

## Installation Methods

### Method 1: Automated Installer (RPi)

The `install.sh` script handles the full installation:

```bash
sudo ./install.sh [--resource-profile {embedded|standard}]
```

**What it does:**
1. Checks system dependencies
2. Creates `memogarden` user and group
3. Installs Python packages to `/opt/memogarden/venv/`
4. Sets up directory structure
5. Creates systemd service file
6. Generates default configuration

### Method 2: Manual Installation

For custom deployments or development:

```bash
# 1. Create user
sudo useradd -r -s /bin/bash memogarden
sudo mkdir -p /opt/memogarden
sudo chown memogarden:memogarden /opt/memogarden

# 2. Install packages
cd /opt/memogarden
sudo -u memogarden python3 -m venv venv
sudo -u memogarden venv/bin/pip install \
    memogarden-system memogarden-api

# 3. Create directories
sudo -u memogarden mkdir -p /var/lib/memogarden /var/log/memogarden

# 4. Create systemd service
sudo cp memogarden.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable memogarden
```

### Method 3: Container Deployment

```bash
# Build image
docker build -t memogarden:latest .

# Run container
docker run -d \
  -v memogarden-data:/data \
  -v memogarden-config:/config \
  -p 8080:8080 \
  -e MEMOGARDEN_RESOURCE_PROFILE=standard \
  memogarden:latest
```

---

## Configuration

### Configuration File Location

By deployment verb:

| Verb | Config Location |
|------|-----------------|
| `serve` | `/etc/memogarden/config.toml` |
| `run` | `~/.config/memogarden/config.toml` |
| `deploy` | `/config/config.toml` |

### Example Configuration

```toml
# /etc/memogarden/config.toml

[runtime]
# Resource profile: "embedded" (RPi) or "standard" (servers)
resource_profile = "standard"

# Optional: Override individual profile settings
# max_view_entries = 1000
# max_search_results = 100
# fossilization_threshold = 0.90
# wal_checkpoint_interval = 60
# log_level = "info"

[paths]
# Optional: Override default paths
# data_dir = "/var/lib/memogarden"
# config_dir = "/etc/memogarden"
# log_dir = "/var/log/memogarden"

[network]
bind_address = "127.0.0.1"
bind_port = 8080

[security]
encryption = "disabled"
# jwt_secret_key = "change-me-in-production"
# jwt_expiry_days = 30
# bypass_localhost_check = false
# bcrypt_work_factor = 12

[api]
api_v1_prefix = "/api/v1"
cors_origins = ["http://localhost:3000"]
```

### Resource Profiles

**embedded** (for Raspberry Pi, low-power systems):
- `max_view_entries`: 100
- `max_search_results`: 20
- `fossilization_threshold`: 0.80
- `wal_checkpoint_interval`: 300 seconds
- `log_level`: "warning"

**standard** (for servers, workstations):
- `max_view_entries`: 1000
- `max_search_results`: 100
- `fossilization_threshold`: 0.90
- `wal_checkpoint_interval`: 60 seconds
- `log_level`: "info"

---

## Deployment Verbs

MemoGarden uses three deployment verbs to determine configuration sources:

### `serve` - System Daemon

**Use case:** Production service managed by systemd

**Paths:**
- Data: `/var/lib/memogarden/`
- Config: `/etc/memogarden/`
- Logs: `/var/log/memogarden/`

**Command:**
```bash
/opt/memogarden/bin/memogarden serve
```

**Or via systemd:**
```bash
sudo systemctl start memogarden
```

### `run` - User Process

**Use case:** Development, personal use

**Paths:**
- Data: `~/.local/share/memogarden/`
- Config: `~/.config/memogarden/`
- Logs: `~/.local/state/memogarden/logs/`

**Command:**
```bash
memogarden run
```

### `deploy` - Container

**Use case:** Docker/Kubernetes deployment

**Paths:**
- Data: `/data/` (volume mount)
- Config: `/config/` (volume mount)
- Logs: stdout only

**Command:**
```bash
memogarden deploy
```

---

## Environment Variables

Environment variables take precedence over TOML configuration (RFC-004 Section 5.3):

| Variable | Purpose | Default |
|----------|---------|---------|
| `MEMOGARDEN_VERB` | Deployment verb | `run` |
| `MEMOGARDEN_CONFIG` | Config file path | (verb-based) |
| `MEMOGARDEN_RESOURCE_PROFILE` | Resource profile | `standard` |
| `MEMOGARDEN_DATA_DIR` | Data directory | (verb-based) |
| `MEMOGARDEN_SOIL_DB` | Soil database path | `{data_dir}/soil.db` |
| `MEMOGARDEN_CORE_DB` | Core database path | `{data_dir}/core.db` |
| `MEMOGARDEN_BIND_ADDRESS` | Bind address | `127.0.0.1` |
| `MEMOGARDEN_BIND_PORT` | Bind port | `8080` |
| `MEMOGARDEN_LOG_LEVEL` | Logging level | `info` |
| `MEMOGARDEN_ENCRYPTION` | Encryption mode | `disabled` |

### Example: Override via Environment

```bash
# Set resource profile
export MEMOGARDEN_RESOURCE_PROFILE=embedded

# Override data directory
export MEMOGARDEN_DATA_DIR=/mnt/ssd/memogarden

# Override network settings
export MEMOGARDEN_BIND_ADDRESS=0.0.0.0
export MEMOGARDEN_BIND_PORT=9000
```

---

## Running the Service

### Using systemd (Production)

```bash
# Start service
sudo systemctl start memogarden

# Enable at boot
sudo systemctl enable memogarden

# Check status
sudo systemctl status memogarden

# View logs
sudo journalctl -u memogarden -f

# Restart
sudo systemctl restart memogarden

# Stop
sudo systemctl stop memogarden
```

### Using User systemd (Development)

```bash
# Start user service
systemctl --user start memogarden

# Enable at login
systemctl --user enable memogarden

# Check status
systemctl --user status memogarden
```

### Direct Execution (Development)

```bash
# From source directory
cd memogarden/memogarden-api
./scripts/run.sh
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u memogarden -n 50 --no-pager
```

**Common issues:**

1. **Database locked:**
   ```bash
   sudo systemctl stop memogarden
   sudo rm -f /var/lib/memogarden/*.db-wal
   sudo systemctl start memogarden
   ```

2. **Permission denied:**
   ```bash
   sudo chown -R memogarden:memogarden /var/lib/memogarden
   sudo chown -R memogarden:memogarden /var/log/memogarden
   ```

3. **Port already in use:**
   ```bash
   sudo ss -tlnp | grep 8080
   # Change port in /etc/memogarden/config.toml
   sudo systemctl restart memogarden
   ```

### Database Issues

**Check database integrity:**
```bash
cd /opt/memogarden
./scripts/debug.sh diagnose
```

**Rebuild database (WARNING: Deletes data):**
```bash
sudo systemctl stop memogarden
sudo rm /var/lib/memogarden/*.db
sudo systemctl start memogarden
```

### Performance Issues

**For Raspberry Pi (low RAM):**

1. Use `embedded` resource profile:
   ```toml
   [runtime]
   resource_profile = "embedded"
   ```

2. Reduce WAL checkpoint interval:
   ```toml
   [runtime]
   wal_checkpoint_interval = 600  # 10 minutes
   ```

3. Increase swap space:
   ```bash
   sudo dphys-swapfile swapoff
   sudo vim /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=1024
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

### Health Check

Verify the service is responding:

```bash
# Health endpoint
curl http://localhost:8080/health

# Expected response
{"status": "ok", "databases": "healthy"}
```

### Debug Mode

Run with debug logging:

```bash
# Set log level
export MEMOGARDEN_LOG_LEVEL=debug

# Run in foreground
/opt/memogarden/bin/memogarden serve
```

---

## Advanced Topics

### Custom Installation Prefix

To install to a custom prefix (e.g., `/usr/local`):

```bash
sudo ./install.sh --prefix=/usr/local
```

### Multi-Instance Deployment

Run multiple instances with different configs:

```bash
# Instance 1
sudo cp memogarden.service /etc/systemd/system/memogarden@1.service
sudo mkdir -p /etc/memogarden/instances/1

# Instance 2
sudo cp memogarden.service /etc/systemd/system/memogarden@2.service
sudo mkdir -p /etc/memogarden/instances/2

# Start instances
sudo systemctl start memogarden@1
sudo systemctl start memogarden@2
```

### Backup and Restore

**Backup:**
```bash
sudo systemctl stop memogarden
sudo tar czf memogarden-backup-$(date +%Y%m%d).tar.gz \
    /var/lib/memogarden \
    /etc/memogarden
sudo systemctl start memogarden
```

**Restore:**
```bash
sudo systemctl stop memogarden
sudo tar xzf memogarden-backup-YYYYMMDD.tar.gz -C /
sudo systemctl start memogarden
```

---

## Getting Help

- **Documentation:** See `docs/` directory
- **Issues:** https://github.com/memogarden/memogarden/issues
- **RFCs:** See `plan/` directory for architecture documents

---

**References:**
- RFC-004 v2: Package Structure & Deployment
- RFC-008 v1.2: Transaction Semantics
- Implementation Plan: Session 14
