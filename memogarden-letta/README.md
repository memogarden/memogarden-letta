# mgLetta: MemoGarden Memory Blocks for Letta Agents

MemoGarden memory projections for Letta agents - enables agents to maintain
context about projects, artifacts, and conversations stored in MemoGarden.

## Overview

`mgLetta` provides memory block projections that convert MemoGarden state into
Letta-compatible memory blocks. This allows agents to:

- Track project/scope context (participants, artifacts, branches)
- Access artifact summaries and content
- Review conversation history
- Interact with MemoGarden via semantic tools

## Installation

```bash
# Install with Poetry
poetry add mgLetta

# Or from local path
poetry add ../memogarden-letta
```

## Quick Start

```python
from mgLetta import create_memogarden_agent

# Create an agent with MemoGarden memory
agent = await create_memogarden_agent(
    base_url="http://localhost:5000",
    api_key="mg_sk_agent_...",
    scope_uuid="core_123",
    agent_name="ProjectAgent"
)

# Run the agent
response = await agent.step("Create a README for the project")
print(response.result)
```

## Memory Blocks

### Project Context Block
Contains information about the current Scope:
- Project label and UUID
- Active participants
- Artifact count
- Active conversation branches

### Artifacts Block
Summaries of artifacts in the scope:
- Artifact labels and UUIDs
- Content types and line counts
- Content previews

### Conversation Block
Recent message history:
- Sender and timestamp
- Message content
- Fragment references

### Context Frame Block
RFC-003 context state:
- Active containers
- Head item UUID

## Tools

Agents have access to these MemoGarden tools:

| Tool | Description |
|------|-------------|
| `memogarden_send_message` | Send message to conversation log |
| `memogarden_create_artifact` | Create new artifact |
| `memogarden_get_artifact` | Get artifact content |
| `memogarden_commit_artifact` | Commit delta operations |
| `memogarden_search` | Search entities/facts/relations |
| `memogarden_refresh_memory` | Refresh memory blocks |

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest
# Or use the standardized test runner
./run_tests.sh

# Format code
poetry run ruff check .
poetry run ruff format .
```

## Testing

The test suite has three levels:

| Level | Focus | Tests | Requirements |
|-------|-------|-------|--------------|
| **Level 1** | Schema validation | 5 tests | letta-client installed |
| **Level 2** | Content invariants | 6 tests | letta-client installed |
| **Level 3** | Live API tests | 2 tests | LETTA_API_KEY environment variable |

### Key Invariants Tested

| Invariant | Test | Rationale |
|-----------|------|-----------|
| Block schema compatibility | `test_*_valid_letta_schema` | `Block(**our_dict)` must not raise ValidationError |
| Required fields present | `test_all_blocks_have_required_fields` | Every block has `value`, `label` |
| read_only flag | `test_all_blocks_marked_read_only` | All MemoGarden blocks are read-only |
| Unique labels | `test_all_blocks_have_unique_labels` | No duplicate labels (Letta requirement) |
| block_type in metadata | `test_all_blocks_have_metadata_block_type` | Identifiable as MemoGarden blocks |
| JSON serializable | `test_blocks_are_json_serializable` | Can be sent to Letta API |

### Letta Block Schema Reference

From `letta-client==0.1.324`:
```python
Block(*, value: str, limit: Optional[int] = None, project_id: Optional[str] = None,
       name: Optional[str] = None, is_template: Optional[bool] = None,
       base_template_id: Optional[str] = None, deployment_id: Optional[str] = None,
       entity_id: Optional[str] = None, preserve_on_migration: Optional[bool] = None,
       label: Optional[str] = None, read_only: Optional[bool] = None,
       description: Optional[str] = None,
       metadata: Optional[Dict[str, Optional[Any]]] = None,
       hidden: Optional[bool] = None, id: Optional[str] = None,
       created_by_id: Optional[str] = None, last_updated_by_id: Optional[str] = None,
       **extra_data: Any) -> None
```

Our block format (`label`, `value`, `description`, `read_only`, `limit`, `metadata`) is fully compatible.

## Architecture

```
┌─────────────────┐
│  Letta Agent    │
│                 │
│  Memory Blocks  │◄─── mgLetta (projections)
│  + Tools        │◄─── mgLetta (functions)
└────────┬────────┘
         │
         │ Semantic API
         ▼
┌─────────────────┐
│  MemoGarden     │
│  Core + Soil    │
└─────────────────┘
```

## Session History

| Session | Description | Status |
|---------|-------------|--------|
| 21 | Letta Memory Block Projections | ✅ Complete |
| 22 | Integration Tests (schema validation, invariants, live API) | ✅ Complete |

## See Also

- [MemoGarden Core](../memogarden-system/)
- [MemoGarden API](../memogarden-api/)
- [MemoGarden Client](../memogarden-client/)
- [Letta Documentation](https://letta.ai/)
