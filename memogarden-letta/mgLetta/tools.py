"""MemoGarden tool functions for Letta agents.

This module provides tool functions that agents can call to interact
with MemoGarden (send messages, create artifacts, commit deltas, etc.).

These functions are designed to be registered with Letta's tool system
and called by the agent during execution.

Each function follows Letta's tool pattern:
- Takes agent_state as first parameter
- Returns a string description of the result
- Raises ValueError on errors
"""

import asyncio
from typing import Optional

from mgLetta.client import MemoGardenMemoryClient


# Global client reference - set by agent initialization
_memogarden_client: Optional[MemoGardenMemoryClient] = None


def set_memogarden_client(client: MemoGardenMemoryClient) -> None:
    """Set the global MemoGarden client for tool functions.

    This is called during agent initialization to provide tools
    with access to MemoGarden.

    Args:
        client: The MemoGardenMemoryClient instance
    """
    global _memogarden_client
    _memogarden_client = client


def _get_client() -> MemoGardenMemoryClient:
    """Get the global MemoGarden client, raising an error if not set."""
    if _memogarden_client is None:
        raise ValueError(
            "MemoGarden client not initialized. "
            "Call set_memogarden_client() before using tools."
        )
    return _memogarden_client


async def memogarden_send_message(
    content: str,
    log_uuid: Optional[str] = None,
    sender: str = "agent",
) -> str:
    """Send a message to the conversation log.

    Args:
        content: The message content to send
        log_uuid: Optional ConversationLog UUID (default: current scope's log)
        sender: Sender type (default: "agent")

    Returns:
        Confirmation message with the new message UUID

    Raises:
        ValueError: If the message send fails
    """
    client = _get_client()

    # Use current scope's log if not specified
    if log_uuid is None:
        log_uuid = client.config.scope_uuid

    response = await client.semantic.send_message(
        log_uuid=log_uuid,
        content=content,
        sender=sender,
    )

    if not response.ok:
        raise ValueError(f"Failed to send message: {response.error}")

    message_uuid = response.result.get("uuid", "unknown")
    return f"Message sent successfully (UUID: {message_uuid})"


async def memogarden_create_artifact(
    label: str,
    content: str,
    content_type: str = "text/markdown",
) -> str:
    """Create a new artifact in the current scope.

    Args:
        label: Human-readable label for the artifact
        content: Initial content of the artifact
        content_type: MIME type (default: "text/markdown")

    Returns:
        Confirmation message with the new artifact UUID

    Raises:
        ValueError: If artifact creation fails
    """
    client = _get_client()

    response = await client.semantic.create_artifact(
        label=label,
        content=content,
        content_type=content_type,
    )

    if not response.ok:
        raise ValueError(f"Failed to create artifact: {response.error}")

    artifact_uuid = response.result.get("uuid", "unknown")
    return f"Artifact '{label}' created successfully (UUID: {artifact_uuid})"


async def memogarden_get_artifact(
    artifact_uuid: Optional[str] = None,
    label: Optional[str] = None,
) -> str:
    """Get an artifact's content by UUID or label.

    If both are provided, UUID takes precedence.
    If only label is provided, searches for artifacts with that label.

    Args:
        artifact_uuid: UUID of the artifact
        label: Label of the artifact (used if UUID not provided)

    Returns:
        The artifact's content as a string

    Raises:
        ValueError: If the artifact is not found
    """
    client = _get_client()

    if artifact_uuid:
        # Get by UUID
        response = await client.semantic.get(target=artifact_uuid)
    elif label:
        # Search by label
        response = await client.semantic.search(
            target_type="entity",
            query=label,
            coverage="names",
        )

        if not response.ok:
            raise ValueError(f"Failed to search for artifact: {response.error}")

        results = response.result.get("results", [])
        if not results:
            raise ValueError(f"No artifact found with label: {label}")

        # Get the first matching artifact
        artifact_uuid = results[0].get("uuid")
        response = await client.semantic.get(target=artifact_uuid)
    else:
        raise ValueError("Must provide either artifact_uuid or label")

    if not response.ok:
        raise ValueError(f"Failed to get artifact: {response.error}")

    result = response.result
    content = result.get("data", {}).get("content", "")
    label_val = result.get("data", {}).get("label", "Unknown")

    return f"Artifact: {label_val}\n\n{content}"


