# RFC-001: MemoGarden Security & Operations Architecture

**Version:** 4.0  
**Status:** Draft  
**Author:** MemoGarden Project  
**Created:** 2025-01-09  
**Last Updated:** 2025-01-20

## Abstract

This RFC specifies the security architecture and operational design for MemoGarden across three deployment profiles: device (dedicated hardware), system (shared server), and personal (desktop/laptop). The **system profile is the default target**; device profile adds a watchdog layer for always-on operation. Each profile makes different assumptions about hardware access, resource priority, and security requirements while sharing a common core architecture.

## Motivation

MemoGarden operates as a personal information substrate supporting human-AI collaboration. The system must:

1. **Protect data integrity** across varying deployment contexts
2. **Enable agent autonomy** within appropriate security boundaries
3. **Support recovery** from failures and mistakes
4. **Adapt to constraints** imposed by different deployment environments
5. **Maintain operator sovereignty** over personal data regardless of deployment model

A single software edition supports all profiles through configuration, not separate builds.

---

## 1. Deployment Profiles

### 1.1 Profile Definitions

| Profile | Hardware | Access | Users | Availability | Examples |
|---------|----------|--------|-------|--------------|----------|
| **Device** | Dedicated device | Full hardware access | Single operator | 24/7 | Raspberry Pi, home server |
| **System** | Shared server | Admin-managed | Multiple operators | 24/7, shared resources | DGX Spark, research server |
| **Personal** | Desktop/laptop | User-gated | Single user | Intermittent, graceful shutdown | Laptop, desktop |
| **Satellite** | Mobile/secondary | Limited | Single operator | Opportunistic | Smartphone, tablet (future) |

**Default target: System profile.** This is the baseline implementation. Device profile adds watchdog capabilities. Personal profile removes multi-operator overhead.

### 1.2 Profile Selection

Profile is set via configuration, with auto-detection as fallback:

- Running as system service with dedicated user + watchdog enabled â†’ Device
- Running as system service, cgroup-constrained or multi-user â†’ System  
- Running as user service or foreground process â†’ Personal
- Explicit `profile = "device|system|personal"` overrides detection

### 1.3 System Profile (Default)

**Assumptions:**
- Shared with other services/software
- Sysadmin manages system, may not be operator
- Must respect resource quotas and cgroup limits
- Multiple operators possible, each with own data
- Network security delegated to infrastructure
- Containerization common

**Implications:**
- Yield to higher-priority processes
- No watchdog by default; monitoring via external tools
- ACLs enable backup/monitoring service access
- Per-operator resource tracking and quotas
- Graceful degradation when resources scarce
- Optimized code paths for single-operator case

### 1.4 Device Profile

**Assumptions:**
- Entire system dedicated to MemoGarden
- Operator has root access
- Can monopolize resources (80%+ CPU, most RAM)
- Always-on operation expected
- Network via Tailscale (encrypted overlay)
- User data treated as system data (maintained by system utilities)

**Implications:**
- All System profile capabilities, plus:
- Watchdog daemon with sudo privileges for maintenance
- Aggressive caching and deferred writes acceptable
- Full integrity checks run on schedule
- Hardened security posture (defense in depth)

### 1.5 Personal Profile

**Assumptions:**
- Shared with primary user software (IDE, browser, etc.)
- Hardware access may be user-gated (UAC, polkit)
- Power constraints (battery, thermal)
- Unpredictable but graceful shutdown expected
- Single operator only (multi-operator overhead removed)
- Lower security guarantees acceptable (external attackers, not co-users)

**Implications:**
- Aggressive disk flush (writes not deferred)
- Tasks run interruptibly and opportunistically
- Heavy integrity checks skipped or sampled
- Battery-aware operation (suspend indexing on battery)
- Stricter resource bounds
- Simplified authentication (no multi-operator machinery)

### 1.6 Satellite Profile (Future)

**Assumptions:**
- Secondary device paired with device-profile primary
- Local cache only; authoritative data on primary
- Sync protocol handles conflicts
- Operates offline, reconciles when connected

**Implications:**
- Evolves from personal profile
- Requires sync protocol specification (separate RFC)
- Local operations are provisional until sync confirmed

---

## 2. Storage Architecture

### 2.1 Two-Layer Model (All Profiles)

