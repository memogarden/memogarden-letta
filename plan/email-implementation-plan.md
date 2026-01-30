# Email Import Implementation Plan

**Status**: Pending
**Created**: 2026-01-30
**Context**: Architecture review recommendations for production-ready email import

---

## Overview

This plan implements the recommendations from the Email Import Architecture Review. The focus is on:
1. Formalizing data/metadata separation
2. Implementing threading relations correctly
3. Structuring for incremental import (bulk mbox + future Gmail sync)
4. Documenting architectural decisions

**Estimated effort**: 1-2 days

---

## Architectural Decisions (From Review)

| ID | Decision | Rationale |
|----|----------|-----------|
| AD-1 | Single polymorphic `item` table | Soil is a timeline, not relational DB |
| AD-2 | Strict data/metadata separation | Provider-agnostic core vs provider-specific |
| AD-3 | Defer index optimization | Functional indexes fine, evolve later |
| AD-4 | Search as relation signal | Capture queries for future significance |

---

## Implementation Phases

### Phase 1: Documentation & Schema Formalization

**Goal**: Document decisions and create formal schema definition

#### Task 1.1: Add Schema Documentation
**File**: `soil/schema/schema.sql`

Add comments documenting index evolution strategy:

```sql
-- ============================================================================
-- INDEX STRATEGY
-- ============================================================================
-- Functional indexes for critical fields (current approach)
-- Future: May be replaced with separate index layer (Rust hash tables, etc.)
-- Rebuild strategy: DROP INDEX + CREATE INDEX (indexes are derived data)

CREATE INDEX IF NOT EXISTS idx_item_email_id
  ON item(json_extract(data, '$.rfc_message_id'))
  WHERE _type = 'Email';

-- Document known item types for reference
INSERT OR REPLACE INTO _schema_metadata (key, value) VALUES
  ('item_types', 'Note,Message,Email,ToolCall,EntityDelta,SystemEvent');
```

#### Task 1.2: Create Formal Email Schema
**File**: `schemas/email.yaml` (new file)

Create language-agnostic schema defining:
- `data` fields (RFC 5322 standard)
- `metadata` fields (provider-specific)
- Auto-relations (`replies_to` from threading headers)

Content from review REC-2.

**Deliverables**:
- [ ] Updated `soil/schema/schema.sql` with documentation
- [ ] New `schemas/email.yaml` file

---

### Phase 2: Data/Metadata Separation

**Goal**: Refactor email parser to strictly separate standard vs provider fields

#### Task 2.1: Implement Parsing Utilities
**File**: `soil/email_parser.py` (new file)

Extract and implement helper functions:
- `parse_address()` - Extract email from "Name <email>" format
- `parse_addresses()` - Parse comma-separated address list
- `parse_references()` - Parse References header
- `decode_header_value()` - Decode RFC 2047 encoded headers
- `has_attachments()` - Check for attachments
- `count_attachments()` - Count attachments
- `extract_attachment_filenames()` - Get filenames for significance
- `extract_plain_text_body()` - Get text/plain body
- `extract_html_body()` - Get text/html body for metadata

#### Task 2.2: Refactor `parse_email()`
**File**: `soil/import_mbox.py`

Update `mbox_message_to_email_item()` to:
- Return structured dict with explicit `data` and `metadata` sections
- Standard RFC 5322 fields → `data`
- Provider-specific (GMail headers, HTML) → `metadata`
- Add full original headers dict to metadata for debugging

**Signature**:
```python
def mbox_message_to_email_item(
    msg: email.message.Message,
    source_file: str = "unknown.mbox",
    realized_at: str | None = None,
) -> dict:
    """
    Returns dict with keys:
    - uuid, _type, realized_at, canonical_at, fidelity
    - data: dict of RFC 5322 fields
    - metadata: dict of provider-specific fields
    """
```

#### Task 2.3: Add Validation
**File**: `soil/email_parser.py`

```python
def validate_email_data(data: dict) -> None:
    """Validate required fields present."""
    required = ['rfc_message_id', 'from_address', 'to_addresses', 'sent_at', 'description']
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
```

**Deliverables**:
- [ ] New `soil/email_parser.py` with utilities
- [ ] Refactored `mbox_message_to_email_item()` with separation
- [ ] Validation function implemented

---

### Phase 3: Threading Relations Implementation

**Goal**: Create `replies_to` system relations from RFC 5322 headers

#### Task 3.1: Implement Relation Creation
**File**: `soil/email_parser.py`

Add function from review REC-4:

