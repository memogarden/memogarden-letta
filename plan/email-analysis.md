# Email Analysis for PRD v0.7.0 Validation

**Date**: 2026-01-30
**Source**: Google Takeout MBOX (10,513 messages)
**Purpose**: Validate PRD v0.7.0 assumptions for email import

---

## Summary

- **Total messages**: 10,513
- **Threaded messages**: 3,998 (38%)
- **Date range**: 2025-12-19 to 2026-01-24 (sample)
- **File size**: 1.7GB

---

## Email Headers Analysis

### Standard Headers (All emails)

| Header | Presence | Notes |
|--------|----------|-------|
| Message-ID | 100% | Unique identifier per message |
| Subject | 100% | May be encoded (RFC 2047) |
| From | 100% | Sender address |
| To | 100% | Recipient(s) |
| Date | 100% | Sent timestamp |
| Delivered-To | 100% | Final delivery address |

### Threading Headers (38% of emails)

| Header | Presence | Notes |
|--------|----------|-------|
| References | ~38% | Contains thread ancestor Message-IDs |
| In-Reply-To | ~38% | Direct parent Message-ID |

Both headers are present for threaded emails. `References` may contain multiple Message-IDs for deep threads.

### GMail-Specific Headers

| Header | Presence | Notes |
|--------|----------|-------|
| X-Gm-Thrid | 100% | GMail thread ID (numeric string) |
| X-Gmail-Message-ID | 0% | Not present in takeout export |

**Key finding**: `X-Gm-Thrid` is critical for GMail thread reconstruction. This is provider-specific data that should go in `Item.metadata`.

### Attachment Headers

| Header | Presence | Notes |
|--------|----------|-------|
| Content-Disposition | ~5% | Indicates attachment |
| attachment filename | Variable | PDF, images, etc. |

---

## PRD v0.7.0 Validation

### Gap Analysis: Missing Email Type ✅ RESOLVED

**Finding (2026-01-30)**: PRD v0.7.0 initially defined `Note` and `Message` types but no `Email` type.

**Resolution**: `Email` type added to PRD v0.7.0 as a subtype of `Note`.

**Schema**: The `Email` type includes:
- Standard RFC 5322 headers (Message-ID, From, To, Cc, Bcc, Date)
- Threading fields (References, In-Reply-To)
- Attachment metadata
- Provider-specific data in `Item.metadata`

**Implementation**: See PRD v0.7.0 → Item Types → Email section.

---

## Threading Strategy

### Two Options

**Option A: RFC 5322 Threading (Recommended)**
- Use `References` + `In-Reply-To` headers
- Create `replies_to` system relations
- Provider-agnostic (works with any email provider)
- Matches PRD's `replies_to` system relation kind

**Option B: Provider-Specific Threading**
- Use `X-Gm-Thrid` for GMail
- Requires provider-specific logic
- More accurate for GMail conversations
- Doesn't generalize

**Recommendation**: Start with Option A (RFC 5322). Add Option B later as enhancement if needed.

---

## Deduplication Strategy

### Primary Key: `rfc_message_id`

- Message-ID is globally unique per email
- Use for detecting duplicates across imports
- Store as `rfc_message_id` field for lookup

### Implementation

```python
def import_email(email_message: Email) -> str:
    # Check for existing email by Message-ID
    existing = soil_db.get_item_by_rfc_message_id(email_message.rfc_message_id)
    if existing:
        return existing.uuid  # Skip import

    # Create new Item
    uuid = f"soil_{uuid4()}"
    soil_db.create_item(uuid, email_message)
    return uuid
```

---

## Fidelity Considerations

### Initial Import: `full` fidelity

- Store complete email content
- Preserve headers in metadata
- Attachments: store metadata only (not binary content)

### Future: `summary` fidelity for old emails

- Extractive summary of email body
- Preserve threading relations
- Reduce storage footprint

---

## Import Pipeline Design

```
mbox file
    → parse messages (mailbox.mbox)
    → extract headers/body
    → create Email items
    → build replies_to relations
    → store in Soil (item table)
    → index by rfc_message_id
```

### Memory-Efficient Processing

1. **Stream processing**: Use `mailbox.mbox` iterator (not `list(mbox)`)
2. **Batch inserts**: Insert 100-1000 items at a time
3. **Progress tracking**: Log every 1000 messages
4. **Error handling**: Skip malformed messages, log for review

---

## Open Questions

1. **Attachment storage**: Store as separate Items or ignore?
   - *Recommendation*: Ignore for now. Add later as `Attachment` type if needed.

2. **HTML vs plain text**: Which to store in `description`?
   - *Finding*: Most emails have both. Plain text is cleaner.
   - *Recommendation*: Store plain text in `description`, HTML in `metadata` for reference.

3. **BCC handling**: Not available in exports (hidden by design).
   - *Recommendation*: Set `bcc_addresses` to `None` for imported emails.

4. **Label preservation**: GMail labels (INBOX, SENT, etc.)
   - *Recommendation*: Store in `metadata["gmail_labels"]`. Don't create Core Labels yet.

5. **Sent folder handling**: Emails you sent have you as `From`, not `To`.
   - *Recommendation*: Import all emails regardless of folder. Dedup by Message-ID.

---

## Next Steps

1. ✅ Add `Email` type to PRD v0.7.0
2. ✅ Implement Soil database schema (item, system_relation tables)
3. ✅ Write mbox parser and Email item converter
4. ✅ Implement replies_to relation builder
5. ✅ Test import with small subset (100 messages)
6. ⏳ Full import (10,513 messages) - Ready to run

---

**End of Analysis**