**Soil (Immutable Facts)**
- SQLite database (optionally SQLCipher encrypted)
- All Items, system relations
- Append-only (5-minute undo window excepted)
- Source of truth for timeline

**Core (Mutable State)**
- SQLite database (optionally SQLCipher encrypted)
- Artifacts, user relations, active grants, ContextFrames
- User-controllable belief layer
- Time horizon decay for relations

### 2.2 Directory Layout by Profile

**Device:**
```
/var/lib/memogarden/          Data (system-owned)
/etc/memogarden/              Config (admin-editable)
/opt/memogarden/              Software
/var/log/memogarden/          Logs
/run/memogarden/              Runtime (PID, sockets)
```

**System (Native):**
```
/var/lib/memogarden/          Data (ACLs for backup access)
/etc/memogarden/              Config
/opt/memogarden/              Software
```

**System (Container):**
```
/data/                        Data (mount from host)
/config/                      Config (mount or ConfigMap)
/app/                         Software (in image)
```

**Personal:**
```
~/MemoGarden/                 Data (user-owned)
  or XDG: ~/.local/share/memogarden/
~/.config/memogarden/         Config
```

### 2.3 Rationale

Device/System profiles use `/var/lib` because:
- FHS-compliant for system services
- Backup tools expect database state there
- Systemd `StateDirectory=` auto-creates with correct ownership

Personal profile uses user-space because:
- Personal data semantically belongs to user
- No sudo required for backup/migration
- Portable across reinstalls if home preserved

Container internal paths are abstract; host mounts from anywhere.

---

## 3. User Account Model

### 3.1 Device Profile

| Account | Role | Privileges |
|---------|------|------------|
| `operator` | Human owner | sudo access, root of trust |
| `memogarden` | API server | Owns databases, no sudo |
| `mgsystem` | Watchdog | Limited sudo (vetted scripts only) |

**Rationale for separation:**
- `killall -u mgsystem` stops watchdog without affecting core
- Clear attribution in system logs
- Per-user resource limits possible
- Compromised watchdog cannot access databases directly

### 3.2 System Profile

| Account | Role | Privileges |
|---------|------|------------|
| `memogarden` | API server | Owns data, respects quotas |
| Operators | Human users | Access via API only |
| Sysadmin | System management | Can read logs/metrics, manage service |

**No `mgsystem` account:** Watchdog is optional; if enabled, runs unprivileged (monitor-only) or sysadmin configures separately.

**Multi-operator:** Each operator authenticated, accesses only their data partition. Single-operator installations skip multi-operator overhead via optimized code paths.

### 3.3 Personal Profile

| Account | Role | Privileges |
|---------|------|------------|
| User | Operator + owner | Runs service, owns data |

**No separation:** Service runs as user via `systemd --user` or foreground process. Data in user's home directory. No multi-operator support.

---

## 4. Authentication & Authorization

### 4.1 API Key Model (All Profiles)

MemoGarden uses opaque API keys with database-backed validation.

**Key structure:** `mg_key_<random_256_bit_hex>`

**Key record fields:**
- `key_hash`: SHA256 of key (key never stored)
- `participant_id`: Agent or service identifier
- `operator_id`: Which operator's data (system profile with multi-operator)
- `baseline_scopes`: Permanent permissions
- `allowable_scopes`: Can be granted temporarily
- `expires_at`: Auto-rotation (30 days default)

### 4.2 Scope Model

**Syntax:** `<resource>:<action>[:<specifier>]`

**Examples:**
- `tool:artifact_read` - Specific tool
- `tool:*` - All tools
- `!tool:system:*` - Deny system tools

**Deny takes precedence** over allow.

### 4.3 Time-Limited Grants

Scopes beyond baseline require explicit grants with expiration. Grants are linked to `participant_id`, surviving key rotation.

### 4.4 Multi-Operator Authorization (System Profile)

API key includes `operator_id`. All data access validated:
- Key's `operator_id` must match resource's `operator_id`
- Cross-operator access forbidden at API layer
- Integrity checks verify isolation (per-request or sampled)

**Single-operator optimization:** When only one operator exists, `operator_id` checks become no-ops.

### 4.5 Admin Account (System Profile)

Separate admin account for system operations:
- Manages operators, quotas, grants
- Cannot access operator data without explicit delegation
- Requires elevation (like sudo) for destructive actions
- Transferable via credential sharing

---

## 5. Tool Execution Model

