#!/usr/bin/env python
"""Mbox email importer for MemoGarden Soil.

Imports emails from mbox files (Google Takeout format) into Soil database.
Creates Email items and replies_to relations for threading.
"""

from __future__ import annotations

import email
import mailbox
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import from system.soil instead of local soil package
from system.soil import Soil, create_email_item, generate_soil_uuid, Evidence, SystemRelation
from mbox_importer.email_parser import (
    decode_header_value,
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
    create_threading_relations,
)


# ============================================================================
# EMAIL ITEM CREATION
# ============================================================================

def mbox_message_to_email_item(
    msg: email.message.Message,
    source_file: str = "unknown.mbox",
    realized_at: str | None = None,
) -> Optional[dict]:
    """Convert mbox message to Email item with strict data/metadata separation.

    Returns dict with keys:
    - uuid, _type, realized_at, canonical_at, fidelity
    - data: RFC 5322 standard fields (provider-agnostic)
    - metadata: Provider-specific fields (GMail, etc.)

    Args:
        msg: Email message from mailbox
        source_file: Source mbox filename (for metadata)
        realized_at: When import occurred (ISO 8601, defaults to now)

    Returns:
        Dict with email data/metadata or None if message is invalid
    """
    if realized_at is None:
        realized_at = datetime.now(timezone.utc).isoformat()

    # Extract headers
    message_id = decode_header_value(msg.get("Message-ID", ""))
    if not message_id:
        # Skip messages without Message-ID (can't deduplicate)
        return None

    # Normalize Message-ID (with angle brackets for storage)
    normalized_message_id = normalize_message_id(message_id)

    # Extract addresses (RFC 5322 standard fields -> data)
    from_addr = decode_header_value(msg.get("From", ""))
    to_addrs = parse_addresses(msg.get("To", ""))
    cc_addrs = parse_addresses(msg.get("Cc", ""))
    bcc_addrs = parse_addresses(msg.get("Bcc", ""))

    # Extract subject (RFC 5322 standard field -> data)
    subject = decode_header_value(msg.get("Subject", ""))

    # Extract dates (RFC 5322 standard field -> data)
    sent_at = parse_date(msg.get("Date", ""))
    if not sent_at:
        sent_at = realized_at  # Fallback to import time

    # Extract threading headers (RFC 5322 standard fields -> data)
    references_raw = msg.get("References", "")
    references = parse_references(references_raw) if references_raw else None

    in_reply_to_raw = msg.get("In-Reply-To", "")
    in_reply_to = strip_angle_brackets(in_reply_to_raw) if in_reply_to_raw else None

    # Extract body
    plain_text = extract_plain_text_body(msg)
    html_body = extract_html_body(msg)

    # Determine content type and body
    if plain_text:
        body = plain_text
        content_type = "text/plain"
    elif html_body:
        body = html_body
        content_type = "text/html"
    else:
        body = ""
        content_type = "text/plain"

    # Extract attachments
    attachment_filenames = extract_attachment_filenames(msg)
    has_attach = has_attachments(msg)
    attach_count = count_attachments(msg)

    # Extract GMail-specific headers (provider-specific -> metadata)
    gmail_thread_id = msg.get("X-Gm-Thrid")

    # Build metadata (provider-specific)
    metadata = {
        "provider": "google",
        "source_file": source_file,
    }
    if gmail_thread_id:
        metadata["gmail_thread_id"] = gmail_thread_id
    if html_body and content_type == "text/plain":
        # Store HTML in metadata if we're using plain text as primary body
        metadata["html_body"] = html_body[:10000]  # Truncate for storage

    # Build data (RFC 5322 standard fields)
    data = {
        "rfc_message_id": normalized_message_id,
        "from_address": from_addr,
        "to_addresses": to_addrs,
        "cc_addresses": cc_addrs if cc_addrs else None,
        "bcc_addresses": bcc_addrs if bcc_addrs else None,
        "sent_at": sent_at,
        "received_at": None,  # Could extract from other headers
        "references": references,
        "in_reply_to": in_reply_to,
        "title": subject,
        "description": body,
        "content_type": content_type,
        "has_attachments": has_attach,
        "attachment_count": attach_count,
        "attachment_filenames": attachment_filenames if attachment_filenames else [],
    }

    # Validate required fields
    try:
        validate_email_data(data)
    except ValueError as e:
        # Skip invalid emails
        print(f"Warning: Skipping invalid email: {e}")
        return None

    return {
        "_type": "Email",
        "realized_at": realized_at,
        "canonical_at": sent_at,
        "fidelity": "full",
        "data": data,
        "metadata": metadata,
    }


