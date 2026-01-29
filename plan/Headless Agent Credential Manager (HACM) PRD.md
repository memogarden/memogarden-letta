# Product Requirements Document (PRD)

## Product Name

Headless Agent Credential Manager (HACM)

## Purpose

Provide a secure, reliable, non-interactive credential management system for long-running agent loops on headless Linux systems (e.g., Raspberry Pi) without reliance on desktop environments, OS keychains, or external secret daemons.

The system must support OAuth-based services (e.g., GitHub, Google) and service-account-style credentials while prioritizing robustness, determinism, and recoverability over convenience.

---

## Non-Goals

* Emulating desktop keychains (Secret Service API, gnome-keyring, KWallet)
* Supporting GUI-based unlock flows
* Acting as a general-purpose secret vault for unrelated applications
* Multi-user isolation on the same host
* Running outside a supervised init system (e.g., manual shell launch)

---

## Target Environment

* Hardware: Raspberry Pi (ARM64/ARMv7)
* OS: Headless Linux (Arch ARM, Raspberry Pi OS Lite, Debian minimal)
* Runtime supervisor: **systemd (mandatory)**
* Execution model: single long-running process
* No desktop environment
* No D-Bus assumptions

---

## Threat Model

### In Scope

* Disk theft / offline access
* Accidental logging of secrets
* Power loss during write
* Process crash or restart

### Out of Scope

* Physical adversary with live root access
* Kernel compromise
* Side-channel attacks

---

## Core Design Principles

1. Explicit over implicit
2. Deterministic startup and recovery
3. No background daemons
4. No interactive unlock requirements during normal operation
5. Minimal trusted computing base
6. Atomic and auditable state transitions

---

## Functional Requirements

### FR-1: Credential Abstraction Layer

Provide a clear interface:

* `load()` – Load and decrypt stored credentials
* `get(id)` – Retrieve credential material by logical ID (mapping-style lookup)
* `put(id, value)` – Store or update credential
* `delete(id)` – Remove credential
* `list()` – Enumerate stored credential IDs

**Interface Design:** Mapping-style lookup by unique credential ID. On-disk storage uses
object/mapping format with credential IDs as keys, enabling O(1) direct access without
in-memory indexing. Natural mapping interface matches storage structure.

The abstraction must be backend-agnostic.

---

### FR-2: Encrypted File Backend (Primary)

* Credentials stored in a single encrypted file

* File location configurable (default: `/var/lib/agent/credentials.enc`)

* Encryption:

  * libsodium (XSalsa20-Poly1305 or equivalent AEAD)
  * Authenticated encryption mandatory

* Encryption key derivation:

  * Input material:

    * `/etc/machine-id`
    * static application salt
    * optional operator-provided passphrase
  * Key derivation via HKDF or Argon2

---

### FR-3: Credential Types Supported

* OAuth refresh tokens
* OAuth client credentials (where applicable)
* Service account private keys
* Arbitrary opaque secrets

Access tokens:

* Must never be persisted
* Memory-only lifetime

---

### FR-4: Atomic Persistence

* All writes must be atomic:

  * write to temp file
  * fsync
  * rename
* Partial writes must not corrupt existing data
* On startup, system must recover cleanly from interrupted writes
* **Order Preservation:** Serialization must use deterministic key ordering (alphabetically
  sorted) to ensure reproducible output. This enables consistent auditing, file hashing, and
  encryption validation. Timestamps (created_at, updated_at) remain the authoritative
  source of temporal ordering.

---

### FR-5: Auto-Refresh Support

* Provide metadata fields per credential:

  * expiry timestamp
  * refresh endpoint (optional)
  * scope

* Credential manager must:

  * expose expiry metadata
  * allow a single refresh worker to update credentials
  * prevent concurrent refresh storms (single-flight)

Actual refresh logic remains client responsibility.

---

### FR-6: Boot & Restart Behavior

* Must be launched and supervised by systemd
* Must function non-interactively after reboot
* Must handle SIGTERM for clean shutdown and memory zeroisation
* Must fail fast if credentials cannot be decrypted
* Clear error modes:

  * missing file
  * invalid MAC
  * key derivation failure

systemd is considered part of the operational contract, not an optional deployment detail.