### 5.1 Core Principle (All Profiles)

**All agent actions go through tools.** Agents cannot:
- Execute shell commands directly
- Access databases directly
- Modify files directly

**All tool calls logged to Soil** as ToolCall Items, providing complete audit trail.

### 5.2 Idempotency

Artifact writes use hash-based idempotency:
- Client sends `prev_hash` of expected current state
- Server rejects if actual hash differs (conflict)
- Identical content = no-op (safe retry)

### 5.3 Tool Registry

Tools declare:
- Required scopes
- Timeout
- Idempotency status

Enforcement is profile-independent; tool availability may vary.

### 5.4 Agent Budget (Operator Policy)

Agent resource consumption is operator-configurable policy, not architectural constraint:

```python
@dataclass
class AgentBudget:
    window_hours: int
    max_llm_tokens: int
    current_spend: int
    window_reset_at: datetime
    behavior_on_exhaust: str  # 'block' | 'notify_operator' | 'allow_overflow'
```

Synchronous tool calls are self-throttling (agent waits for response). Asynchronous operations (if any) use task queue with sequential execution.

---

## 6. Encryption & Key Management

### 6.1 Design Philosophy

**Availability over confidentiality.** MemoGarden prioritizes data accessibility:
- Default: No encryption (rely on device-level full-disk encryption)
- Optional: SQLCipher with operator-managed key
- No automatic recovery mechanismâ€”operator is responsible for key management

**Rationale:** Personal systems fail permanently when encryption keys are lost. Device-level FDE (FileVault, LUKS, BitLocker) provides primary protection. SQLCipher adds defense-in-depth for those who want it.

### 6.2 Encryption Scope

**Databases:** SQLCipher encrypted (optional)  
**Files:** Not encrypted (rely on full-disk encryption as fallback)

### 6.3 Device Profile: Optional Shamir's Secret Sharing

For operators who want key redundancy, Shamir's 2-of-4 sharing available:

| Share | Location | Unlock Method |
|-------|----------|---------------|
| A | Server filesystem | Automatic on startup |
| B | Operator memory | Passphrase entry |
| C | Hardware token | YubiKey/FIDO2 tap |
| D | Paper backup | Manual entry |

**Normal operation:** A + (B or C or D)  
**Recovery:** Any two shares reconstruct key

**This is opt-in.** Default device profile uses no encryption.

### 6.4 System Profile: Sysadmin-Managed Key

If encryption enabled:
- Sysadmin manages key via environment variable or secrets manager
- Operators authenticated at API layer, not encryption layer
- Lower isolation guarantee (trusted co-operators)
- Simpler key management for shared environments

### 6.5 Personal Profile: Passphrase Mode

If encryption enabled:
- SQLCipher key derived from passphrase (Argon2)
- Paper backup key recommended
- No hardware token or cloud registry required
- Security priority: external attackers, not co-users

### 6.6 No Progressive Decryption

**Eliminated from design.** If encryption key is lost, data is lost. MemoGarden does not implement automatic decryption fallback.

**Rationale:** Progressive decryption (automatically decrypting after failed recovery attempts) undermines the security guarantee encryption provides. Operators who enable encryption are responsible for key management.

---

## 7. Network Security

### 7.1 Device Profile: Tailscale Recommended

- Bind only to Tailscale interface (when available)
- WireGuard encryption for all traffic
- NAT traversal handled
- ACLs restrict device access
- Fallback to localhost if Tailscale unavailable

### 7.2 System Profile: Infrastructure-Managed

- Bind to `0.0.0.0` or configured interface
- Trust service mesh (Istio/Linkerd) for mTLS
- Validate `X-Forwarded-For` from trusted proxies
- Network security delegated to infrastructure

### 7.3 Personal Profile: Localhost Default

- Bind to `127.0.0.1` by default
- Tailscale optional for remote agent access
- LAN access configurable with auth required
- Auto-increment port if default taken

---

## 8. Watchdog & Maintenance

### 8.1 Device Profile: Full Watchdog

FSM-based daemon (no LLM) performing:
- Resource monitoring
- Pre-vetted maintenance scripts (via limited sudo)
- Heartbeat logging
- Alert on anomalies

**Emergency stop:** Flag in Core; watchdog checks each iteration.

**This is what distinguishes Device from System profile.** The watchdog layer enables autonomous maintenance for always-on operation.