```python
def create_threading_relations(
    email: dict,
    email_index: dict[str, str]
) -> list[dict]:
    """
    Create replies_to system relations from RFC 5322 headers.

    Args:
        email: Parsed email dict with uuid and data fields
        email_index: Mapping of rfc_message_id -> item_uuid

    Returns:
        List of SystemRelation dicts
    """
```

**Logic**:
1. Check `in_reply_to` field first (most reliable)
2. Fallback to last `references` entry
3. Look up parent UUID in `email_index`
4. Create `SystemRelation` with proper evidence
5. Return list (usually 1 relation)

#### Task 3.2: Integrate into Import Flow
**File**: `soil/import_mbox.py`

Update `MboxImporter.import_mbox()`:
- Build `email_index` (rfc_message_id → uuid mapping) before import
- After inserting each email, call `create_threading_relations()`
- Insert relations into `system_relation` table
- Track relation count in stats

**Changes**:
```python
class MboxImporter:
    def __init__(self, soil: Soil, batch_size: int = 100):
        self.soil = soil
        self.batch_size = batch_size
        self.message_id_to_uuid: dict[str, str] = {}  # Already exists
        # Reuse as email_index for threading

    def import_mbox(self, mbox_path, limit=None, verbose=True):
        # ... existing import logic ...

        # After inserting email:
        # Create threading relations
        relations = create_threading_relations(email_data, self.message_id_to_uuid)
        for rel in relations:
            self.soil.create_relation(...)  # Need to add method or use direct SQL
            self.stats["relations_created"] += 1
```

#### Task 3.3: Verify Threading
**Test SQL**:
```sql
-- Find emails with replies
SELECT
    i.uuid,
    json_extract(i.data, '$.subject') as subject,
    COUNT(sr.uuid) as reply_count
FROM item i
LEFT JOIN system_relation sr
    ON i.uuid = sr.target AND sr.kind = 'replies_to'
WHERE i._type = 'Email'
GROUP BY i.uuid
HAVING reply_count > 0
ORDER BY reply_count DESC
LIMIT 10;
```

**Expected**: ~38% of emails should have replies (based on analysis)

**Deliverables**:
- [ ] `create_threading_relations()` function
- [ ] Integrated into import flow
- [ ] Relation tracking in stats
- [ ] Verification query succeeds

---

### Phase 4: Refactor to Abstract Importer

**Goal**: Enable bulk (mbox) and incremental (Gmail) import with shared logic

#### Task 4.1: Create Abstract Base Class
**File**: `soil/email_importer.py` (new file)

```python
class EmailImporter(ABC):
    """Abstract base for email import strategies."""

    def __init__(self, soil: Soil):
        self.soil = soil
        self.email_index = self._build_index()
        self.stats = {
            "processed": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "relations_created": 0,
        }

    def _build_index(self) -> dict[str, str]:
        """Build rfc_message_id -> uuid index for deduplication."""
        # Implementation from review REC-5

    def import_email(self, email: dict) -> tuple[bool, int]:
        """Import single email with deduplication and threading.

        Returns:
            (imported: bool, relations_created: int)
        """
        # Implementation from review REC-5

    def import_all(self):
        """Import all emails from source."""
        # Implementation from review REC-5

    @abstractmethod
    def fetch_emails(self) -> Iterator[dict]:
        """Fetch emails from source. Must be implemented by subclasses."""
        pass
```

#### Task 4.2: Refactor MboxImporter
**File**: `soil/import_mbox.py` → update to use new base class

```python
from soil.email_importer import EmailImporter

class MboxImporter(EmailImporter):
    """Bulk import from mbox file."""

    def __init__(self, soil: Soil, mbox_path: str, batch_size: int = 100):
        super().__init__(soil)
        self.mbox_path = mbox_path
        self.batch_size = batch_size

    def fetch_emails(self) -> Iterator[dict]:
        """Yield parsed emails from mbox file."""
        import mailbox
        mbox = mailbox.mbox(self.mbox_path)
        for msg in mbox:
            try:
                yield mbox_message_to_email_item(msg, self.mbox_path)
            except Exception as e:
                self.stats["errors"] += 1
                if self.stats["errors"] <= 10:  # Limit error spam
                    print(f"Error parsing mbox message: {e}")
                continue
```

#### Task 4.3: Create GmailImporter Stub
**File**: `soil/gmail_importer.py` (new file)

