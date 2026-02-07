# RFC-007: Runtime Operations & Service Management

**Version:** 2.1  
**Status:** Draft  
**Author:** MemoGarden Project  
**Created:** 2026-02-02

## Abstract

This RFC specifies MemoGarden's runtime behavior, process lifecycle, installation procedures, and operational characteristics. It complements RFC-004 (which defines static structure and file locations) by detailing how MemoGarden processes start, run, signal readiness, handle failures, and shut down across different deployment contexts.

## Motivation

RFC-004 defines **where files live**; this RFC defines **how processes behave**. Specifically:

- How installation happens (interactive vs silent modes)
- How resource profiles are selected
- How startup sequences differ by verb (serve/run/deploy)
- How readiness is signaled to supervisors
- How graceful shutdown works
- How concurrency and locking are managed
- How failures are detected and recovered

---

## 1. Runtime Operations

### 1.1 Command Interface

MemoGarden provides three primary runtime verbs:

```bash
memogarden serve [OPTIONS]
  Run as system daemon (systemd-managed)
  Config: /etc/memogarden/config.toml
  
memogarden run [OPTIONS]
  Run as user process
  Config: ~/.config/memogarden/config.toml
  
memogarden deploy [OPTIONS]
  Run in container
  Config: Environment variables or /config/config.toml
```

**Common options:**

```
--config <path>
  Override default config file location
  
--resource-profile {embedded|standard}
  Override resource profile from config
  
--bind-address <addr>
  Override bind address (default: from config)
  
--bind-port <port>
  Override bind port (default: from config)
  
--log-level {debug|info|warning|error}
  Override log level
```

**Examples:**

```bash
# System daemon with default config
sudo systemctl start memogarden  # (calls: memogarden serve)

# User process for development
memogarden run --log-level debug

# Embedded device with custom config
memogarden serve --resource-profile embedded --config /custom/config.toml

# Container deployment
docker run memogarden deploy  # (uses ENV vars)
```

### 1.2 Resource Profiles

Resource profiles control operational parameters. Profiles are **operator-declared**, not hardware-detected.

#### embedded Profile

**Target:** Raspberry Pi, embedded systems, low-power hardware (<2GB RAM)

**Runtime parameters:**
- `max_view_entries`: 100 (vs 1000)
- `max_search_results`: 20 (vs 100)
- `fossilization_threshold`: 0.80 (trigger at 80% capacity)
- `wal_checkpoint_interval`: 300 seconds (5 minutes)
- `log_level`: "warning" (reduce I/O)
- `integrity_check_on_startup`: false (skip after first boot)

**Operational characteristics:**
- Aggressive fossilization under storage pressure
- Conservative memory allocation
- Reduced logging to minimize SD card wear
- Longer maintenance intervals to reduce CPU usage

#### standard Profile (default)

**Target:** Laptops, desktops, servers, containers (ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°Ãƒâ€šÃ‚Â¥2GB RAM)

**Runtime parameters:**
- `max_view_entries`: 1000
- `max_search_results`: 100
- `fossilization_threshold`: 0.90 (trigger at 90% capacity)
- `wal_checkpoint_interval`: 60 seconds
- `log_level`: "info"
- `integrity_check_on_startup`: true

**Operational characteristics:**
- Normal fossilization policy
- Standard memory allocation
- Full logging
- Frequent maintenance for optimal performance

#### Profile Selection

Profiles are set via:
1. `config.toml`: `[runtime] resource_profile = "embedded"`
2. CLI flag: `--resource-profile embedded`
3. Environment: `MEMOGARDEN_RESOURCE_PROFILE=embedded`

Priority: CLI flag > Environment > config.toml > default (standard)

### 1.3 Startup Sequence

Startup is **synchronous and fail-fast**. The process must fully initialize before signaling readiness.

```python
def main(verb: str, args: Args) -> int:
    """
    MemoGarden main entry point.
    
    Returns:
        0 on success, 1 on failure
    """
    
    # 1. Resolve runtime context from verb
    try:
        context = resolve_context(verb, args.config)
    except ConfigError as e:
        log.fatal(f"Config error: {e}")
        return 1
    
    # 2. Load configuration
    try:
        config = load_config(context.config_path, args)
        setup_logging(config, context)
    except Exception as e:
        log.fatal(f"Failed to load config: {e}")
        return 1
    
    # 3. Initialize databases (BLOCKING, FAIL-FAST)
    try:
        soil_db = init_soil_database(context, config)
        core_db = init_core_database(context, config)
        
        # Optional integrity check (embedded profile skips after first boot)
        if config.integrity_check_on_startup:
            verify_integrity(soil_db, core_db)
            
    except DatabaseError as e:
        log.fatal(f"Database initialization failed: {e}")
        return 1
    
    # 4. Start HTTP server (BLOCKING)
    try:
        server = create_server(config, soil_db, core_db)
        server.bind(config.bind_address, config.bind_port)
    except Exception as e:
        log.fatal(f"Failed to start server: {e}")
        return 1
    
    # 5. Signal readiness
    signal_ready(context)
    
    # 6. Main loop
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Received interrupt, shutting down")
    except Exception as e:
        log.error(f"Server error: {e}")
        return 1
    finally:
        shutdown_gracefully(server, soil_db, core_db)
    
    return 0
```

