"""Mbox Email Importer for MemoGarden Soil.

Imports emails from mbox files (Google Takeout format) into Soil database.
"""

from .email_parser import (
    decode_header_value,
    parse_address,
    parse_addresses,
    parse_date,
    parse_references,
    strip_angle_brackets,
    normalize_message_id,
    has_attachments,
    count_attachments,
    extract_attachment_filenames,
    extract_plain_text_body,
    extract_html_body,
    validate_email_data,
    validate_email_format,
    create_threading_relations,
)
from .import_mbox import MboxImporter, mbox_message_to_email_item, main

__all__ = [
    # Email parsing utilities
    "decode_header_value",
    "parse_address",
    "parse_addresses",
    "parse_date",
    "parse_references",
    "strip_angle_brackets",
    "normalize_message_id",
    "has_attachments",
    "count_attachments",
    "extract_attachment_filenames",
    "extract_plain_text_body",
    "extract_html_body",
    "validate_email_data",
    "validate_email_format",
    "create_threading_relations",
    # Mbox importer
    "MboxImporter",
    "mbox_message_to_email_item",
    "main",
]