async def memogarden_commit_artifact(
    artifact_uuid: str,
    ops: str,
    references: Optional[list[str]] = None,
    based_on_commit: Optional[str] = None,
) -> str:
    """Commit a delta operation to an artifact.

    Delta operations syntax:
    - +N:^abc   - Add fragment at line N
    - -N        - Remove line N
    - ~N:^old→^new  - Replace line N content
    - >N@M      - Move line N to position M

    Args:
        artifact_uuid: UUID of the artifact to modify
        ops: Delta operations string (e.g., "+5:^abc -10")
        references: Optional list of fragment references
        based_on_commit: Optional commit hash for optimistic locking

    Returns:
        Confirmation message with new commit hash

    Raises:
        ValueError: If commit fails or has conflicts
    """
    client = _get_client()

    # Get current artifact hash if based_on_commit not provided
    if based_on_commit is None:
        response = await client.semantic.get(target=artifact_uuid)
        if not response.ok:
            raise ValueError(f"Failed to get artifact: {response.error}")
        based_on_commit = response.result.get("hash")

    response = await client.semantic.commit_artifact_delta(
        artifact=artifact_uuid,
        ops=ops,
        references=references or [],
        based_on_hash=based_on_commit,
    )

    if not response.ok:
        error = response.error
        # Check for conflict
        if error and "conflict" in str(error).lower():
            raise ValueError(
                f"Commit conflict: artifact was modified. "
                f"Please fetch latest version and retry."
            )
        raise ValueError(f"Failed to commit artifact: {error}")

    commit_hash = response.result.get("commit_hash", "unknown")
    return f"Artifact delta committed successfully (commit: {commit_hash})"


async def memogarden_search(
    term: str,
    target_type: str = "entity",
    coverage: str = "full",
    limit: int = 10,
) -> str:
    """Search for entities, facts, or relations in MemoGarden.

    Args:
        term: Search term
        target_type: Type to search ("entity", "fact", "relation", or "all")
        coverage: Search scope ("names", "content", or "full")
        limit: Maximum results to return

    Returns:
        Formatted search results

    Raises:
        ValueError: If search fails
    """
    client = _get_client()

    response = await client.semantic.search(
        target_type=target_type,  # type: ignore
        query=term,
        coverage=coverage,  # type: ignore
        limit=limit,
    )

    if not response.ok:
        raise ValueError(f"Search failed: {response.error}")

    result = response.result
    results = result.get("results", [])
    total = result.get("total", len(results))

    if not results:
        return f"No results found for '{term}' (total: {total})"

    lines = [f"Search results for '{term}' (showing {len(results)}/{total}):"]

    for i, item in enumerate(results, 1):
        item_type = item.get("_type", "Unknown")
        uuid = item.get("uuid", "")
        label = item.get("data", {}).get("label", "")

        lines.append(f"\n{i}. [{item_type}] {label}")
        lines.append(f"   UUID: {uuid}")

        # Add content preview for entities
        if item_type == "Artifact":
            content = item.get("data", {}).get("content", "")
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                lines.append(f"   Preview: {preview}")

    return "\n".join(lines)


async def memogarden_refresh_memory() -> str:
    """Refresh the agent's memory blocks from MemoGarden state.

    This updates the project context, artifacts, and conversation blocks
    with the latest data from MemoGarden.

    Returns:
        Confirmation of memory refresh

    Raises:
        ValueError: If refresh fails
    """
    client = _get_client()

    # Refresh memory
    blocks = await client.refresh_memory()

    # Update agent state blocks
    # Note: This is handled by the Letta agent's memory manager
    # The function here is for explicit refresh by the agent

    return f"Memory refreshed successfully. Updated {len(blocks)} blocks."


# Sync wrappers for Letta tool system (which uses sync functions)
def memogarden_send_message_sync(content: str, log_uuid: Optional[str] = None, sender: str = "agent") -> str:
    """Synchronous wrapper for memogarden_send_message."""
    return asyncio.run(memogarden_send_message(content, log_uuid, sender))


def memogarden_create_artifact_sync(label: str, content: str, content_type: str = "text/markdown") -> str:
    """Synchronous wrapper for memogarden_create_artifact."""
    return asyncio.run(memogarden_create_artifact(label, content, content_type))


def memogarden_get_artifact_sync(artifact_uuid: Optional[str] = None, label: Optional[str] = None) -> str:
    """Synchronous wrapper for memogarden_get_artifact."""
    return asyncio.run(memogarden_get_artifact(artifact_uuid, label))


def memogarden_commit_artifact_sync(
    artifact_uuid: str,
    ops: str,
    references: Optional[list[str]] = None,
    based_on_commit: Optional[str] = None,
) -> str:
    """Synchronous wrapper for memogarden_commit_artifact."""
    return asyncio.run(memogarden_commit_artifact(artifact_uuid, ops, references, based_on_commit))


def memogarden_search_sync(term: str, target_type: str = "entity", coverage: str = "full", limit: int = 10) -> str:
    """Synchronous wrapper for memogarden_search."""
    return asyncio.run(memogarden_search(term, target_type, coverage, limit))


def memogarden_refresh_memory_sync() -> str:
    """Synchronous wrapper for memogarden_refresh_memory."""
    return asyncio.run(memogarden_refresh_memory())