**Startup timing:**
- Database open: <100ms (no data)
- Schema verification: <50ms
- Server bind: <10ms
- **Total to readiness: <200ms** (fast enough for Type=simple)

**Failure modes:**

| Error Type | Exit Code | Systemd Behavior |
|------------|-----------|------------------|
| Config invalid | 1 | No restart (permanent) |
| DB locked | 1 | Restart after 5s |
| Port in use | 1 | Restart after 5s |
| DB corrupted | 1 | No restart (requires manual repair) |
| Schema mismatch | 1 | No restart (requires migration) |

### 1.4 Readiness Signaling

Readiness signaling is **context-appropriate**:

```python
def signal_ready(context: RuntimeContext):
    """
    Signal that process is ready to serve requests.
    
    Method depends on context.signal_method:
    - "systemd": sd_notify("READY=1") if NOTIFY_SOCKET present, else no-op
    - "stdout": Print ready message to terminal
    - "none": No signaling (container probes /health)
    """
    
    if context.signal_method == "systemd":
        # Optional systemd notification
        # Only if Type=notify in unit file (not required for Type=simple)
        if socket_path := os.getenv('NOTIFY_SOCKET'):
            try:
                systemd.daemon.notify("READY=1")
                log.debug("Signaled readiness to systemd")
            except Exception as e:
                log.warning(f"Failed to notify systemd: {e}")
                # Non-fatal: systemd will consider us ready anyway (Type=simple)
    
    elif context.signal_method == "stdout":
        # User process: print to terminal
        print(f"ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ MemoGarden ready at http://{config.bind_address}:{config.bind_port}")
        print(f"  Data: {context.data_dir}")
        print(f"  Logs: {context.log_dir}")
        sys.stdout.flush()
    
    elif context.signal_method == "none":
        # Container: orchestrator probes /health
        log.info("Ready - awaiting health probe")
```

**For systemd:**
- We use `Type=simple` (not `Type=notify`)
- Process running after bind_socket() = ready
- Optional `sd_notify("READY=1")` if NOTIFY_SOCKET present
- Fast startup means Type=simple is sufficient

**For containers:**
- No explicit signal
- Orchestrator uses liveness probe: `GET /health`
- Returns 200 when ready, 503 before ready

### 1.5 Shutdown Sequence

Graceful shutdown ensures data integrity:

```python
def shutdown_gracefully(server, soil_db, core_db):
    """
    Graceful shutdown sequence.
    
    Handles: SIGTERM, SIGINT, exception in main loop
    """
    
    log.info("Beginning graceful shutdown")
    
    # 1. Stop accepting new requests (close listening socket)
    try:
        server.shutdown()
        log.info("Server shutdown complete")
    except Exception as e:
        log.error(f"Error shutting down server: {e}")
    
    # 2. Flush View ringbuffer to disk (if any pending)
    try:
        flush_view_ringbuffer(core_db)
        log.info("View ringbuffer flushed")
    except Exception as e:
        log.error(f"Error flushing views: {e}")
    
    # 3. Optimize databases
    try:
        soil_db.execute("PRAGMA optimize")
        core_db.execute("PRAGMA optimize")
        log.info("Database optimization complete")
    except Exception as e:
        log.error(f"Error optimizing databases: {e}")
    
    # 4. Checkpoint WAL files
    try:
        soil_db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        core_db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        log.info("WAL checkpoint complete")
    except Exception as e:
        log.error(f"Error checkpointing WAL: {e}")
    
    # 5. Close database connections
    try:
        soil_db.close()
        core_db.close()
        log.info("Database connections closed")
    except Exception as e:
        log.error(f"Error closing databases: {e}")
    
    log.info("Shutdown complete")
```

**Shutdown timeouts per context:**

| Context | SIGTERM ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ SIGKILL | Reason |
|---------|-------------------|--------|
| serve (systemd) | 90 seconds | Default systemd TimeoutStopSec |
| run (user) | 5 seconds | Laptop sleep, user expectation |
| deploy (container) | 30 seconds | K8s default terminationGracePeriodSeconds |

**Implementation:**

```python
def setup_signal_handlers(server, soil_db, core_db):
    """Register shutdown handlers."""
    
    def handle_shutdown(signum, frame):
        log.info(f"Received signal {signum}")
        shutdown_gracefully(server, soil_db, core_db)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
```

---

## 2. Installation Process

Installation procedures create the file structures documented in RFC-004 Section 3.

**Reference:** RFC-004 Section 3 defines installation locations. This section defines installation procedures.

### 2.1 Installation Command

