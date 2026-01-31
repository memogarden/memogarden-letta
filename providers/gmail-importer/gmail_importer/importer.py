"""Gmail Email Importer for MemoGarden Soil.

Provides GmailImporter stub for future Gmail API integration.
The EmailImporter base class is imported from mbox-importer package.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

# Import from system.soil
from system.soil import Soil

# Import EmailImporter base class from mbox-importer
from mbox_importer.import_mbox import EmailImporter


# ============================================================================
# CONCRETE IMPORTERS
# ============================================================================


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

    def fetch_emails(self, since: Optional[datetime] = None) -> Iterator[dict]:
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
