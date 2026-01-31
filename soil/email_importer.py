"""Abstract email importer for MemoGarden Soil.

Provides base class for email import strategies (mbox, Gmail API, etc.).
Implements deduplication, threading, and batching logic shared across importers.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# Import from system.soil instead of local soil package
from system.soil import Soil, create_email_item, generate_soil_uuid, SystemRelation
from soil.email_parser import normalize_message_id


# ============================================================================
# ABSTRACT BASE CLASS
# ============================================================================

class EmailImporter(ABC):
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
        uuid = self.soil.create_item(email_item)
        self.stats["imported"] += 1
        self.email_index[message_id] = uuid

        # Create threading relations
        relations_created = self._create_threading_relations(email, uuid)

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
        from soil.email_parser import create_threading_relations

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

    @abstractmethod
    def fetch_emails(self) -> Iterator[dict]:
        """Fetch emails from source. Must be implemented by subclasses.

        Yields:
            Email dicts with uuid, _type, data, metadata
        """
        pass


# ============================================================================
# CONCRETE IMPORTERS
# ============================================================================

# MboxImporter is implemented in soil/import_mbox.py
# GmailImporter stub is below


class GmailImporter(EmailImporter):
    """Incremental import from Gmail API (future implementation).

    This is a stub for future Gmail API integration.
    Will use HACM (Headless Agent Credential Manager) for OAuth tokens.
    """

    def __init__(self, soil: Soil, account_id: str, batch_size: int = 50):
        """Initialize Gmail importer.

        Args:
            soil: Soil database instance
            account_id: Gmail account identifier (for HACM lookup)
            batch_size: Batch size for API calls (default: 50)
        """
        super().__init__(soil, batch_size)
        self.account_id = account_id
        # TODO: Load refresh token from HACM
        # TODO: Build Gmail service
        # self.service = build_gmail_service(account_id)

    def fetch_emails(self, since: datetime | None = None) -> Iterator[dict]:
        """Fetch emails from Gmail API since last sync.

        Args:
            since: Only fetch emails after this timestamp (for incremental sync)

        Yields:
            Email dicts

        Raises:
            NotImplementedError: Not yet implemented
        """
        raise NotImplementedError("Gmail sync not yet implemented")

    def translate_gmail_to_email(self, gmail_msg: dict) -> dict:
        """Translate Gmail API response to Email item dict.

        Args:
            gmail_msg: Gmail API message object

        Returns:
            Email dict with _type, data, metadata

        Raises:
            NotImplementedError: Not yet implemented
        """
        # TODO: Map Gmail API schema to RFC 5322 schema
        # - GmailMessage.id -> rfc_message_id (with <>)
        # - GmailMessage.payload.headers -> From, To, Subject, etc.
        # - GmailMessage.threadId -> metadata.gmail_thread_id
        # - GmailMessage.labelIds -> metadata.gmail_labels
        raise NotImplementedError("Gmail translation not yet implemented")