```bash
memogarden install [OPTIONS]

Options:
  --yes, -y
    Non-interactive mode (auto-detect profile, accept defaults)
    
  --user
    Install to user directories (~/.local) instead of system (/opt)
    
  --resource-profile {embedded|standard|auto}
    Explicitly set resource profile
    Default: prompt in interactive, auto in silent
    
  --config <path>
    Use existing config file (skip config creation)
    
  --skip-systemd
    Skip systemd unit installation (manual service management)

Examples:
  sudo memogarden install
    Interactive system installation
    
  sudo memogarden install --yes --resource-profile embedded
    Silent system installation with embedded profile
    
  memogarden install --user
    Interactive user installation
    
  memogarden install --user --yes
    Silent user installation
```

### 2.2 Interactive Installation

**System installation (`sudo memogarden install`):**

```
MemoGarden Installation
=======================

Detected existing config: /etc/memogarden/config.toml
[O]verwrite, [M]erge, [A]bort? [A]: o

Select resource profile:
  1) embedded  - Conservative resource usage (<2GB RAM)
  2) standard  - Normal resource usage (ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°Ãƒâ€šÃ‚Â¥2GB RAM)
  3) auto      - Detect based on system capabilities

Choice [3]: 3

Detecting system capabilities...
  RAM: 1.0 GB
  CPU: 4 cores

Recommended profile: embedded
Accept recommendation? [Y/n]: y

Installing MemoGarden (system, embedded profile)...
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Created directories
    /var/lib/memogarden/
    /var/log/memogarden/
    /etc/memogarden/
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Created service user: memogarden
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Installed binary: /opt/memogarden/bin/memogarden
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Created config: /etc/memogarden/config.toml (resource_profile="embedded")
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Created systemd unit: /etc/systemd/system/memogarden.service
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Reloaded systemd daemon

Installation complete!

Start MemoGarden:
  sudo systemctl start memogarden
  
View status:
  sudo systemctl status memogarden
  
View logs:
  sudo journalctl -u memogarden -f
```

**User installation (`memogarden install --user`):**

```
MemoGarden Installation (User)
===============================

Select resource profile:
  1) embedded  - Conservative resource usage
  2) standard  - Normal resource usage
  3) auto      - Detect based on system capabilities

Choice [3]: 2

Installing MemoGarden (user, standard profile)...
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Created directories
    ~/.local/share/memogarden/
    ~/.local/state/memogarden/logs/
    ~/.config/memogarden/
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Installed binary: ~/.local/bin/memogarden
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Created config: ~/.config/memogarden/config.toml (resource_profile="standard")
  ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Created systemd user unit: ~/.config/systemd/user/memogarden.service

Installation complete!

Start MemoGarden:
  systemctl --user start memogarden
  
Or run directly:
  memogarden run
```

### 2.3 Silent Installation

Silent mode auto-detects and accepts defaults:

```bash
# System installation
$ sudo memogarden install --yes
Detecting system capabilities...
8GB RAM, 8 cores detected ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ resource_profile="standard"
Installing to /opt/memogarden/
ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Installation complete

# User installation
$ memogarden install --user --yes
Detecting system capabilities...
16GB RAM, 16 cores detected ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ resource_profile="standard"
Installing to ~/.local/
ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ Installation complete
```

**Exit codes:**
- 0: Success
- 1: Failed (permission denied, disk full, etc.)
- 2: Aborted by user (interactive mode only)

### 2.4 Resource Profile Selection

**In interactive mode:**

Operator chooses:
1. `embedded` - manually selected
2. `standard` - manually selected
3. `auto` - use auto-detection with accept/reject

**In silent mode:**

Always auto-detect unless `--resource-profile` flag provided.

**Auto-detection heuristics:**

```python
def auto_detect_resource_profile() -> str:
    """
    Recommend resource profile based on system capabilities.
    
    Does NOT attempt to identify specific devices or vendors.
    Uses only: available RAM, CPU count.
    
    Returns:
        "embedded" or "standard"
    """
    import psutil
    
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count(logical=False) or 1
    
    # Threshold-based recommendation
    if total_ram_gb < 2.0:
        return "embedded"
    elif total_ram_gb < 4.0 and cpu_count <= 4:
        # Edge case: older hardware, small SBCs
        return "embedded"
    else:
        return "standard"
```

**Operator can always override:**
```bash
sudo memogarden install --yes --resource-profile embedded
# Forces embedded even if auto-detect says standard
```

### 2.5 Config File Handling

**If config already exists:**

Interactive mode prompts:
- `[O]verwrite`: Delete old config, create new one
- `[M]erge`: Update only missing keys, preserve custom values
- `[A]bort`: Exit without changes

Silent mode (`--yes`):
- Skips config creation if file exists
- To force overwrite: `--yes --config /dev/null` (creates new config)

**Config template:**