# ============================================================================
# IMPORT PIPELINE
# ============================================================================

class EmailImporter:
    """Abstract base for email import strategies.

    Subclasses must implement fetch_emails() to provide emails from their source.
    The base class handles deduplication, threading, and batching.
    """

    def __init__(self, soil: Soil, batch_size: int = 100):
        """Initialize importer.

        Args:
            soil: Soil database instance
            batch_size: Number of emails to process before committing
        """
        self.soil = soil
        self.batch_size = batch_size
        self.email_index = self._build_index()
        self.stats = {
            "processed": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "relations_created": 0,
        }

    def _build_index(self) -> dict[str, str]:
        """Build rfc_message_id -> uuid index for deduplication.

        Scans existing Email items in database and builds mapping.

        Returns:
            Dict mapping rfc_message_id to item UUID
        """
        index = {}
        emails = self.soil.list_items(_type="Email", limit=1000000)
        for email_item in emails:
            message_id = email_item.data.get("rfc_message_id")
            if message_id:
                index[message_id] = email_item.uuid
        return index

    def import_email(self, email: dict) -> tuple[bool, int]:
        """Import single email with deduplication and threading.

        Args:
            email: Email dict with uuid, _type, data, metadata

        Returns:
            Tuple of (imported: bool, relations_created: int)
        """
        message_id = email["data"]["rfc_message_id"]

        # Check for duplicates
        if message_id in self.email_index:
            self.stats["skipped"] += 1
            return (False, 0)

        # Create Email item
        email_item = create_email_item(**email)
        uuid = self.soil.create_fact(email_item)
        self.stats["imported"] += 1
        self.email_index[message_id] = uuid

        # Create threading relations
        relations_created = self._create_threading_relations(email, uuid)

        return (True, relations_created)

    def _create_threading_relations(self, email: dict, email_uuid: str) -> int:
        """Create replies_to relations for email.

        Args:
            email: Email dict
            email_uuid: UUID of imported email

        Returns:
            Number of relations created
        """
        from mbox_importer.email_parser import create_threading_relations

        relations = create_threading_relations(
            {**email, "uuid": email_uuid},
            self.email_index
        )

        count = 0
        for rel_dict in relations:
            # Convert days since epoch
            epoch = datetime(2020, 1, 1, tzinfo=timezone.utc)
            created_at = (datetime.now(timezone.utc) - epoch).days

            relation = SystemRelation(
                uuid=generate_soil_uuid(),
                kind=rel_dict["kind"],
                source=rel_dict["source"],
                source_type=rel_dict["source_type"],
                target=rel_dict["target"],
                target_type=rel_dict["target_type"],
                created_at=created_at,
                evidence=rel_dict["evidence"],
                metadata=None,
            )
            self.soil.create_relation(relation)
            count += 1

        self.stats["relations_created"] += count
        return count

    def import_all(self, verbose: bool = True) -> dict:
        """Import all emails from source.

        Args:
            verbose: Print progress messages

        Returns:
            Import statistics
        """
        if verbose:
            print(f"Starting import from {self.__class__.__name__}...")
            print(f"Batch size: {self.batch_size}")

        with self.soil:
            for email in self.fetch_emails():
                self.stats["processed"] += 1

                # Print progress
                if verbose and self.stats["processed"] % 100 == 0:
                    print(f"Processed: {self.stats['processed']} emails, "
                          f"imported: {self.stats['imported']}, "
                          f"skipped: {self.stats['skipped']}")

                try:
                    self.import_email(email)
                except Exception as e:
                    self.stats["errors"] += 1
                    if self.stats["errors"] <= 10:  # Limit error spam
                        print(f"Error importing email: {e}")
                    continue

                # Commit batch
                if self.stats["imported"] % self.batch_size == 0:
                    if verbose:
                        print(f"Batch commit: {self.stats['imported']} items imported")

        if verbose:
            self._print_stats()

        return self.stats

    def _print_stats(self):
        """Print import statistics."""
        print()
        print("=" * 50)
        print("IMPORT COMPLETE")
        print("=" * 50)
        print(f"Processed:   {self.stats['processed']}")
        print(f"Imported:    {self.stats['imported']}")
        print(f"Skipped:     {self.stats['skipped']}")
        print(f"Errors:      {self.stats['errors']}")
        print(f"Relations:   {self.stats['relations_created']}")
        print("=" * 50)

    def fetch_emails(self):
        """Fetch emails from source. Must be implemented by subclasses.

        Yields:
            Email dicts with uuid, _type, data, metadata
        """
        raise NotImplementedError("Subclasses must implement fetch_emails()")


