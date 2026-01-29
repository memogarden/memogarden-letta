# MemoGarden Email Import: Implementation Plan

**Status**: In Progress
**Last Updated**: 2025-01-29
**Context**: Evaluating MemoGarden PRD v0.7.0 design by importing GMail emails

---

## Objectives

1. **Primary**: Import GMail emails into MemoGarden Soil to test/validate the PRD design
2. **Secondary**: Establish minimal infrastructure for OAuth-based data providers

---

## Completed Work

### 1. HACM (Headless Agent Credential Manager) ✅

**Repository**: https://github.com/memogarden/hacm

**Implementation**: Python reference implementation
- **Schema v3**: Object/mapping storage with credential IDs as keys
- **Crypto layer**: Argon2id key derivation, XSalsa20-Poly1305 AEAD encryption
- **Storage layer**: Atomic file operations, deterministic JSON serialization
- **Core interface**: `CredentialStore` with get(), put(), delete(), list()
- **Tests**: 33 passing, covering crypto, storage, and CRUD operations

**Stored Credentials**:
- OAuth client: `google:oauth-client` (your GCloud project)
- Location: `~/hacm-test/credentials.enc` (encrypted with machine-id)

### 2. GMail OAuth Handler Module ✅

**Location**: `/home/kureshii/memogarden/gmail-oauth/`

**Implementation**: OOB (out-of-band) OAuth flow for headless systems
- `GmailOAuthClient`: get_authorization_url(), exchange_code_for_tokens(), store_tokens(), refresh_access_token()
- **Scripts** (standalone, no complex imports):
  - `oauth-auth-url.py`: Generate OAuth authorization URL
  - `oauth-exchange.py`: Exchange code for refresh token
- **Dependencies**: requests, pynacl, HACM

**OAuth Flow**:
1. Run `oauth-auth-url.py` → displays authorization URL
2. User visits URL, authorizes application
3. Google displays authorization code (e.g., `4/0AX4Xf...`)
4. Run `oauth-exchange.py <code> <email>` → stores refresh token in HACM

**Status**: Ready to use. Client credentials stored, scripts tested.

---

## Current Status

### Completed ✅
- HACM fully implemented and tested (33 tests passing)
- GMail OAuth handler created with OOB flow
- Client credentials stored in HACM
- Virtual environment set up (`.venv/`)
- Authorization URL generation tested successfully

### In Progress 🔄
- **Next**: Complete OAuth flow to obtain GMail refresh token

### Blocked/Pending ⏸
- GMail API integration (needs refresh token first)
- Mbox file creation (Google Takeout)
- Soil database implementation (PRD v0.7.0)

---

## Next Steps

### Immediate: Complete OAuth Flow

1. **Authorize Application**
   ```bash
   source .venv/bin/activate
   python gmail-oauth/oauth-auth-url.py
   ```

2. **Visit URL and Copy Code**
   - Visit displayed URL in browser
   - Sign in with your GMail account
   - Copy authorization code from Google

3. **Exchange Code for Refresh Token**
   ```bash
   python gmail-oauth/oauth-exchange.py <code> your-email@gmail.com
   ```

4. **Verify Token Storage**
   - Refresh token will be stored in HACM as `google:your-email@gmail.com`
   - Can be retrieved via `get_refresh_token()` for API access

### Phase 2: GMail Data Export

**Option A: Google Takeout (Recommended)**
1. Go to https://takeout.google.com/
2. Select "Mail" data
3. Select "All Mail" or specific date range (≤ 2025-12-31)
4. Choose export format: **MBOX** (not .mbox.zip - actual mbox format)
5. Download file

**Option B: GMail API (Future)**
- Use refresh token to call GMail API
- Export messages programmatically
- Write to mbox format
- More complex but enables real-time sync

### Phase 3: PRD Review with Real Data

1. **Analyze Exported Emails**
   - Review email headers (Message-ID, References, In-Reply-To)
   - Check thread structure
   - Identify edge cases (attachments, encoding, non-standard headers)
   - Sample data: number of emails, date range, threading patterns

2. **Validate PRD v0.7.0 Assumptions**
   - Does `Email` type capture all necessary fields?
   - Are system relations (`replies_to`) sufficient for threading?
   - Is metadata field flexible enough for GMail-specific data?
   - Any missing fields in PRD?