```toml
# Generated by: memogarden install
# Date: 2026-02-02T15:30:00Z
# Profile: embedded

[runtime]
resource_profile = "embedded"

[paths]
# Paths managed by installation, do not edit
# data_dir = "/var/lib/memogarden"
# config_dir = "/etc/memogarden"
# log_dir = "/var/log/memogarden"

[network]
bind_address = "127.0.0.1"
bind_port = 8080

[security]
encryption = "disabled"
```

### 2.6 Post-Installation Actions

**System installation:**
1. Create service user if not exists: `useradd -r -s /bin/false memogarden`
2. Set ownership: `chown -R memogarden:memogarden /var/lib/memogarden /var/log/memogarden`
3. Set permissions: `chmod 750 /var/lib/memogarden`, `chmod 755 /var/log/memogarden`
4. Reload systemd: `systemctl daemon-reload`

**User installation:**
1. Add `~/.local/bin` to PATH if not present (inform user)
2. Enable systemd user unit (optional, prompt user)
3. Create desktop entry (optional, prompt user)

---

## 3. Process Lifecycle & Supervision

### 3.1 systemd Integration

**serve verb (system daemon):**

```ini
# /etc/systemd/system/memogarden.service
[Unit]
Description=MemoGarden Personal Information System
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=memogarden
Group=memogarden
ExecStart=/opt/memogarden/bin/memogarden serve
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

[Install]
WantedBy=multi-user.target
```

**Restart policy:**
- `Restart=on-failure`: Restart only on non-zero exit
- `RestartSec=5s`: Wait 5 seconds between restart attempts
- systemd default: 5 restarts in 10 seconds ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ failure state

**Resource limits (optional, embedded profile):**

Can be added to unit file if needed:

```ini
[Service]
MemoryMax=512M
CPUQuota=50%
TasksMax=50
```

**But recommended approach:** Let MemoGarden self-limit based on `resource_profile` in config, not systemd cgroups. More portable across different systemd versions.

**serve verb (user daemon):**

```ini
# ~/.config/systemd/user/memogarden.service
[Unit]
Description=MemoGarden Personal Information System (User)

[Service]
Type=simple
ExecStart=%h/.local/bin/memogarden serve
WorkingDirectory=%h/.local/share/memogarden
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
```

### 3.2 Health Checks

Health check endpoint: `GET /health`

**Response format:**

```json
{
  "status": "healthy",
  "checks": {
    "soil_db": {
      "status": "ok",
      "latency_ms": 2
    },
    "core_db": {
      "status": "ok",
      "latency_ms": 1
    },
    "disk_space": {
      "status": "warning",
      "used_percent": 85
    },
    "memory": {
      "status": "ok",
      "used_mb": 150,
      "limit_mb": 512
    }
  },
  "uptime_seconds": 3600,
  "version": "0.1.0"
}
```

**Status values:**
- `healthy`: All checks OK
- `degraded`: Some warnings, but operational
- `unhealthy`: Critical failure, service non-functional

**HTTP status codes:**
- 200: `healthy` or `degraded`
- 503: `unhealthy`

**Container liveness probe:**

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 30
  timeoutSeconds: 3
  failureThreshold: 3
```

**Container readiness probe:**

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 2
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 2
```

### 3.3 Logging

**Log format:**

```
2026-02-02T15:30:00.123Z [INFO] memogarden.main: Starting MemoGarden v0.1.0
2026-02-02T15:30:00.234Z [INFO] memogarden.soil: Opened Soil database (2ms)
2026-02-02T15:30:00.345Z [INFO] memogarden.core: Opened Core database (1ms)
2026-02-02T15:30:00.456Z [INFO] memogarden.server: Listening on 127.0.0.1:8080
2026-02-02T15:30:00.567Z [INFO] memogarden.main: Ready
```

**Log destinations by context:**

| Context | Destination | Format |
|---------|-------------|--------|
| serve (systemd) | journald (stdout) | Structured |
| run (user) | File + stdout | Human-readable |
| deploy (container) | stdout | JSON |

**Log levels by profile:**

| Profile | Default Level | Console | File |
|---------|---------------|---------|------|
| embedded | WARNING | No | Yes (limited rotation) |
| standard | INFO | Optional | Yes |

**Log rotation:**

```python
# For file logging (run context)
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    log_path,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5                # Keep 5 old files
)
```

---

## 4. Concurrency & Locking

### 4.1 Single-Instance Enforcement (run context)

**Problem:** In `run` context, user may start multiple processes:
- CLI command while GUI is open
- Multiple terminal windows
- Accidental double-click on launcher

**Solution:** File-based lock + IPC socket