---

### FR-7: Observability

* Structured logging
* Explicit log events for:

  * credential load success/failure
  * refresh updates (no secret material)
  * corruption detection

No secrets may appear in logs.

---

## Non-Functional Requirements

### Security

* Encrypted at rest
* File permissions: owner-only (`0600`)
* Zero plaintext secrets on disk

### Reliability

* Survive power loss
* Deterministic startup
* Idempotent operations

### Performance

* Load time < 50ms on Raspberry Pi
* No background polling

### Portability

* No DE, no DBus
* ARM-compatible crypto libraries

---

## Configuration

* Credential file path
* Static salt
* Optional passphrase source:

  * environment variable
  * systemd credentials (`LoadCredential=`)
  * hardware-derived secret (future)

systemd is the preferred mechanism for injecting configuration and secrets at runtime.

---

## Failure Modes & Handling

| Scenario                 | Behavior                    |
| ------------------------ | --------------------------- |
| Missing credentials file | Hard fail with clear error  |
| Decryption failure       | Hard fail; do not overwrite |
| Corrupted file           | Refuse to start             |
| Expired access token     | Trigger refresh via client  |

---

## Open Questions (KIV)

* Hardware-backed key derivation (TPM / secure element)
* Remote credential bootstrap option
* Optional read-only mode

---

## Success Criteria

* Agent runs unattended for 30+ days under systemd supervision
* Survives power loss without credential loss
* No desktop dependencies
* No manual intervention for routine operation
* Python reference implementation and Rust implementation produce identical observable behavior

---

## Implementation Sequencing & Language Strategy

### Phase 1: Python Reference Implementation

The initial implementation **must be written in Python** to validate behavior, failure modes, and operational assumptions.

Goals of Phase 1:

* Stabilize credential file format and metadata schema
* Validate atomic write and recovery logic
* Exercise systemd startup, restart, and shutdown semantics
* Identify real-world edge cases (power loss, clock skew, token expiry races)

This Python version is treated as a **reference model**, not a throwaway prototype.

---

### Phase 2: Rust Refactor / Reimplementation

Once behavior is stable, reimplement the credential manager in Rust for:

* memory safety
* explicit ownership of secret material
* stronger guarantees around zeroisation

The Rust implementation must preserve the external contract exactly:

* same file format
* same error semantics
* same refresh and locking behavior

---

### Abstraction Design to Enable Clean Refactoring

To avoid bug hunting during refactoring, the following abstraction boundaries are mandatory from Day 1:

#### 1. Pure Data Model

* Define a language-agnostic credential schema (JSON)
* No logic embedded in serialization
* Treat the schema as immutable once Phase 1 stabilizes

#### 2. Deterministic Storage Interface

```text
StorageBackend
├── load() -> CredentialSet
├── store(CredentialSet)
└── validate(CredentialSet)

Runtime Interface (mapping-style):
├── get(id: str) -> Credential | None
├── put(id: str, credential: Credential)
├── delete(id: str)
└── list() -> list[Credential]
```

* No side effects outside this interface
* All atomicity guarantees live here
* On-disk format: object with credential IDs as keys (schema v3)
* Runtime: O(1) direct access via object keys (no index building needed)
* Deterministic serialization: keys sorted alphabetically for reproducibility
* Mapping storage provides natural API surface matching storage structure

#### 3. Crypto Boundary

```text
CryptoProvider
├── derive_key()
├── encrypt(plaintext)
└── decrypt(ciphertext)
```

* Crypto code must be swappable without touching business logic
* Python and Rust implementations must be black-box equivalent

#### 4. Refresh Logic Isolation

* Token refresh logic must consume and produce plain data structures
* No direct file or crypto access
* Enables identical test vectors across languages

---

### Testing Strategy

* Golden-file tests for encrypted blobs (where feasible)
* Cross-language test vectors:

  * encrypt in Python, decrypt in Rust
  * corrupt data tests
* Fault injection tests (partial writes, invalid MACs)

---

## Executive Summary

This product treats **operational reality as a first-class requirement**. systemd is part of the contract, Python is used to discover truth, and Rust is introduced only once the design is proven. The result is a credential manager that is predictable, auditable, and survivable in unattended headless deployments.
