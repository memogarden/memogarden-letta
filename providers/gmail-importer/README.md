# Gmail Email Importer

Import emails from Gmail API into MemoGarden Soil database.

## Status

**Currently a stub** - This package provides the base EmailImporter class and a GmailImporter stub for future implementation.

## Features

- Abstract EmailImporter base class with:
  - Deduplication by Message-ID
  - Batch processing with configurable batch size
  - Thread reconstruction (replies_to relations)
  - Progress tracking and statistics
- GmailImporter stub for future OAuth integration

## Installation

```bash
cd providers/gmail-importer
poetry install
```

## Future Usage

### Python API

```python
from system.soil import Soil
from gmail_importer.importer import GmailImporter

soil = Soil("soil.db")
soil.init_schema()

importer = GmailImporter(soil, account_id="user@example.com")
stats = importer.import_all(since=datetime(2024, 1, 1))
print(stats)
```

## Implementation Status

- [x] EmailImporter abstract base class
- [x] Deduplication logic
- [x] Threading relations
- [ ] Gmail API OAuth integration
- [ ] HACM credential management
- [ ] Incremental sync
- [ ] Labels support

## License

MIT
