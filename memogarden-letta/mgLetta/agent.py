"""MemoGarden agent creation for Letta.

This module provides helper functions to create Letta agents with
MemoGarden memory blocks and tools.
"""

from typing import Any, Optional

from mgLetta.blocks import (
    MemoGardenProjectBlock,
    ArtifactSummary,
    create_memogarden_blocks,
)
from mgLetta.client import MemoGardenMemoryClient
from mgLetta.tools import (
    set_memogarden_client,
    memogarden_send_message_sync,
    memogarden_create_artifact_sync,
    memogarden_get_artifact_sync,
    memogarden_commit_artifact_sync,
    memogarden_search_sync,
    memogarden_refresh_memory_sync,
)


async def create_memogarden_blocks_async(
    base_url: str,
    api_key: str,
    scope_uuid: str,
    participant_uuid: Optional[str] = None,
    artifact_limit: int = 10,
    message_limit: int = 50,
) -> list[dict[str, Any]]:
    """Create Letta memory blocks from MemoGarden state.

    This function queries MemoGarden and returns Letta-compatible
    Block dictionaries ready for agent creation.

    Args:
        base_url: MemoGarden API base URL
        api_key: MemoGarden API key
        scope_uuid: UUID of the Scope to track
        participant_uuid: Optional UUID of the agent participant
        artifact_limit: Max artifacts to include in memory
        message_limit: Max messages to include in memory

    Returns:
        List of Letta Block dictionaries

    Example:
        blocks = await create_memogarden_blocks_async(
            base_url="http://localhost:5000",
            api_key="mg_sk_agent_...",
            scope_uuid="core_123"
        )

        # Use with Letta
        from letta import create_agent

        agent = await create_agent(
            name="MyAgent",
            memory_blocks=blocks,
            tools=memogarden_tools
        )
    """
    client = MemoGardenMemoryClient(
        base_url=base_url,
        api_key=api_key,
        scope_uuid=scope_uuid,
        participant_uuid=participant_uuid,
        artifact_limit=artifact_limit,
        message_limit=message_limit,
    )

    return await client.refresh_memory()


def create_memogarden_blocks(
    base_url: str,
    api_key: str,
    scope_uuid: str,
    participant_uuid: Optional[str] = None,
    artifact_limit: int = 10,
    message_limit: int = 50,
) -> list[dict[str, Any]]:
    """Synchronous version of create_memogarden_blocks_async."""
    import asyncio
    return asyncio.run(
        create_memogarden_blocks_async(
            base_url=base_url,
            api_key=api_key,
            scope_uuid=scope_uuid,
            participant_uuid=participant_uuid,
            artifact_limit=artifact_limit,
            message_limit=message_limit,
        )
    )


def get_memogarden_tools() -> list[dict[str, Any]]:
    """Get MemoGarden tool definitions for Letta agent.

    Returns a list of tool dictionaries compatible with Letta's
    tool registration system.

    Returns:
        List of tool definition dictionaries

    Example:
        tools = get_memogarden_tools()

        # Register with Letta
        for tool in tools:
            await agent_manager.register_tool(tool)
    """
    return [
        {
            "name": "memogarden_send_message",
            "description": "Send a message to the MemoGarden conversation log.",
            "function": memogarden_send_message_sync,
            "parameters": {
                "content": {
                    "type": "string",
                    "description": "The message content to send",
                },
                "log_uuid": {
                    "type": "string",
                    "description": "Optional ConversationLog UUID (default: current scope's log)",
                    "required": False,
                },
                "sender": {
                    "type": "string",
                    "description": "Sender type (default: 'agent')",
                    "required": False,
                },
            },
        },
        {
            "name": "memogarden_create_artifact",
            "description": "Create a new artifact in the current scope.",
            "function": memogarden_create_artifact_sync,
            "parameters": {
                "label": {
                    "type": "string",
                    "description": "Human-readable label for the artifact",
                },
                "content": {
                    "type": "string",
                    "description": "Initial content of the artifact",
                },
                "content_type": {
                    "type": "string",
                    "description": "MIME type (default: 'text/markdown')",
                    "required": False,
                },
            },
        },
        {
            "name": "memogarden_get_artifact",
            "description": "Get an artifact's content by UUID or label.",
            "function": memogarden_get_artifact_sync,
            "parameters": {
                "artifact_uuid": {
                    "type": "string",
                    "description": "UUID of the artifact",
                    "required": False,
                },
                "label": {
                    "type": "string",
                    "description": "Label of the artifact (used if UUID not provided)",
                    "required": False,
                },
            },
        },
        {
            "name": "memogarden_commit_artifact",
            "description": (
                "Commit a delta operation to an artifact. "
                "Delta syntax: +N:^abc (add), -N (remove), "
                "~N:^old→^new (replace), >N@M (move)"
            ),
            "function": memogarden_commit_artifact_sync,
            "parameters": {
                "artifact_uuid": {
                    "type": "string",
                    "description": "UUID of the artifact to modify",
                },
                "ops": {
                    "type": "string",
                    "description": "Delta operations string (e.g., '+5:^abc -10')",
                },
                "references": {
                    "type": "array",
                    "description": "Optional list of fragment references",
                    "required": False,
                },
                "based_on_commit": {
                    "type": "string",
                    "description": "Optional commit hash for optimistic locking",
                    "required": False,
                },
            },
        },
        {
            "name": "memogarden_search",
            "description": "Search for entities, facts, or relations in MemoGarden.",
            "function": memogarden_search_sync,
            "parameters": {
                "term": {
                    "type": "string",
                    "description": "Search term",
                },
                "target_type": {
                    "type": "string",
                    "description": "Type to search ('entity', 'fact', 'relation', or 'all')",
                    "required": False,
                },
                "coverage": {
                    "type": "string",
                    "description": "Search scope ('names', 'content', or 'full')",
                    "required": False,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "required": False,
                },
            },
        },
        {
            "name": "memogarden_refresh_memory",
            "description": (
                "Refresh the agent's memory blocks from MemoGarden state. "
                "Updates project context, artifacts, and conversation."
            ),
            "function": memogarden_refresh_memory_sync,
            "parameters": {},
        },
    ]