### 8.2 System Profile: External Monitoring

- No built-in watchdog
- Sysadmin uses external monitoring (Prometheus, Datadog, etc.)
- MemoGarden exposes metrics endpoint
- Alert integration via standard protocols

### 8.3 Personal Profile: No Dedicated Watchdog

- GUI application handles monitoring if needed
- Battery-aware operation (suspend heavy tasks)
- Graceful handling of sleep/wake cycles

---

## 9. Resource Management

### 9.1 Device Profile: Aggressive

- Use 80%+ of available resources
- Defer writes for performance
- Full integrity checks on schedule
- Assume resources available on demand

### 9.2 System Profile: Defensive

- Read and respect cgroup limits
- Yield to higher-priority processes
- Per-operator quotas enforced
- Shared resource use reported separately
- Graceful degradation under pressure

### 9.3 Personal Profile: Opportunistic

- Conservative defaults (25% CPU, 2GB RAM)
- Battery-aware (suspend indexing/embedding on battery)
- Tasks run interruptibly
- Stricter bounds on all operations
- Write amplification acceptable for durability

---

## 10. Backup & Recovery

### 10.1 Device Profile: System Utility

Backup via system utilities (treated as system data):
- `memogarden backup` command with verification
- SQLite-aware (WAL checkpoint before backup)
- Operator manages schedule and destination

### 10.2 System Profile: Sysadmin Orchestrated

MemoGarden provides hooks only:
- `backup-prepare.sh`: Checkpoint databases
- `backup-complete.sh`: Release locks
- Sysadmin integrates with Restic/Borg/etc.

**Per-operator granularity:** Backup/restore individual operator data possible.

### 10.3 Personal Profile: User Initiated

- Simple: `tar czf backup.tar.gz ~/MemoGarden`
- `memogarden backup` available for consistency
- GUI application may automate

---

## 11. Integrity & Verification

### 11.1 Verification Strategy (All Profiles)

- Items include `integrity_hash` (SHA256 of content)
- Verified on access (detect corruption early)
- Failed verification logged, operator notified

### 11.2 Device Profile: Full Checks

- Scheduled comprehensive integrity sweeps
- All relations verified
- Anomalies trigger alerts

### 11.3 System Profile: Full Checks + Isolation Audit

Same as device, plus:
- Verify data access matches operator_id
- Per-request validation or sampled log audit
- Cross-operator access attempts logged as security events

### 11.4 Personal Profile: Reduced Checks

- Computationally intensive checks skipped or sampled
- Focus on detecting obvious corruption
- Full checks run opportunistically (plugged in, idle)

---

## 12. Multi-Operator Considerations (System Profile)

### 12.1 Data Isolation

- Separate data directories per operator
- API key determines operator context
- All queries scoped to operator's data
- No cross-operator relations possible

### 12.2 Resource Accounting

- Per-operator storage quotas
- Per-operator API rate limits
- Per-operator metrics exposed
- Shared resources (CPU, memory) reported separately

### 12.3 Backup Granularity

- Admin can backup/restore individual operators
- Operator can backup own data (if permitted)
- System-wide backup includes all operators

### 12.4 Administration

- Admin account separate from operator accounts
- Elevation required for system changes
- Admin cannot read operator data without delegation
- Onboarding/offboarding procedures (deferred)

### 12.5 Single-Operator Optimization

When only one operator exists:
- `operator_id` validation becomes no-op
- Per-operator isolation overhead skipped
- Equivalent performance to personal profile with system profile durability

---

## 13. External Integration

### 13.1 Logging (All Profiles)

- Structured JSON to stdout
- Sysadmin routes (journald, file, aggregator)
- Fields: timestamp, level, operator (if applicable), event, details

### 13.2 Metrics (All Profiles)

- Prometheus endpoint at `/metrics`
- Standard metrics: items_total, api_latency, active_agents
- Per-operator labels where applicable
- Endpoint optional (configurable)

### 13.3 Reverse Proxy (System Profile)

- Example configs provided (nginx, Caddy)
- WebSocket support required
- TLS termination at proxy acceptable

### 13.4 Container Support (System Profile)

- Official Docker image available
- Standard volume mounts (`/data`, `/config`)
- Non-root container user
- K8s manifests provided as examples
- Single replica only (SQLite constraint)