```python
from soil.email_importer import EmailImporter

class GmailImporter(EmailImporter):
    """Incremental import from Gmail API (future implementation)."""

    def __init__(self, soil: Soil, account_id: str):
        super().__init__(soil)
        self.account_id = account_id
        # Load refresh token from HACM
        # self.service = build_gmail_service(...)

    def fetch_emails(self, since: datetime = None) -> Iterator[dict]:
        """Yield emails from Gmail API since last sync."""
        raise NotImplementedError("Gmail sync not yet implemented")

    def translate_gmail_to_email(self, gmail_msg: dict) -> dict:
        """Translate Gmail API response to Email item dict."""
        # TODO: Map Gmail API schema to RFC 5322 schema
        pass
```

**Deliverables**:
- [ ] `soil/email_importer.py` with abstract base class
- [ ] Refactored `MboxImporter` extending base class
- [ ] `GmailImporter` stub file

---

### Phase 5: Testing & Validation

**Goal**: Verify all changes work correctly

#### Task 5.1: Deduplication Test
**File**: `soil/tests/test_email_import.py` (new file)

```python
def test_deduplication():
    """Import same mbox twice, verify no duplicates."""
    # Import mbox
    # Import again
    # Assert count unchanged
```

#### Task 5.2: Threading Test
**Verification**: Run SQL query from Phase 3, verify ~38% threaded

#### Task 5.3: Schema Conformance Test
**File**: `soil/tests/test_email_import.py`

```python
def test_schema_conformance():
    """Verify data/metadata separation."""
    for item in soil.list_items('Email'):
        # RFC 5322 fields in data
        assert 'rfc_message_id' in item['data']
        assert 'from_address' in item['data']

        # Provider fields in metadata
        assert 'provider' in item['metadata']
        assert 'gmail_thread_id' not in item['data']
```

#### Task 5.4: Full Import Test
**Command**:
```bash
rm -f /tmp/soil-test.db
python -m soil.import_mbox \
  /path/to/mbox.mbox \
  --db /tmp/soil-test.db \
  --init \
  --batch-size 500
```

**Verify**:
- 10,512 emails imported
- ~1,435 threading relations (or more with new logic)
- 0 errors (or acceptable errors logged)

**Deliverables**:
- [ ] Test file created
- [ ] All tests passing
- [ ] Full import succeeds

---

## Implementation Order

**Recommended sequence** (can be done in any order, but this minimizes rework):

1. **Phase 1** (Documentation) - Do first, guides implementation
2. **Phase 2** (Data/Metadata) - Foundation for everything else
3. **Phase 3** (Threading) - Requires Phase 2 data structure
4. **Phase 4** (Refactor) - Requires Phase 2 + 3 complete
5. **Phase 5** (Testing) - Verify all phases

**Time estimates**:
- Phase 1: 30 min
- Phase 2: 2-3 hours
- Phase 3: 2-3 hours
- Phase 4: 2-3 hours
- Phase 5: 1-2 hours

**Total**: ~8-12 hours (1-2 days)

---

## Open Questions (From Review)

### Q1: HTML-only Emails
**Question**: What to do when email has no plain text body?

**Options**:
- A: Store HTML in `description`, flag as `content_type: 'text/html'`
- B: Convert HTML to plain text (requires html2text)

**Decision**: Start with Option A
- Add `content_type` field to data
- Store HTML in `description`
- Add conversion later if needed (low priority)

### Q2: Attachment Storage
**Question**: Store attachment binaries or just metadata?

**Decision**: Metadata only for now
- Current: filenames, count, size
- Future: Could store as separate items with `contained_by` relation
- Rationale: Binaries complicate import, low priority

### Q3: Label Significance
**Question**: Use Gmail labels for time horizon/significance?

**Decision**: Store in metadata for now
- Capture labels like "Important", user-created labels
- Use for significance inference later
- Don't create user_relations yet

### Q4: Sent vs Received
**Question**: Should sent emails have different initial time horizon?

**Decision**: Treat equally for now
- No distinction in initial state
- Revisit after observing decay patterns
- Can bias later based on actual usage

---

## Success Criteria

- [ ] All 5 phases complete
- [ ] Tests passing
- [ ] Full 10k email import succeeds
- [ ] Threading relations verified (~38% of emails)
- [ ] Data/metadata separation validated
- [ ] Gmail stub ready for future implementation
- [ ] Documentation updated

---

## Post-Implementation

**After completing this plan**:
1. Delete test databases (`/tmp/soil-test.db`)
2. Update `plan/email-analysis.md` with implementation notes
3. Consider next steps:
   - Implement Gmail sync using `GmailImporter` stub
   - Add search functionality (deferred from review)
   - Build query tools/CLI for browsing emails

---

**END OF PLAN**
