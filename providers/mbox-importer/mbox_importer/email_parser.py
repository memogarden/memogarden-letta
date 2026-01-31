"""Email parsing utilities for MemoGarden Soil.

Provides functions for parsing RFC 5322 email messages into Email items
with strict data/metadata separation. Data fields are provider-agnostic
RFC 5322 standard fields, while metadata fields are provider-specific.
"""

from __future__ import annotations

import email
import re
from datetime import datetime, timezone
from email.header import decode_header
from typing import Optional


# ============================================================================
# EMAIL PARSING UTILITIES
# ============================================================================

def decode_header_value(value: str) -> str:
    """Decode RFC 2047 encoded header value.

    Args:
        value: Header value (may be encoded)

    Returns:
        Decoded Unicode string
    """
    if not value:
        return ""

    decoded_parts = []
    for content, encoding in decode_header(value):
        if isinstance(content, bytes):
            if encoding:
                try:
                    decoded_parts.append(content.decode(encoding))
                except (LookupError, UnicodeDecodeError):
                    decoded_parts.append(content.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(content.decode('utf-8', errors='replace'))
        else:
            decoded_parts.append(content)

    return "".join(decoded_parts)


def parse_address(addr_string: str) -> str:
    """Parse single email address from header string.

    Extracts just the email address from formats like:
    - "john@example.com"
    - "John Doe <john@example.com>"
    - "<john@example.com>"

    Args:
        addr_string: Address header string

    Returns:
        Email address only
    """
    if not addr_string:
        return ""

    # Use email.utils to parse address
    from email.utils import getaddresses

    addresses = getaddresses([addr_string])
    if addresses:
        return addresses[0][1] if addresses[0][1] else ""
    return ""


def parse_addresses(addr_string: str) -> list[str]:
    """Parse email addresses from header string.

    Handles multiple addresses separated by commas.

    Args:
        addr_string: Address header string (e.g., "John Doe <johndoe@example.com>, jane@example.com")

    Returns:
        List of email addresses
    """
    if not addr_string:
        return []

    # Use email.utils to parse addresses
    from email.utils import getaddresses

    addresses = getaddresses([addr_string])
    return [addr for name, addr in addresses if addr]


def parse_date(date_string: str) -> Optional[str]:
    """Parse RFC 5322 date string to ISO 8601 format.

    Args:
        date_string: RFC 5322 date string

    Returns:
        ISO 8601 timestamp or None if parsing fails
    """
    if not date_string:
        return None

    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except (ValueError, TypeError):
        return None


def parse_references(value: str) -> list[str]:
    """Parse References header into list of Message-IDs.

    The References header contains Message-IDs of thread ancestors,
    ordered from oldest to newest.

    Args:
        value: References header value

    Returns:
        List of Message-ID strings (without angle brackets)
    """
    if not value:
        return []

    # Split by whitespace and strip angle brackets
    message_ids = []
    for part in value.split():
        part = part.strip()
        if part.startswith("<") and part.endswith(">"):
            message_ids.append(part[1:-1])
        else:
            message_ids.append(part)

    return message_ids


def strip_angle_brackets(message_id: str) -> str:
    """Strip angle brackets from Message-ID.

    Args:
        message_id: Message-ID with or without angle brackets

    Returns:
        Message-ID without angle brackets
    """
    if not message_id:
        return ""
    message_id = message_id.strip()
    if message_id.startswith("<") and message_id.endswith(">"):
        return message_id[1:-1]
    return message_id


def normalize_message_id(message_id: str) -> str:
    """Normalize Message-ID for storage and lookup.

    Stores Message-IDs with angle brackets for consistency.

    Args:
        message_id: Message-ID with or without angle brackets

    Returns:
        Message-ID with angle brackets
    """
    stripped = strip_angle_brackets(message_id)
    return f"<{stripped}>"


def has_attachments(msg: email.message.Message) -> bool:
    """Check if email message has attachments.

    Args:
        msg: Email message object

    Returns:
        True if message has attachments
    """
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in content_disposition:
            return True
    return False


def count_attachments(msg: email.message.Message) -> int:
    """Count attachments in email message.

    Args:
        msg: Email message object

    Returns:
        Number of attachments
    """
    count = 0
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in content_disposition:
            count += 1
    return count


def extract_attachment_filenames(msg: email.message.Message) -> list[str]:
    """Extract attachment filenames from email message.

    Args:
        msg: Email message object

    Returns:
        List of attachment filenames (for significance inference)
    """
    filenames = []
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in content_disposition:
            filename = part.get_filename()
            if filename:
                filenames.append(decode_header_value(filename))
    return filenames


def extract_plain_text_body(msg: email.message.Message) -> str:
    """Extract plain text body from email message.

    Args:
        msg: Email message object

    Returns:
        Plain text body (empty string if not found)
    """
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        return payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                    except Exception:
                        return str(payload)
    else:
        # Single part message
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='replace')
                if msg.get_content_type() == "text/plain":
                    return content
            except Exception:
                return str(payload)

    return ""


