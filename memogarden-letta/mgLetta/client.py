"""MemoGarden memory client for Letta agents.

This module provides the client that queries MemoGarden and projects
the state into Letta-compatible memory blocks.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from mg_client import MemoGardenClient
from mg_client.semantic import SemanticAPI

from mgLetta.blocks import (
    MemoGardenProjectBlock,
    ArtifactSummary,
    MemoGardenArtifactBlock,
    MessageSummary,
    MemoGardenConversationBlock,
    MemoGardenContextBlock,
    create_memogarden_blocks,
)


@dataclass
class MemoGardenMemoryConfig:
    """Configuration for MemoGarden memory projection.

    Attributes:
        base_url: MemoGarden API base URL
        api_key: MemoGarden API key
        scope_uuid: UUID of the Scope to track
        participant_uuid: UUID of the agent/participant
        artifact_limit: Max number of artifacts to include
        message_limit: Max number of messages to include
    """

    base_url: str
    api_key: str
    scope_uuid: str
    participant_uuid: Optional[str] = None
    artifact_limit: int = 10
    message_limit: int = 50


class MemoGardenMemoryClient:
    """Client for projecting MemoGarden state into Letta memory blocks.

    This client queries MemoGarden Core and Soil APIs and returns
    Letta-compatible memory block data.

    Example:
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_agent_...",
            scope_uuid="core_123",
            participant_uuid="agt_456"
        )

        # Get all memory blocks
        blocks = await client.refresh_memory()

        # Get specific block types
        project_block = await client.get_project_block()
        artifacts = await client.get_artifact_block()
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        scope_uuid: str,
        participant_uuid: Optional[str] = None,
        artifact_limit: int = 10,
        message_limit: int = 50,
    ):
        """Initialize the MemoGarden memory client.

        Args:
            base_url: MemoGarden API base URL
            api_key: MemoGarden API key for authentication
            scope_uuid: UUID of the Scope to track
            participant_uuid: Optional UUID of the agent participant
            artifact_limit: Max artifacts to include in memory
            message_limit: Max messages to include in memory
        """
        self.config = MemoGardenMemoryConfig(
            base_url=base_url,
            api_key=api_key,
            scope_uuid=scope_uuid,
            participant_uuid=participant_uuid,
            artifact_limit=artifact_limit,
            message_limit=message_limit,
        )
        self._client: Optional[MemoGardenClient] = None
        self._semantic: Optional[SemanticAPI] = None

    @property
    def client(self) -> MemoGardenClient:
        """Lazy-loaded MemoGarden client."""
        if self._client is None:
            self._client = MemoGardenClient(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
            )
        return self._client

    @property
    def semantic(self) -> SemanticAPI:
        """Lazy-loaded Semantic API client."""
        if self._semantic is None:
            self._semantic = self.client.semantic
        return self._semantic

    async def get_project_context(self) -> MemoGardenProjectBlock:
        """Get project context block for the current scope.

        Returns:
            MemoGardenProjectBlock with scope information
        """
        # Get the Scope entity
        response = await self.semantic.get_async(target=self.config.scope_uuid)

        if not response.ok:
            raise ValueError(f"Failed to get scope: {response.error}")

        scope_data = response.result

        return MemoGardenProjectBlock(
            scope_uuid=self.config.scope_uuid,
            label=scope_data.get("data", {}).get("label", "Unknown Project"),
            active_participants=scope_data.get("data", {}).get("active_participants", []),
            artifact_count=len(scope_data.get("data", {}).get("artifact_uuids", [])),
            active_branches=1,  # TODO: Query actual branch count
            root_summary=None,  # TODO: Get from ConversationLog
        )

    async def get_artifact_summaries(
        self,
        limit: Optional[int] = None,
    ) -> list[ArtifactSummary]:
        """Get artifact summaries for the current scope.

        Args:
            limit: Max number of artifacts (default from config)

        Returns:
            List of ArtifactSummary objects
        """
        limit = limit or self.config.artifact_limit

        # Query for Artifacts in this scope
        response = await self.semantic.query_async(
            type="Artifact",
            filters={"scope_uuid": self.config.scope_uuid},
            count=limit,
        )

        if not response.ok:
            raise ValueError(f"Failed to query artifacts: {response.error}")

        artifacts = response.result.get("results", [])

        summaries = []
        for artifact in artifacts:
            content = artifact.get("data", {}).get("content", "")
            lines = content.split("\n") if content else []

            summaries.append(
                ArtifactSummary(
                    uuid=artifact.get("uuid", ""),
                    label=artifact.get("data", {}).get("label", "Untitled"),
                    content_type=artifact.get("data", {}).get("content_type", "text/plain"),
                    preview=content[:100] if content else "",
                    line_count=len(lines),
                    updated_at=artifact.get("updated_at", ""),
                )
            )

        return summaries

    async def get_artifact_block(
        self,
        limit: Optional[int] = None,
    ) -> MemoGardenArtifactBlock:
        """Get artifact memory block.

        Args:
            limit: Max number of artifacts

        Returns:
            MemoGardenArtifactBlock with artifact summaries
        """
        artifacts = await self.get_artifact_summaries(limit)

        # Get total count
        response = await self.semantic.query_async(
            type="Artifact",
            filters={"scope_uuid": self.config.scope_uuid},
            count=1,  # We just need the total
        )

        total = response.result.get("total", len(artifacts))

        return MemoGardenArtifactBlock(
            artifacts=artifacts,
            total_count=total,
        )

    async def get_conversation_history(
        self,
        log_uuid: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[MessageSummary]:
        """Get recent conversation messages.

        Args:
            log_uuid: ConversationLog UUID (default: finds root log for scope)
            limit: Max number of messages

        Returns:
            List of MessageSummary objects
        """
        limit = limit or self.config.message_limit

        # TODO: Find root ConversationLog for scope
        # For now, return empty list
        return []

    async def get_conversation_block(
        self,
        log_uuid: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> MemoGardenConversationBlock:
        """Get conversation memory block.

        Args:
            log_uuid: ConversationLog UUID
            limit: Max number of messages

        Returns:
            MemoGardenConversationBlock with message summaries
        """
        messages = await self.get_conversation_history(log_uuid, limit)

        return MemoGardenConversationBlock(
            log_uuid=log_uuid or self.config.scope_uuid,
            messages=messages,
            total_count=len(messages),
        )

    async def get_context_frame(self) -> MemoGardenContextBlock:
        """Get context frame block for the agent.

        Returns:
            MemoGardenContextBlock with context frame state
        """
        if not self.config.participant_uuid:
            raise ValueError("participant_uuid required for context frame")

        # TODO: Query ContextFrame for participant
        # For now, return empty context
        return MemoGardenContextBlock(
            participant_uuid=self.config.participant_uuid,
            containers=[],
            head_item=None,
        )

    async def refresh_memory(self) -> list[dict[str, Any]]:
        """Refresh all memory blocks from MemoGarden state.

        This is the main entry point for updating agent memory.
        Call this periodically to keep memory in sync.

        Returns:
            List of Letta-compatible block dictionaries
        """
        # Get project context
        project = await self.get_project_context()

        # Get artifacts
        artifacts = await self.get_artifact_summaries()

        # Get conversation (if available)
        messages = await self.get_conversation_history()

        # Get context frame (if participant_uuid set)
        containers = None
        if self.config.participant_uuid:
            ctx = await self.get_context_frame()
            containers = ctx.containers

        # Create blocks
        return create_memogarden_blocks(
            scope_uuid=self.config.scope_uuid,
            project_label=project.label,
            participants=project.active_participants,
            artifact_summaries=artifacts,
            conversation_summaries=messages if messages else None,
            context_containers=containers,
            participant_uuid=self.config.participant_uuid,
        )

    def refresh_memory_sync(self) -> list[dict[str, Any]]:
        """Synchronous version of refresh_memory.

        Returns:
            List of Letta-compatible block dictionaries
        """
        return asyncio.run(self.refresh_memory())