3. **Schema Adjustments**
   - Add Item.metadata field (mentioned in analysis but not in PRD)
   - Adjust Email type based on real email structure
   - Add missing fields if needed

### Phase 4: Soil Database Implementation

**Core Database Schema** (from PRD v0.7.0, minimal):

```sql
CREATE TABLE item (
    uuid TEXT PRIMARY KEY,  -- "soil_" + uuid4
    _type TEXT NOT NULL,    -- "Email", "Note", etc.
    realized_at TEXT NOT NULL,
    canonical_at TEXT NOT NULL,
    integrity_hash TEXT,
    fidelity TEXT NOT NULL DEFAULT 'full',
    superseded_by TEXT,
    superseded_at TEXT,
    data JSON NOT NULL,
    metadata JSON           -- Added for provider-specific data
);

CREATE TABLE system_relation (
    uuid TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target TEXT NOT NULL,
    target_type TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    evidence JSON,
    metadata JSON,
    UNIQUE(kind, source, target)
);
```

**Email Type** (provider-agnostic):

```python
@dataclass
class Email(Note):  # Email extends Note extends Item
    # Standard fields (all email providers)
    rfc_message_id: str              # Message-ID header
    references: list[str] | None     # References header
    in_reply_to: str | None          # In-Reply-To header
    from_address: str
    to_addresses: list[str]
    cc_addresses: list[str] | None
    bcc_addresses: list[str] | None
    sent_at: datetime                # Date header
    received_at: datetime | None
    has_attachments: bool
    attachment_count: int

# In Item.metadata (provider-specific):
# {
#   "provider": "google",
#   "gmail_message_id": "...",
#   "gmail_thread_id": "...",
#   "labels": ["INBOX"],
#   "original_object": {...}
```

### Phase 5: Mbox Import Implementation

**Components**:
1. **Mbox Parser**: Python `mailbox` module to read mbox file
2. **Email → Item Converter**: Transform mbox message to Email item
3. **Relation Builder**: Build `replies_to` relations from headers
4. **Deduplication**: Check for existing items by `rfc_message_id`

**Import Pipeline**:
```
mbox file → parse messages → create Email items → build relations → store in Soil
```

### Phase 6: Testing & Validation

1. **Import Test**: Import small mbox subset
2. **Threading Validation**: Verify `replies_to` relations
3. **Metadata Validation**: Ensure GMail metadata fits in Item.metadata
4. **Edge Cases**: Attachments, encoding issues, malformed headers

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **PRD schema gaps** | Review with real email data before committing to Soil |
| **Mbox format issues** | Start with small subset, handle errors gracefully |
| **OAuth token revocation** | Implement refresh flow, store new token when rotated |
| **Large mbox files** | Stream processing, memory-efficient parsing |
| **Thread detection issues** | Start with simple References/In-Reply-To, validate against Google's thread structure |

---

## Success Criteria

1. ✅ HACM stores credentials securely
2. ✅ OAuth flow works with OOB
3. ⏳ Refresh token obtained and stored
4. ⏳ Mbox file exported (≤ 2025-12-31)
5. ⏳ PRD reviewed with real email data
6. ⏳ Soil database created
7. ⏳ Emails imported as Message items
8. ⏳ `replies_to` relations validated

---

## Open Questions

1. **Soil directory structure**: Where should Soil database files live? (`~/memogarden/soil/`, `/var/lib/memogarden/soil/`, etc.)
2. **Database initialization**: Should Soil auto-create or require explicit init?
3. **Multi-user support**: Does Soil need user isolation or single-user for now?
4. **Attachment handling**: Ignore for now, or store as separate items?
5. **Real-time sync**: How to handle new emails after initial import?

---

## Session Notes

**Accomplished this session**:
- HACM: complete implementation (crypto, storage, core)
- HACM Schema: v3 with object/mapping storage
- GMail OAuth: OOB flow with HACM integration
- Workspace: Single venv for all development
- Documentation: PRD v0.7.0, HACM PRD, HACM Schema v3

**Dependencies installed in venv**:
- pynacl (crypto)
- requests (OAuth HTTP calls)
- HACM (via local import path)

**Next session starts with**: Running the OAuth flow end-to-end.

---

**Last action**: Created OAuth scripts that successfully generate authorization URLs using client credentials from HACM.
