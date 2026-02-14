# MemoGarden Utils

Shared utilities across MemoGarden packages.

## Utilities

- **datetime**: ISO 8601 datetime/date conversion
- **uid**: UUID generation and prefix handling
- **secret**: Secret generation (API keys, tokens, passwords)
- **hash_chain**: Entity hash computation for change tracking
- **recurrence**: iCal RRULE utilities
- **time**: Time horizon computation
- **config**: Configuration management

## Installation

```bash
poetry install
```

## Usage

```python
from utils import datetime, uid, secret, hash_chain, recurrence
from utils.config import Settings, get_config_path

# Generate UUID with prefix
entity_uuid = uid.add_core_prefix(uid.generate())

# Format datetime
timestamp = datetime.to_timestamp(datetime.now())

# Generate API key
api_key = secret.generate_api_key()
```

## Testing

```bash
./run_tests.sh
```

Or directly:

```bash
poetry run pytest
```