```python
def ensure_single_instance(context: RuntimeContext) -> Optional[socket]:
    """
    Ensure only one MemoGarden process runs in this context.
    
    Returns:
        Server socket if this is the primary instance, None if client mode
    """
    
    lock_path = context.data_dir / ".memogarden.lock"
    socket_path = context.data_dir / "memogarden.sock"
    
    try:
        # Try to acquire exclusive lock
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(lock_fd, str(os.getpid()).encode())
        
        # We're the primary instance - create IPC socket
        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(str(socket_path))
        server_sock.listen(5)
        
        log.info("Primary instance acquired lock")
        return server_sock
        
    except FileExistsError:
        # Lock exists - another process is running
        log.info("Another instance detected, entering client mode")
        
        # Connect to existing instance via socket
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client_sock.connect(str(socket_path))
            return None  # Signal: run as client, not server
        except Exception as e:
            # Socket exists but can't connect - stale lock
            log.warning(f"Stale lock detected, cleaning up: {e}")
            os.unlink(lock_path)
            os.unlink(socket_path)
            return ensure_single_instance(context)  # Retry
```

**Client mode:**

If another instance is running, subsequent invocations become clients:

```python
if server_sock is None:
    # We're a client - forward request to primary instance
    forward_to_primary(args)
    sys.exit(0)
```

**Not needed in serve/deploy contexts:**
- `serve`: systemd ensures single instance
- `deploy`: Container orchestrator ensures single pod

### 4.2 Database Lock Handling

SQLite WAL mode allows:
- Multiple concurrent readers
- One writer at a time
- Readers not blocked by writer

**Lock timeouts:**

```python
def init_database(path: Path, timeout: int = 30) -> sqlite3.Connection:
    """
    Open SQLite database with lock timeout.
    
    Args:
        path: Database file path
        timeout: Busy timeout in seconds
    """
    conn = sqlite3.connect(path, timeout=timeout)
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Set busy timeout
    conn.execute(f"PRAGMA busy_timeout={timeout * 1000}")
    
    return conn
```

**Lock contention handling:**

```python
try:
    cursor.execute(sql, params)
    conn.commit()
except sqlite3.OperationalError as e:
    if "database is locked" in str(e):
        log.warning("Database locked, retrying...")
        time.sleep(0.1)
        # Retry logic here
    else:
        raise
```

---

## 5. Resource Management

### 5.1 Storage Pressure Policies

**Monitoring:**

```python
def check_storage_pressure(data_dir: Path, config: Config) -> StoragePressure:
    """
    Check if storage is under pressure.
    
    Returns:
        StoragePressure enum: NORMAL, WARNING, CRITICAL, EMERGENCY
    """
    stat = os.statvfs(data_dir)
    
    used_percent = 1.0 - (stat.f_bavail / stat.f_blocks)
    
    if used_percent < 0.70:
        return StoragePressure.NORMAL
    elif used_percent < 0.80:
        return StoragePressure.WARNING
    elif used_percent < 0.90:
        return StoragePressure.CRITICAL
    else:
        return StoragePressure.EMERGENCY
```

**Responses by profile:**

| Profile | Threshold | Action |
|---------|-----------|--------|
| embedded | 80% | Trigger aggressive fossilization |
| embedded | 90% | Evict View ringbuffer, warn operator |
| embedded | 95% | Deny new writes, critical alert |
| standard | 90% | Trigger fossilization |
| standard | 95% | Warn operator |
| standard | 98% | Deny new writes |

**Fossilization trigger:**

```python
async def storage_pressure_task(soil_db, core_db, config):
    """Background task to monitor storage and trigger fossilization."""
    
    while True:
        pressure = check_storage_pressure(config.data_dir, config)
        
        if pressure >= StoragePressure.CRITICAL:
            log.warning(f"Storage pressure: {pressure}")
            
            # Trigger fossilization of old data
            fossilize_threshold = (
                config.fossilization_threshold 
                if pressure == StoragePressure.CRITICAL 
                else 0.5  # Emergency: more aggressive
            )
            
            await fossilize_old_data(soil_db, core_db, fossilize_threshold)
        
        await asyncio.sleep(300)  # Check every 5 minutes
```

### 5.2 Memory Management

**Tracking:**

```python
import psutil

def check_memory_usage(config: Config) -> MemoryStatus:
    """Check current memory usage against profile limits."""
    
    process = psutil.Process()
    mem_info = process.memory_info()
    
    used_mb = mem_info.rss / (1024 * 1024)
    
    # Profile-specific limits
    if config.resource_profile == "embedded":
        limit_mb = 512
    else:
        limit_mb = 2048  # Soft limit for standard
    
    return MemoryStatus(
        used_mb=used_mb,
        limit_mb=limit_mb,
        percent=used_mb / limit_mb
    )
```

**Response to memory pressure:**

embedded profile:
- Reduce View ringbuffer size
- Reduce query result cache
- More aggressive cache eviction

standard profile:
- Log warning
- Let OS handle (swap if needed)

### 5.3 Database Maintenance

**WAL checkpoint:**

```python
async def wal_checkpoint_task(soil_db, core_db, config):
    """Periodic WAL checkpoint to prevent unbounded growth."""
    
    interval = config.wal_checkpoint_interval  # 60s standard, 300s embedded
    
    while True:
        await asyncio.sleep(interval)
        
        try:
            soil_db.execute("PRAGMA wal_checkpoint(PASSIVE)")
            core_db.execute("PRAGMA wal_checkpoint(PASSIVE)")
            log.debug("WAL checkpoint complete")
        except Exception as e:
            log.error(f"WAL checkpoint failed: {e}")
```

