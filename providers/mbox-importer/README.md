# Mbox Email Importer

Import emails from mbox files (Google Takeout format) into MemoGarden Soil database.

## Features

- Bulk import from mbox files
- RFC 5322 email parsing
- Deduplication by Message-ID
- Thread reconstruction (replies_to relations)
- Attachment detection and filename extraction
- Provider-agnostic data/metadata separation

## Installation

```bash
cd providers/mbox-importer
poetry install
```

## Usage

### Command Line

```bash
poetry run python -m mbox_importer.import_mbox path/to/emails.mbox --db soil.db --init
```

### Python API

```python
from system.soil import Soil
from mbox_importer.import_mbox import MboxImporter

soil = Soil("soil.db")
soil.init_schema()

importer = MboxImporter(soil, mbox_path="emails.mbox")
stats = importer.import_mbox(limit=100)  # For testing
print(stats)
```

## Data Model

Emails are stored as Soil Items with:
- **_type**: "Email"
- **data**: RFC 5322 standard fields (provider-agnostic)
  - rfc_message_id, from_address, to_addresses, sent_at, etc.
- **metadata**: Provider-specific fields
  - provider: "google"
  - source_file, gmail_thread_id, etc.

## License

MIT