### 13.5 Proxy Support (All Profiles)

- Honor `HTTP_PROXY`, `HTTPS_PROXY` environment variables
- Basic proxy authentication only
- No NTLM or TLS inspection workarounds

---

## 14. Platform Considerations (Personal Profile)

### 14.1 Cross-Platform Paths

Single config schema with `"auto"` values resolving per-platform:
- Linux: XDG Base Directory Specification
- macOS: `~/Library/Application Support/MemoGarden`
- Windows: `%LOCALAPPDATA%\MemoGarden`

### 14.2 Platform-Specific Behavior

Deferred to GUI application:
- Windows: UAC, Defender exclusions
- macOS: Keychain integration, notarization
- Linux: Autostart mechanism

### 14.3 Cloud Storage Warning

SQLite in Dropbox/iCloud/OneDrive is dangerous. MemoGarden:
- Does not prevent (user's choice)
- Does not support (undefined behavior if conflicts occur)

---

## 15. Configuration Reference

### 15.1 Format

TOML for all configuration files.

### 15.2 Key Settings

```toml
[deployment]
profile = "auto"          # "device", "system", "personal", or "auto"

[storage]
data_dir = "auto"         # Platform-specific default

[network]
bind_address = "auto"     # Profile-specific default
bind_port = 8080

[resources]
max_memory_mb = "auto"    # Profile-specific default
max_cpu_percent = "auto"

[security]
encryption = "disabled"   # "disabled", "optional", "required"
# If encryption = "optional" or "required":
# key_source = "passphrase" | "env" | "shamir"

[watchdog]
enabled = "auto"          # true for device profile, false otherwise
```

### 15.3 Encryption Configuration Examples

**No encryption (default):**
```toml
[security]
encryption = "disabled"
```

**Passphrase encryption (personal profile):**
```toml
[security]
encryption = "required"
key_source = "passphrase"
```

**Environment variable (system profile, container):**
```toml
[security]
encryption = "required"
key_source = "env"
key_env_var = "MEMOGARDEN_DB_KEY"
```

**Shamir's Secret Sharing (device profile):**
```toml
[security]
encryption = "required"
key_source = "shamir"
shamir_threshold = 2
shamir_shares = ["filesystem", "passphrase", "yubikey", "paper"]
```

---

## 16. Deferred Items

| Item | Status | Notes |
|------|--------|-------|
| Satellite profile | Future RFC | Requires sync protocol |
| Corruption recovery | Future RFC | Complex topic |
| Agent failure handling | KIV | Need usage data |
| Onboarding/offboarding | Deferred | UI/UX decisions needed |
| Export formats | KIV | Data portability |
| Multi-device sync | KIV | Related to satellite |

---

## 17. Ecosystem Context

MemoGarden serves as the data substrate for the AIAS (AI Assistive System) vision:
- Applications use MemoGarden API instead of siloed storage
- Agents coordinate through MemoGarden's tool execution model
- Personal data remains under operator control regardless of which apps access it
- Letta (or other agent runtimes) serve as execution layer; MemoGarden provides persistence

This RFC focuses on MemoGarden core; application integration patterns will be separate documents.

---

## 18. Eliminated Concepts

The following concepts from earlier designs have been removed:

| Concept | Previous Version | Reason for Elimination |
|---------|------------------|------------------------|
| Progressive decryption | v3.0 | Undermines security guarantee; availability achieved by defaulting to no encryption |
| Encryption required by default | v3.0 | Availability > confidentiality for personal systems; FDE provides primary protection |
| High/Mid/Low naming | v3.0 | Renamed to Device/System/Personal for clarity |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-09 | Initial draft (device deployment only) |
| 2.0 | 2025-01-09 | Security architecture, agent coordination |
| 3.0 | 2025-01-19 | Multi-profile architecture (high/mid/low availability), cross-platform support, multi-operator considerations |
| 4.0 | 2025-01-20 | **Design review integration:** System profile as default target; Device adds watchdog layer; Encryption default = disabled (availability priority); Progressive decryption eliminated; Profile names changed (Device/System/Personal); Single-operator optimization; Agent budget as operator policy |

---

**Status:** Draft  
**Next Steps:**
1. Prototype profile auto-detection
2. Implement single-operator optimization paths
3. Develop per-profile installation guides
4. Design satellite sync protocol (separate RFC)

---

**END OF RFC**