**Integrity check:**

```python
def verify_integrity(soil_db, core_db):
    """
    Verify database integrity.
    
    Called on startup (standard profile only).
    """
    
    def check_db(conn, name):
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise DatabaseError(f"{name} integrity check failed: {result}")
    
    check_db(soil_db, "Soil")
    check_db(core_db, "Core")
    
    log.info("Database integrity verified")
```

**VACUUM:**

Not run automatically (can lock DB for long time). Manual operation:

```bash
memogarden maintain --vacuum
```

---

## 6. Failure Recovery

### 6.1 Restart Policies

**serve context (systemd):**

```ini
Restart=on-failure
RestartSec=5s
StartLimitIntervalSec=60s
StartLimitBurst=5
```

Behavior:
- Restart on non-zero exit
- Wait 5s between attempts
- Max 5 restarts in 60s window
- After limit: enters failed state, requires manual `systemctl start`

**run context:**

No automatic restart. Process exits, user must restart manually.

**deploy context (K8s):**

```yaml
spec:
  restartPolicy: Always
  # Exponential backoff: 10s, 20s, 40s, ... max 5m
```

### 6.2 Corruption Detection

**On startup:**

```python
try:
    conn = sqlite3.connect(db_path)
    
    # Quick sanity check
    conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
    
    # Full integrity check (standard profile only)
    if config.integrity_check_on_startup:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise CorruptionError(f"Database corrupt: {result}")
            
except sqlite3.DatabaseError as e:
    log.fatal(f"Database corruption detected: {e}")
    
    if config.resource_profile == "embedded":
        # Attempt recovery
        attempt_recovery(db_path)
    else:
        # Fail fast
        sys.exit(1)
```

**Recovery (embedded profile only):**

```python
def attempt_recovery(db_path: Path):
    """
    Attempt to recover from database corruption.
    
    Only used in embedded profile (SD card corruption risk).
    """
    backup_path = db_path.with_suffix('.db.corrupt')
    
    # Backup corrupted DB
    shutil.copy(db_path, backup_path)
    log.warning(f"Backed up corrupt DB to {backup_path}")
    
    # Try .dump recovery
    try:
        subprocess.run([
            "sqlite3", str(backup_path),
            ".recover"
        ], stdout=open(db_path, 'w'), check=True)
        
        log.info("Recovery successful")
        
    except Exception as e:
        log.fatal(f"Recovery failed: {e}")
        log.fatal("Manual intervention required")
        sys.exit(1)
```

### 6.3 Degraded Mode

**Not implemented.** MemoGarden requires databases to function.

Future consideration: read-only mode if write fails.

---

## 7. System Operating Modes

MemoGarden operates in one of three modes that reflect system health and capability. The operating mode is determined at startup based on consistency checks and can be changed by operator intervention.

### 7.1 Mode Definitions

| Mode | Description | Capabilities | Use Cases |
|------|-------------|--------------|-----------|
| **NORMAL** | Healthy operation | Full read/write access to both Soil and Core | Standard operation |
| **READ-ONLY** | Maintenance/recovery mode | Queries allowed, mutations blocked | Backup, maintenance, investigation |
| **SAFE MODE** | Degraded/inconsistent state | Limited operations, diagnostics enabled | Recovery from crash, inconsistency detected |

### 7.2 Mode Transitions

**Automatic transitions (system-initiated):**

Startup sequence determines initial mode:
- No issues detected Ã¢â€ â€™ NORMAL
- Orphaned deltas detected Ã¢â€ â€™ SAFE MODE
- Hash chain broken Ã¢â€ â€™ SAFE MODE
- Database corruption Ã¢â€ â€™ SAFE MODE

Runtime transitions:
- NORMAL Ã¢â€ â€™ SAFE MODE: Transaction commit failure (Soil commits, Core fails)
- SAFE MODE Ã¢â€ â€™ NORMAL: After successful `memogarden repair`

**Manual transitions (operator-initiated):**

```bash
# Enter read-only mode for maintenance
memogarden mode set readonly

# Return to normal after maintenance
memogarden mode set normal

# Force safe mode for investigation
memogarden mode set safe
```

### 7.3 Startup Consistency Checks

On startup, MemoGarden performs quick consistency checks:

**Fast checks (< 1 second):**
1. Database files readable and not corrupted
2. Cross-database delta consistency (orphaned EntityDeltas)
3. SQLite integrity quick check

**Startup sequence:**
```python
def startup():
    """MemoGarden startup with mode detection."""
    
    # Open databases (always succeeds, may return None if corrupted)
    soil = open_database('soil.db')
    core = open_database('core.db')
    
    if soil is None or core is None:
        mode = SystemStatus.SAFE_MODE
        logger.error("Database corruption detected")
    else:
        issues = quick_consistency_check(soil, core)
        mode = SystemStatus.NORMAL if not issues else SystemStatus.SAFE_MODE
        
        if issues:
            logger.warning(f"Inconsistencies detected: {len(issues)}")
    
    logger.info(f"Starting in {mode.value} mode")
    return MemoGarden(soil, core, mode)
```

