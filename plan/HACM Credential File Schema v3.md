Credential File Schema (v3)

Status: Current for Python reference implementation

This document defines the authoritative, language-agnostic on-disk schema for credentials managed by the Headless Agent Credential Manager.

Once implemented and validated, this schema must not change without an explicit version bump and migration plan.



---

Design Principles

Explicit is mandatory; implicit is forbidden

Secrets and metadata are strictly separated

No derived or cached values on disk

Forward-compatible via versioning

Suitable for deterministic encryption and atomic replacement

Mapping storage with direct lookup: credentials object keyed by credential ID for O(1) access



---

Top-Level Structure

{
  "version": 3,
  "created_at": "2026-01-15T08:12:30Z",
  "updated_at": "2026-01-15T09:01:10Z",
  "credentials": {
    "github:user@company": { ... },
    "google:user@gmail.com": { ... }
  }
}

Fields

Field	Type	Required	Notes

version	integer	yes	Schema version. Must be 3.
created_at	RFC3339 string	yes	File creation timestamp.
updated_at	RFC3339 string	yes	Last successful write.
credentials	object	yes	Credential entries keyed by unique ID.



---

Implementation Interface

Direct mapping access by credential ID:

get(id) -> Credential | None     # O(1) direct object access
put(id, credential)              # Atomic update with full file rewrite
delete(id)                       # Atomic removal with full file rewrite
list() -> list[Credential]       # Return all credentials (values())

This design combines:
- Simple on-disk format (object with ID keys for direct access)
- Fast runtime lookup (O(1) by key, no index building needed)
- Natural API surface (mapping-style interface matches storage)
- Order preservation via deterministic serialization (see below)

Order Preservation

Object order is preserved during serialization via deterministic key ordering.
When serializing to JSON, credential keys are sorted alphabetically to ensure
reproducible output. This provides:
- Auditing (viewing credentials in consistent order)
- Reproducibility (same data → same serialized bytes → same encryption result)
- Deterministic file hashes for validation

Timestamps (created_at, updated_at) remain the authoritative source of temporal
ordering information. Object key ordering is for reproducibility only.



---

Credential Entry

Each value in the credentials object represents one logical credential.

{
  "id": "github:user@company",
  "provider": "github",
  "account_id": "user@company",
  "type": "oauth_refresh",
  "material": "BASE64_ENCODED_OPAQUE_BLOB",
  "metadata": { ... },
  "created_at": "2026-01-15T08:12:30Z",
  "updated_at": "2026-01-15T09:01:10Z"
}

Required Fields

Field	Type	Required	Notes

id	string	yes	Globally unique logical ID. Format: <provider>:<account_id>.
provider	string	yes	e.g. github, google.
account_id	string	yes	Human-readable identifier (email, username).
type	enum	yes	Credential class (see below).
material	string (base64)	yes	Opaque secret payload. No structure assumed.
metadata	object	yes	Non-secret operational data only.
created_at	RFC3339 string	yes	Creation timestamp.
updated_at	RFC3339 string	yes	Last modification timestamp.



---

Credential Types

oauth_refresh

Represents an OAuth refresh token.

material

Refresh token (opaque string), base64-encoded


metadata

{
  "scopes": ["repo", "issues"],
  "token_endpoint": "https://github.com/login/oauth/access_token",
  "access_expires_in": 3600
}

Rules:

No access token is ever persisted

Expiry values are advisory only



---

oauth_client

Represents OAuth 2.0 client credentials (client_id + client_secret).

Used for confidential clients (desktop apps, headless services) that require
a static client_id and client_secret to perform the OAuth flow.

material

JSON object with client_id and client_secret, base64-encoded:

{
  "client_id": "your-app-id.apps.googleusercontent.com",
  "client_secret": "GOCSPX-..."
}


metadata (optional)

{
  "redirect_uris": ["http://localhost:8080/callback"],
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}

Rules:

Multiple oauth_client entries may exist (one per provider/app)

URIs in metadata are for documentation/audit only (non-sensitive)



---

service_account

Represents a long-lived private key or credential blob.

material

Encrypted private key or credential JSON


metadata

{
  "key_id": "abc123",
  "issuer": "service@example.com"
}



---

Metadata Rules (Hard)

MUST NOT contain secrets

MUST be JSON-serializable

MUST be stable across refreshes unless explicitly changed



---

Invariants

id must be unique within the file (enforced by object keys)

updated_at must monotonically increase per credential

Removing a credential requires deleting the key from the object

Partial updates are forbidden; rewrite whole file atomically



---

Forbidden Patterns

Storing access tokens

Derived fields (e.g. cached access token expiry timestamps)

Implicit defaults not encoded in schema

Provider-specific logic encoded in file structure



---

Migration Policy

Any incompatible change requires:

version increment

explicit migration function

dual-read during transition



---

Rationale (Why this is strict)

This schema is designed to:

survive language rewrites

survive power loss

support offline inspection (after decryption)

eliminate refactor-induced semantic drift

If a field is not justified here, it does not belong on disk.



---

Migration from v2

To migrate from schema v2 to v3:

1. Load and decrypt v2 credential file
2. Extract credentials array
3. Build v3 credentials object:
   - For each credential in array, use credential["id"] as key
   - Validate no duplicate IDs exist (v2 schema guarantees this)
4. Update version field from 2 to 3
5. Update updated_at timestamp
6. Encrypt and write new v3 file

This is a lossless, reversible migration.