class MboxImporter(EmailImporter):
    """Bulk import from mbox file (Google Takeout format)."""

    def __init__(self, soil: Soil, mbox_path: str | Path, batch_size: int = 100):
        """Initialize mbox importer.

        Args:
            soil: Soil database instance
            mbox_path: Path to mbox file
            batch_size: Number of messages to process before committing
        """
        super().__init__(soil, batch_size)
        self.mbox_path = Path(mbox_path)
        self._limit: int | None = None

    def fetch_emails(self):
        """Yield parsed emails from mbox file.

        Yields:
            Email dicts
        """
        if not self.mbox_path.exists():
            raise FileNotFoundError(f"Mbox file not found: {self.mbox_path}")

        mbox = mailbox.mbox(str(self.mbox_path))
        realized_at = datetime.now(timezone.utc).isoformat()

        for i, msg in enumerate(mbox):
            if self._limit and i >= self._limit:
                break

            try:
                email_dict = mbox_message_to_email_item(
                    msg,
                    source_file=self.mbox_path.name,
                    realized_at=realized_at,
                )
                if email_dict:
                    yield email_dict
            except Exception as e:
                self.stats["errors"] += 1
                if self.stats["errors"] <= 10:  # Limit error spam
                    print(f"Error parsing mbox message: {e}")
                continue

    # import_mbox method for backwards compatibility
    def import_mbox(
        self,
        mbox_path: str | Path | None = None,
        limit: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Import emails from mbox file (backwards compatible method).

        Args:
            mbox_path: Path to mbox file (optional, uses __init__ path if not provided)
            limit: Maximum number of messages to import (for testing)
            verbose: Print progress messages

        Returns:
            Import statistics
        """
        if verbose:
            print(f"Importing from: {self.mbox_path}")
            print(f"Batch size: {self.batch_size}")

        if limit:
            if verbose:
                print(f"Limit: {limit} messages")
            self._limit = limit

        # Use parent class import_all method
        stats = self.import_all(verbose=verbose)

        # Reset limit
        self._limit = None

        return stats


# ============================================================================
# CLI
# ============================================================================

def main():
    """Command-line interface for mbox import."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import emails from mbox file into MemoGarden Soil"
    )
    parser.add_argument(
        "mbox_file",
        help="Path to mbox file (Google Takeout format)"
    )
    parser.add_argument(
        "--db",
        default="soil.db",
        help="Path to Soil database file (default: soil.db)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of messages to import (for testing)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for commits (default: 100)"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize database schema if not exists"
    )

    args = parser.parse_args()

    # Open Soil database
    soil = Soil(args.db)

    # Initialize schema if requested
    if args.init:
        try:
            version = soil.get_schema_version()
            print(f"Database already initialized (schema {version})")
        except Exception:
            # Database not initialized
            print("Initializing Soil database schema...")
            soil.init_schema()
            print(f"Schema version: {soil.get_schema_version()}")

    # Create importer
    importer = MboxImporter(soil, mbox_path=args.mbox_file, batch_size=args.batch_size)

    # Import
    try:
        importer.import_mbox(limit=args.limit)
    except Exception as e:
        print(f"Import failed: {e}")
        raise
    finally:
        soil.close()


if __name__ == "__main__":
    main()