def extract_html_body(msg: email.message.Message) -> str:
    """Extract HTML body from email message.

    Args:
        msg: Email message object

    Returns:
        HTML body (empty string if not found)
    """
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        return payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                    except Exception:
                        return str(payload)
    else:
        # Single part message
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='replace')
                if msg.get_content_type() == "text/html":
                    return content
            except Exception:
                return str(payload)

    return ""


# ============================================================================
# VALIDATION
# ============================================================================

def validate_email_data(data: dict) -> None:
    """Validate required Email data fields are present.

    Args:
        data: Email data dict with RFC 5322 fields

    Raises:
        ValueError: If required fields are missing
    """
    required_fields = [
        'rfc_message_id',
        'from_address',
        'to_addresses',
        'sent_at',
        'title',        # Email subject
        'description',  # Email body
    ]

    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        raise ValueError(f"Missing required Email data fields: {missing}")


def validate_email_format(email_addr: str) -> bool:
    """Validate email address format.

    Args:
        email_addr: Email address to validate

    Returns:
        True if email format is valid
    """
    if not email_addr:
        return False

    # Basic email regex (RFC 5322 is more complex, but this is practical)
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    return bool(re.match(pattern, email_addr))


# ============================================================================
# THREADING RELATIONS
# ============================================================================

def create_threading_relations(
    email: dict,
    email_index: dict[str, str]
) -> list[dict]:
    """Create replies_to system relations from RFC 5322 headers.

    Args:
        email: Parsed email dict with uuid and data fields
        email_index: Mapping of rfc_message_id -> item_uuid

    Returns:
        List of SystemRelation dicts (usually 1 relation)
    """
    relations = []
    data = email.get('data', {})
    email_uuid = email.get('uuid')

    if not email_uuid:
        return relations

    # Check in_reply_to first (direct parent, most reliable)
    in_reply_to = data.get('in_reply_to')
    if in_reply_to:
        # Normalize to match storage format (with angle brackets)
        parent_message_id = normalize_message_id(in_reply_to)

        if parent_message_id in email_index:
            parent_uuid = email_index[parent_message_id]
            relations.append({
                'kind': 'replies_to',
                'source': email_uuid,
                'source_type': 'item',
                'target': parent_uuid,
                'target_type': 'item',
                'evidence': {
                    'source': 'system_inferred',
                    'method': 'rfc_5322_in_reply_to',
                    'confidence': 'high',
                }
            })
            return relations  # Found direct parent, done

    # Fallback to last reference (thread ancestors)
    references = data.get('references')
    if references and len(references) > 0:
        # Use the last (most recent) reference as direct parent
        last_ref = references[-1]
        parent_message_id = normalize_message_id(last_ref)

        if parent_message_id in email_index:
            parent_uuid = email_index[parent_message_id]
            relations.append({
                'kind': 'replies_to',
                'source': email_uuid,
                'source_type': 'item',
                'target': parent_uuid,
                'target_type': 'item',
                'evidence': {
                    'source': 'system_inferred',
                    'method': 'rfc_5322_references',
                    'confidence': 'high',
                }
            })

    return relations
