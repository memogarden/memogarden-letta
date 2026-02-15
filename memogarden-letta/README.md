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

# Format code
poetry run ruff check .
poetry run ruff format .
```

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

## Session 21 Status

**Status**: In Progress

Deliverables:
- [x] Create `memogarden-letta/` package structure
- [x] Implement memory projection functions
- [x] Define memory block schema (Letta-compatible)
- [x] Toolcall wrappers for agent operations
- [ ] Integration tests

## See Also

- [MemoGarden Core](../memogarden-system/)
- [MemoGarden API](../memogarden-api/)
- [MemoGarden Client](../memogarden-client/)
- [Letta Documentation](https://letta.ai/)
