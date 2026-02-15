"""MemoGarden memory blocks for Letta agents.

This module defines custom memory block types that project MemoGarden state
into Letta-compatible memory blocks.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class MemoGardenProjectBlock:
    """Project context block - contains information about the current Scope/project.

    This block is read-only and updated by the memory projection system,
    not by the agent directly.

    Attributes:
        scope_uuid: UUID of the current Scope
        label: Human-readable project name
        active_participants: List of participant UUIDs in the scope
        artifact_count: Number of artifacts in the scope
        active_branches: Number of active conversation branches
        root_summary: Summary of the root conversation (if collapsed)
    """

    scope_uuid: str
    label: str
    active_participants: list[str]
    artifact_count: int
    active_branches: int
    root_summary: Optional[str] = None

    def to_letta_block(self) -> dict[str, Any]:
        """Convert to Letta Block format.

        Returns a dictionary compatible with Letta's CreateBlock schema.
        """
        value = f"""Project: {self.label}
Scope UUID: {self.scope_uuid}
Active Participants: {len(self.active_participants)}
Artifacts: {self.artifact_count}
Active Branches: {self.active_branches}"""

        if self.root_summary:
            value += f"\n\nRoot Summary:\n{self.root_summary}"

        return {
            "label": "project_context",
            "value": value,
            "description": "MemoGarden project/scope context (read-only)",
            "read_only": True,
            "limit": 2000,
            "metadata": {
                "scope_uuid": self.scope_uuid,
                "block_type": "memogarden_project",
            },
        }


@dataclass
class ArtifactSummary:
    """Summary of a single artifact."""

    uuid: str
    label: str
    content_type: str
    preview: str  # First ~100 chars
    line_count: int
    updated_at: str


@dataclass
class MemoGardenArtifactBlock:
    """Artifact block - contains recent artifact summaries.

    Provides the agent with context about artifacts in the current scope.
    Updated by the memory projection system.

    Attributes:
        artifacts: List of artifact summaries (most recent first)
        total_count: Total number of artifacts (may exceed displayed)
    """

    artifacts: list[ArtifactSummary]
    total_count: int

    def to_letta_block(self) -> dict[str, Any]:
        """Convert to Letta Block format."""
        lines = [f"Artifacts in scope ({self.total_count} total, showing {len(self.artifacts)}):"]

        for i, artifact in enumerate(self.artifacts, 1):
            lines.append(
                f"\n{i}. {artifact.label} ({artifact.content_type})"
                f"\n   UUID: {artifact.uuid}"
                f"\n   Lines: {artifact.line_count}"
            )
            if artifact.preview:
                preview = artifact.preview[:80] + "..." if len(artifact.preview) > 80 else artifact.preview
                lines.append(f"   Preview: {preview}")

        return {
            "label": "artifacts",
            "value": "\n".join(lines),
            "description": "Recent artifacts in the current scope (read-only)",
            "read_only": True,
            "limit": 3000,
            "metadata": {
                "block_type": "memogarden_artifacts",
                "total_count": self.total_count,
            },
        }


@dataclass
class MessageSummary:
    """Summary of a single conversation message."""

    uuid: str
    sender: str  # "operator", "agent", or "system"
    content: str
    fragments: list[str]  # Fragment IDs mentioned
    timestamp: str


@dataclass
class MemoGardenConversationBlock:
    """Conversation block - contains recent message history.

    Provides the agent with context about recent conversation activity.
    Updated by the memory projection system.

    Attributes:
        log_uuid: UUID of the ConversationLog
        messages: List of recent messages (most recent last)
        total_count: Total number of messages in the log
    """

    log_uuid: str
    messages: list[MessageSummary]
    total_count: int

    def to_letta_block(self) -> dict[str, Any]:
        """Convert to Letta Block format."""
        lines = [f"Recent conversation ({self.total_count} total messages, showing {len(self.messages)}):"]

        for msg in self.messages:
            sender_label = msg.sender.capitalize()
            timestamp = msg.timestamp[:19] if len(msg.timestamp) > 19 else msg.timestamp
            lines.append(f"\n[{timestamp}] {sender_label}:")

            if msg.fragments:
                lines.append(f"  Fragments: {', '.join(msg.fragments)}")

            # Truncate long messages
            content = msg.content
            if len(content) > 200:
                content = content[:197] + "..."
            lines.append(f"  {content}")

        return {
            "label": "conversation",
            "value": "\n".join(lines),
            "description": "Recent conversation history (read-only)",
            "read_only": True,
            "limit": 4000,
            "metadata": {
                "block_type": "memogarden_conversation",
                "log_uuid": self.log_uuid,
                "total_count": self.total_count,
            },
        }


@dataclass
class MemoGardenContextBlock:
    """ContextFrame block - contains active context containers.

    Provides the agent with information about its current context frame
    per RFC-003. Updated by the memory projection system.

    Attributes:
        participant_uuid: UUID of the agent/participant
        containers: List of active container UUIDs or descriptions
        head_item: Current head item UUID (if any)
    """

    participant_uuid: str
    containers: list[str]
    head_item: Optional[str] = None

    def to_letta_block(self) -> dict[str, Any]:
        """Convert to Letta Block format."""
        lines = ["Active Context (RFC-003):"]
        lines.append(f"Participant UUID: {self.participant_uuid}")

        if self.containers:
            lines.append(f"\nActive Containers ({len(self.containers)}):")
            for i, container in enumerate(self.containers, 1):
                lines.append(f"  {i}. {container}")
        else:
            lines.append("\nNo active containers")

        if self.head_item:
            lines.append(f"\nCurrent Head Item: {self.head_item}")

        return {
            "label": "context_frame",
            "value": "\n".join(lines),
            "description": "RFC-003 ContextFrame state (read-only)",
            "read_only": True,
            "limit": 1500,
            "metadata": {
                "block_type": "memogarden_context",
                "participant_uuid": self.participant_uuid,
            },
        }


def create_memogarden_blocks(
    scope_uuid: str,
    project_label: str,
    participants: list[str],
    artifact_summaries: list[ArtifactSummary] | None = None,
    conversation_summaries: list[MessageSummary] | None = None,
    context_containers: list[str] | None = None,
    participant_uuid: str | None = None,
) -> list[dict[str, Any]]:
    """Create a complete set of MemoGarden memory blocks.

    Args:
        scope_uuid: UUID of the current Scope
        project_label: Human-readable project name
        participants: List of active participant UUIDs
        artifact_summaries: Optional list of artifact summaries
        conversation_summaries: Optional list of message summaries
        context_containers: Optional list of context containers
        participant_uuid: Agent's participant UUID (for context block)

    Returns:
        List of Letta-compatible block dictionaries
    """
    blocks = []

    # Project context block (always included)
    project_block = MemoGardenProjectBlock(
        scope_uuid=scope_uuid,
        label=project_label,
        active_participants=participants,
        artifact_count=len(artifact_summaries) if artifact_summaries else 0,
        active_branches=1,  # TODO: Query actual branch count
        root_summary=None,
    )
    blocks.append(project_block.to_letta_block())

    # Artifacts block (if provided)
    if artifact_summaries:
        artifact_block = MemoGardenArtifactBlock(
            artifacts=artifact_summaries,
            total_count=len(artifact_summaries),
        )
        blocks.append(artifact_block.to_letta_block())

    # Conversation block (if provided)
    if conversation_summaries:
        conv_block = MemoGardenConversationBlock(
            log_uuid=scope_uuid,  # TODO: Get actual log UUID
            messages=conversation_summaries,
            total_count=len(conversation_summaries),
        )
        blocks.append(conv_block.to_letta_block())

    # Context frame block (if participant_uuid provided)
    if participant_uuid and context_containers is not None:
        context_block = MemoGardenContextBlock(
            participant_uuid=participant_uuid,
            containers=context_containers,
        )
        blocks.append(context_block.to_letta_block())

    return blocks