### 7.4 Recovery Workflow

Typical recovery from SAFE MODE:

```bash
# 1. Investigate issues
$ memogarden diagnose

# 2. Execute repair
$ memogarden repair

# System automatically transitions to NORMAL after successful repair
```

For detailed consistency guarantees and failure modes, see RFC-008 (Transaction Semantics).

---

## 8. Monitoring & Observability

MemoGarden uses a three-layer observability model:

### 8.1 Observability Layers

**Layer 1: MemoGarden Facts (Semantic Data)**
- **Action facts:** All Semantic API calls (reads/writes, success/failure)
- **EntityDelta facts:** Data mutations with actor attribution
- **SystemEvent facts:** Operational state changes (mode transitions, consistency checks, backups, critical alerts)
- **Purpose:** Queryable by agents and operators via Semantic API
- **Storage:** Soil database, subject to fossilization

**Layer 2: Internal Logs (Technical Troubleshooting)**
- Internal API call traces
- SQL queries and transaction boundaries
- Stack traces on errors
- Performance timing (query latency, lock contention)
- Log levels: DEBUG/INFO/WARNING/ERROR
- **Output:** journald (systemd) or stderr
- **Rotation:** Monthly, retention 1-2 years
- **Purpose:** Advanced troubleshooting by technically inclined operators

**Layer 3: OS Logs (Infrastructure)**
- Service lifecycle (start/stop/restart)
- Resource exhaustion (OOM, disk full)
- Hardware issues
- **Output:** systemd journal
- **Purpose:** System administration, not MemoGarden's concern

### 8.2 System Agent

The **system agent** is a privileged, rule-based component responsible for MemoGarden's autonomic survivability. It implements cybernetic control loops that monitor system health and execute recovery protocols.

**Key characteristics:**
- **Rule-based:** No LLM required (resource-constrained hardware compatible)
- **Privileged access:** Internal metrics APIs not available through Semantic API
- **Predetermined algorithms:** SPC-based monitoring, threshold detection, recovery protocols
- **Context exposure:** Writes health summaries to its memory block visible to conversational agents

**System agent responsibilities:**

1. **Metrics collection and analysis**
   - Storage health (disk usage, growth rate projection)
   - Performance (query latency, transaction commit time)
   - Reliability (failure rates, lock conflicts)
   - Resource health (SSD SMART attributes, thermal throttling)

2. **Anomaly detection via SPC**
   - Moving average with 3Ïƒ thresholds
   - Exponential smoothing for trend detection
   - Control charts for process stability monitoring

3. **Recovery protocol execution**
   - Automatic responses to detected conditions
   - Escalation to operator when auto-recovery insufficient
   - Logging SystemEvent facts for audit trail

### 8.3 Metrics Implementation

**Storage architecture:**
- **In-memory:** Last N samples for SPC algorithms (sliding window)
- **Journald:** Periodic snapshots via structured logging
- **Not in Soil:** High-frequency metrics would pollute semantic data

**Metrics collected:**

| Metric | Sample Frequency | Window Size | Purpose |
|--------|------------------|-------------|---------|
| Disk usage (Soil) | 5 minutes | 24 hours | Storage pressure detection |
| Disk usage (Core) | 5 minutes | 24 hours | Storage pressure detection |
| Available disk space | 5 minutes | 24 hours | Capacity planning |
| Query latency (p50/p95/p99) | Per query | Last 1000 queries | Performance monitoring |
| Transaction commit time | Per transaction | Last 1000 commits | Performance monitoring |
| Transaction failure rate | Per transaction | Last 1000 transactions | Reliability monitoring |
| Optimistic lock conflicts | Per conflict | 24 hours | Concurrency issue detection |
| Consistency check duration | Per startup | Last 30 days | Health monitoring |
| SSD wear level | Hourly | 30 days | Hardware health |

**SPC algorithm parameters:**
- **Control limits:** Î¼ Â± 3Ïƒ (99.7% confidence)
- **Trend detection:** Exponential smoothing Î±=0.3
- **Window size:** Metric-dependent (see table above)
- **Alert threshold:** 2 consecutive samples outside control limits OR 7 consecutive samples showing trend

### 8.4 Recovery Protocols

The system agent implements predetermined responses to detected conditions:

**Disk >85% full:**
```
Actions:
1. Log WARNING to journald
2. Trigger aggressive fossilization sweep
3. Create SystemEvent fact: "storage_pressure"
4. If >95% full: Create SystemEvent fact with severity=critical, alert operator
```

**Transaction failure rate >5%:**
```
Actions:
1. Log ERROR to journald
2. Enter READ_ONLY mode (prevent further failures)
3. Create SystemEvent fact: "transaction_failure_spike"
4. Alert operator immediately
5. Wait for operator intervention (memogarden diagnose/repair)
```