async def create_memogarden_agent(
    base_url: str,
    api_key: str,
    scope_uuid: str,
    agent_name: str,
    participant_uuid: Optional[str] = None,
    system_prompt: Optional[str] = None,
    model: str = "openai/gpt-4o-mini",
    artifact_limit: int = 10,
    message_limit: int = 50,
) -> Any:
    """Create a Letta agent with MemoGarden memory blocks and tools.

    This is a convenience function that creates a fully configured Letta
    agent with MemoGarden integration.

    Args:
        base_url: MemoGarden API base URL
        api_key: MemoGarden API key
        scope_uuid: UUID of the Scope to track
        agent_name: Name for the agent
        participant_uuid: Optional UUID of the agent participant
        system_prompt: Optional custom system prompt
        model: Model to use (format: provider/model-name)
        artifact_limit: Max artifacts to include in memory
        message_limit: Max messages to include in memory

    Returns:
        Letta Agent instance

    Example:
        agent = await create_memogarden_agent(
            base_url="http://localhost:5000",
            api_key="mg_sk_agent_...",
            scope_uuid="core_123",
            agent_name="ProjectAgent"
        )

        # Run the agent
        response = await agent.step("Create a README for the project")
    """
    # Import Letta here to avoid hard dependency
    try:
        from letta.schemas.block import CreateBlock
        from letta.schemas.llm_config import LLMConfig
        from letta.schemas.embedding_config import EmbeddingConfig
    except ImportError:
        raise ImportError(
            "Letta is required to create agents. "
            "Install with: pip install letta"
        )

    # Create memory blocks
    blocks_data = await create_memogarden_blocks_async(
        base_url=base_url,
        api_key=api_key,
        scope_uuid=scope_uuid,
        participant_uuid=participant_uuid,
        artifact_limit=artifact_limit,
        message_limit=message_limit,
    )

    # Convert to Letta CreateBlock objects
    blocks = []
    for block_data in blocks_data:
        blocks.append(
            CreateBlock(
                label=block_data["label"],
                value=block_data["value"],
                description=block_data.get("description"),
                read_only=block_data.get("read_only", False),
                limit=block_data.get("limit", 2000),
            )
        )

    # Create client for tools
    client = MemoGardenMemoryClient(
        base_url=base_url,
        api_key=api_key,
        scope_uuid=scope_uuid,
        participant_uuid=participant_uuid,
        artifact_limit=artifact_limit,
        message_limit=message_limit,
    )
    set_memogarden_client(client)

    # Default system prompt
    if system_prompt is None:
        system_prompt = f"""You are an AI assistant working in a MemoGarden project.

You have access to:
- Project context information (scope, artifacts, participants)
- Conversation history
- Artifact content and editing tools
- Search capabilities

Your goal is to help the operator with tasks in the current project.
Use the memogarden_ tools to interact with the project state.

Scope UUID: {scope_uuid}
"""

    # Note: Full agent creation requires Letta server/infrastructure
    # This returns a configuration dict that can be used with Letta
    return {
        "name": agent_name,
        "system": system_prompt,
        "memory_blocks": blocks,
        "tools": get_memogarden_tools(),
        "model": model,
        "config": {
            "memogarden": {
                "base_url": base_url,
                "scope_uuid": scope_uuid,
                "participant_uuid": participant_uuid,
            }
        }
    }
