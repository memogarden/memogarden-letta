"""Tests for MemoGarden memory blocks."""

import pytest

from mgLetta.blocks import (
    MemoGardenProjectBlock,
    ArtifactSummary,
    MemoGardenArtifactBlock,
    MessageSummary,
    MemoGardenConversationBlock,
    MemoGardenContextBlock,
    create_memogarden_blocks,
)


class TestMemoGardenProjectBlock:
    """Test MemoGardenProjectBlock."""

    def test_to_letta_block(self):
        """Test conversion to Letta block format."""
        block = MemoGardenProjectBlock(
            scope_uuid="core_123",
            label="Test Project",
            active_participants=["usr_abc", "agt_def"],
            artifact_count=5,
            active_branches=2,
            root_summary="Initial discussion about requirements",
        )

        letta_block = block.to_letta_block()

        assert letta_block["label"] == "project_context"
        assert letta_block["read_only"] is True
        assert letta_block["limit"] == 2000
        assert "Test Project" in letta_block["value"]
        assert "core_123" in letta_block["value"]
        assert "Active Participants: 2" in letta_block["value"]
        assert "Artifacts: 5" in letta_block["value"]
        assert "Initial discussion" in letta_block["value"]

    def test_to_letta_block_without_summary(self):
        """Test conversion without root summary."""
        block = MemoGardenProjectBlock(
            scope_uuid="core_123",
            label="Test Project",
            active_participants=[],
            artifact_count=0,
            active_branches=1,
            root_summary=None,
        )

        letta_block = block.to_letta_block()

        assert letta_block["value"] is not None
        assert "Root Summary:" not in letta_block["value"]


class TestArtifactSummary:
    """Test ArtifactSummary."""

    def test_artifact_summary(self):
        """Test ArtifactSummary dataclass."""
        summary = ArtifactSummary(
            uuid="art_123",
            label="README.md",
            content_type="text/markdown",
            preview="# Project Title\n\nThis is a project...",
            line_count=42,
            updated_at="2026-02-15T10:00:00Z",
        )

        assert summary.uuid == "art_123"
        assert summary.label == "README.md"
        assert summary.line_count == 42


class TestMemoGardenArtifactBlock:
    """Test MemoGardenArtifactBlock."""

    def test_to_letta_block(self):
        """Test conversion to Letta block format."""
        artifacts = [
            ArtifactSummary(
                uuid="art_001",
                label="README.md",
                content_type="text/markdown",
                preview="# Introduction",
                line_count=50,
                updated_at="2026-02-15T10:00:00Z",
            ),
            ArtifactSummary(
                uuid="art_002",
                label="main.py",
                content_type="text/x-python",
                preview="def main():",
                line_count=100,
                updated_at="2026-02-15T11:00:00Z",
            ),
        ]

        block = MemoGardenArtifactBlock(
            artifacts=artifacts,
            total_count=10,
        )

        letta_block = block.to_letta_block()

        assert letta_block["label"] == "artifacts"
        assert letta_block["read_only"] is True
        assert letta_block["limit"] == 3000
        assert "(10 total, showing 2)" in letta_block["value"]
        assert "README.md" in letta_block["value"]
        assert "main.py" in letta_block["value"]
        assert "Lines: 50" in letta_block["value"]


class TestMemoGardenConversationBlock:
    """Test MemoGardenConversationBlock."""

    def test_to_letta_block(self):
        """Test conversion to Letta block format."""
        messages = [
            MessageSummary(
                uuid="msg_001",
                sender="operator",
                content="Let's add a new feature",
                fragments=["^abc"],
                timestamp="2026-02-15T10:00:00Z",
            ),
            MessageSummary(
                uuid="msg_002",
                sender="agent",
                content="I'll help implement that feature",
                fragments=[],
                timestamp="2026-02-15T10:05:00Z",
            ),
        ]

        block = MemoGardenConversationBlock(
            log_uuid="log_root",
            messages=messages,
            total_count=15,
        )

        letta_block = block.to_letta_block()

        assert letta_block["label"] == "conversation"
        assert letta_block["read_only"] is True
        assert "(15 total messages, showing 2)" in letta_block["value"]
        assert "[2026-02-15T10:00:00]" in letta_block["value"]
        assert "Operator:" in letta_block["value"]
        assert "Agent:" in letta_block["value"]


class TestMemoGardenContextBlock:
    """Test MemoGardenContextBlock."""

    def test_to_letta_block(self):
        """Test conversion to Letta block format."""
        block = MemoGardenContextBlock(
            participant_uuid="agt_123",
            containers=["core_456", "art_789"],
            head_item="msg_abc",
        )

        letta_block = block.to_letta_block()

        assert letta_block["label"] == "context_frame"
        assert letta_block["read_only"] is True
        assert "agt_123" in letta_block["value"]
        assert "core_456" in letta_block["value"]
        assert "art_789" in letta_block["value"]
        assert "msg_abc" in letta_block["value"]

    def test_to_letta_block_empty_containers(self):
        """Test conversion with no containers."""
        block = MemoGardenContextBlock(
            participant_uuid="agt_123",
            containers=[],
            head_item=None,
        )

        letta_block = block.to_letta_block()

        assert "No active containers" in letta_block["value"]


class TestCreateMemoGardenBlocks:
    """Test create_memogarden_blocks function."""

    def test_create_blocks_minimal(self):
        """Test creating blocks with minimal parameters."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test Project",
            participants=["usr_abc"],
        )

        assert len(blocks) == 1
        assert blocks[0]["label"] == "project_context"
        assert "Test Project" in blocks[0]["value"]

    def test_create_blocks_with_artifacts(self):
        """Test creating blocks with artifacts."""
        artifacts = [
            ArtifactSummary(
                uuid="art_001",
                label="README.md",
                content_type="text/markdown",
                preview="Hello",
                line_count=10,
                updated_at="2026-02-15T10:00:00Z",
            )
        ]

        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=[],
            artifact_summaries=artifacts,
        )

        assert len(blocks) == 2
        assert blocks[0]["label"] == "project_context"
        assert blocks[1]["label"] == "artifacts"

    def test_create_blocks_full(self):
        """Test creating all block types."""
        artifacts = [
            ArtifactSummary(
                uuid="art_001",
                label="README.md",
                content_type="text/markdown",
                preview="Hello",
                line_count=10,
                updated_at="2026-02-15T10:00:00Z",
            )
        ]
        messages = [
            MessageSummary(
                uuid="msg_001",
                sender="operator",
                content="Hello",
                fragments=[],
                timestamp="2026-02-15T10:00:00Z",
            )
        ]

        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
            artifact_summaries=artifacts,
            conversation_summaries=messages,
            context_containers=["core_456"],
            participant_uuid="agt_123",
        )

        assert len(blocks) == 4
        labels = [b["label"] for b in blocks]
        assert "project_context" in labels
        assert "artifacts" in labels
        assert "conversation" in labels
        assert "context_frame" in labels