**Query latency p95 >2x baseline:**
```
Actions:
1. Log WARNING to journald
2. Continue monitoring
3. If persists >1 hour:
   - Create SystemEvent fact: "performance_degradation"
   - Alert operator
4. Suggest operator actions: check disk I/O, run consistency check
```

**Startup consistency check finds orphaned deltas:**
```
Actions:
1. Enter SAFE_MODE
2. Create SystemEvent fact: "consistency_failure"
3. Log ERROR to journald with diagnostic details
4. Block mutations until operator runs: memogarden repair
```

**SSD wear level critical (>90% lifetime writes):**
```
Actions:
1. Create SystemEvent fact: "hardware_failure_imminent"
2. Alert operator immediately
3. No auto-recovery available (hardware replacement required)
```

### 8.5 Operator Access to Metrics

Operators can view metrics and system health through standard OS tools:

```bash
# View MemoGarden service logs
journalctl -u memogarden -f

# Check service status and recent events
systemctl status memogarden

# Search for specific event types
journalctl -u memogarden | grep "storage_pressure"

# View system agent health summary
memogarden status
```

System agent also writes health summary to its Letta memory block, making it visible to conversational agents in context.

### 8.6 Agent Context Exposure

Conversational agents see system health in their context but don't query metrics directly:

```
System Health: NORMAL
Disk usage: 67% (trend: +2%/week, projected full in 16 weeks)
Transaction success rate: 99.8%
Query latency p95: 45ms (baseline: 40ms)
Last consistency check: 2026-02-06 03:00 - PASS
```

Agents can reference this information when answering operator questions but cannot access raw metric time series or trigger recovery protocols (those are system agent privileges).

### 8.7 Prometheus Metrics Endpoint (Optional)

For operators who want to integrate with external monitoring systems (Grafana, Prometheus), MemoGarden can optionally expose a `/metrics` endpoint in Prometheus format.

**Configuration:**
```toml
[monitoring]
prometheus_enabled = false  # Default: disabled
prometheus_port = 9090      # Separate port from main API
```

**Example metrics:**
```
# HELP memogarden_uptime_seconds Process uptime
# TYPE memogarden_uptime_seconds gauge
memogarden_uptime_seconds 3600

# HELP memogarden_db_size_bytes Database file size
# TYPE memogarden_db_size_bytes gauge
memogarden_db_size_bytes{db="soil"} 10485760
memogarden_db_size_bytes{db="core"} 5242880

# HELP memogarden_query_latency_seconds Query latency percentiles
# TYPE memogarden_query_latency_seconds summary
memogarden_query_latency_seconds{quantile="0.5"} 0.023
memogarden_query_latency_seconds{quantile="0.95"} 0.045
memogarden_query_latency_seconds{quantile="0.99"} 0.089
```

**Note:** This is optional infrastructure. The system agent's internal metrics collection and SPC monitoring work independently of Prometheus integration.

---

## 9. Open Questions

1. **Watchdog integration:** Should embedded profile use systemd watchdog (`WatchdogSec=30`)?
   - **Recommendation:** Yes for Device profile on real embedded hardware

2. **Cluster mode:** Future support for multiple instances with shared storage?
   - **Deferred:** SQLite doesn't support this well

3. **Hot reload:** Config changes without restart?
   - **Deferred:** Restart is fast enough (<200ms)

4. **Blue/green deployments:** Zero-downtime updates?
   - **Deferred:** Personal system, downtime acceptable

---

## 10. Future Work

### 9.1 Backup Automation

Schedule backups via systemd timer:

```ini
# /etc/systemd/system/memogarden-backup.timer
[Unit]
Description=MemoGarden Daily Backup

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

### 9.2 Remote Monitoring

Push metrics to remote monitoring:
- Prometheus pushgateway
- Grafana Cloud
- Custom webhook

### 9.3 Auto-Updates

Check for updates and prompt user:
- System: via apt/yum
- User: via self-update command
- Container: via image registry

---

## References

- RFC-001 v4: Security & Operations Architecture
- RFC-004 v2: Package Structure & Deployment
- RFC-005 v3: API Design
- systemd documentation: https://systemd.io/
- SQLite WAL mode: https://sqlite.org/wal.html

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-02 | Initial draft |
| 2.0 | 2026-02-02 | Added Section 7: System Operating Modes (NORMAL/READ-ONLY/SAFE MODE) |
| 2.1 | 2026-02-06 | Rewrote Section 8: Monitoring & Observability with three-layer model, system agent architecture, SPC metrics implementation, and recovery protocols |

---

**Status:** Draft  
**Next Steps:**
1. Review startup/shutdown sequences
2. Review resource profile behaviors
3. Review installation UX
4. Implement single-instance locking
5. Implement health check endpoint
6. Test across serve/run/deploy contexts

---

**END OF RFC**