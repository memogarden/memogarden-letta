# Letta Integration Guide

This document provides reference information about the Letta codebase and how MemoGarden integrates with it.

## Letta Codebases

MemoGarden has two Letta codebases cloned for reference:

1. **letta-python** (`/letta-python/`) - Python client library for Letta API
2. **letta** (`/letta/`) - Core Letta server and agent implementation

**IMPORTANT:** These are read-only references. Do not commit changes to these repos.

## Key Letta Concepts

### Memory Blocks

Letta uses memory blocks to provide agents with persistent context.

```python
# Letta Block schema (from letta/schemas/block.py)
class Block(BaseBlock):
    id: str                    # Unique ID
    value: str                 # Content of the block
    label: Optional[str]       # Label (e.g., 'human', 'persona')
    description: Optional[str] # Description of the block
    limit: int = 2000          # Character limit
    read_only: bool = False    # Whether agent can modify
    hidden: Optional[bool]     # Whether to hide from context
    metadata: Optional[dict]   # Additional metadata
    tags: Optional[List[str]]  # Associated tags
```

### Agent State

```python
# From letta/schemas/agent.py
class AgentState(OrmMetadataBase):
    id: str
    name: str
    system: str                # System prompt
    agent_type: AgentType      # Type of agent
    memory: Memory             # In-context memory
    blocks: List[Block]        # Memory blocks (newer)
    tools: List[Tool]          # Available tools
    sources: List[Source]      # Data sources
    # ... other fields
```

### Memory Class

```python
# From letta/schemas/memory.py
class Memory(BaseModel):
    blocks: List[Block]        # Core memory blocks
    file_blocks: List[FileBlock]  # File blocks
    agent_type: AgentType

    def compile(self, tool_usage_rules=None, sources=None) -> str:
        """Render memory into prompt string."""
```

## Creating Letta Agents

### Block Creation

```python
from letta.schemas.block import CreateBlock

blocks = [
    CreateBlock(
        label="persona",
        value="You are a helpful assistant.",
        description="Agent persona",
    ),
    CreateBlock(
        label="human",
        value="User is working on a project.",
        description="Human description",
    ),
]
```

### Tool Registration

```python
from letta.schemas.tool import Tool

# Define a tool function
def my_tool(param1: str) -> str:
    """Tool description."""
    return f"Result: {param1}"

# Create tool from function
tool = Tool(
    name="my_tool",
    description=my_tool.__doc__,
    source_type="python",
    source_code=parse_source_code(my_tool),
    json_schema=generate_schema(my_tool, None),
)

# Register with agent
await server.tool_manager.create_or_update_tool_async(tool, actor=user)
```

## MemoGarden-Letta Integration

### Memory Blocks

MemoGarden provides four block types via `mgLetta`:

1. **project_context** - Scope/project information
2. **artifacts** - Artifact summaries
3. **conversation** - Recent message history
4. **context_frame** - RFC-003 context state

### Tools

MemoGarden provides six tools via `mgLetta`:

1. `memogarden_send_message` - Send message to conversation log
2. `memogarden_create_artifact` - Create new artifact
3. `memogarden_get_artifact` - Get artifact content
4. `memogarden_commit_artifact` - Commit delta operations
5. `memogarden_search` - Search entities/facts/relations
6. `memogarden_refresh_memory` - Refresh memory blocks

### Usage Example

```python
from mgLetta import create_memogarden_agent

agent = await create_memogarden_agent(
    base_url="http://localhost:5000",
    api_key="mg_sk_agent_...",
    scope_uuid="core_123",
    agent_name="ProjectAgent"
)

# Run the agent
response = await agent.step("Create a README for the project")
```

## Key Files in Letta Codebase

### Memory System
- `letta/letta/schemas/memory.py` - Memory class and compilation
- `letta/letta/schemas/block.py` - Block schemas
- `letta/letta/agents/base_agent.py` - Base agent with memory rebuilding

### Agent Creation
- `letta/letta/schemas/agent.py` - AgentState schema
- `letta/letta/agents/letta_agent.py` - Main agent implementation

### Tools
- `letta/letta/functions/functions.py` - Tool definitions
- `letta/letta/functions/schema_generator.py` - Schema generation

### Client
- `letta-python/src/letta_client/` - Python client library
- `letta-python/src/letta_client/resources/agents/` - Agent management

## Session 21 Status

**Completed:** 2026-02-15

- Created `memogarden-letta/` package
- Implemented MemoGardenMemoryClient
- Created Letta-compatible memory blocks
- Added toolcall wrappers for agents
- 10/10 unit tests passing

**TODO:**
- Full end-to-end integration testing with Letta server
- ContextFrame integration (RFC-003)
- ConversationLog query integration
