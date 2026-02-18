"""Tests for Letta integration.

These tests verify that MemoGarden memory blocks are compatible
with the Letta Block schema and can be used to create agents.

Requires letta-client to be installed. Install with:
    poetry install --with dev

Level 3 tests require LETTA_API_KEY environment variable.
"""

import json
import os

import pytest
from letta_client import Block

from mgLetta.blocks import (
    ArtifactSummary,
    MemoGardenArtifactBlock,
    MemoGardenContextBlock,
    MemoGardenConversationBlock,
    MemoGardenProjectBlock,
    MessageSummary,
    create_memogarden_blocks,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_artifacts():
    """Sample artifact summaries for testing."""
    return [
        ArtifactSummary(
            uuid="art_001",
            label="README.md",
            content_type="text/markdown",
            preview="# Introduction",
            line_count=50,
            updated_at="2026-02-15T10:00:00Z",
        ),
    ]


@pytest.fixture
def sample_messages():
    """Sample message summaries for testing."""
    return [
        MessageSummary(
            uuid="msg_001",
            sender="operator",
            content="Let's add a new feature",
            fragments=["^abc"],
            timestamp="2026-02-15T10:00:00Z",
        ),
    ]


@pytest.fixture
def minimal_artifacts():
    """Minimal artifact summaries for testing."""
    return [
        ArtifactSummary(
            uuid="art_001",
            label="README.md",
            content_type="text/markdown",
            preview="Hello",
            line_count=10,
            updated_at="2026-02-15T10:00:00Z",
        )
    ]


@pytest.fixture
def minimal_messages():
    """Minimal message summaries for testing."""
    return [
        MessageSummary(
            uuid="msg_001",
            sender="operator",
            content="Hello",
            fragments=[],
            timestamp="2026-02-15T10:00:00Z",
        )
    ]


# =============================================================================
# Level 1: Schema Validation Tests
# =============================================================================


class TestBlockSchemaCompatibility:
    """Test that MemoGarden blocks produce valid Letta Block schemas."""

    def test_project_block_valid_letta_schema(self):
        """MemoGardenProjectBlock.to_letta_block() produces valid Letta Block."""
        block = MemoGardenProjectBlock(
            scope_uuid="core_123",
            label="Test Project",
            active_participants=["usr_abc", "agt_def"],
            artifact_count=5,
            active_branches=2,
            root_summary="Initial discussion about requirements",
        )

        block_dict = block.to_letta_block()

        # Must not raise ValidationError
        letta_block = Block(**block_dict)

        # Verify the block was created successfully
        assert letta_block.label == "project_context"
        assert letta_block.read_only is True
        assert "Test Project" in letta_block.value

    def test_artifact_block_valid_letta_schema(self, sample_artifacts):
        """MemoGardenArtifactBlock produces valid Letta Block."""
        block = MemoGardenArtifactBlock(artifacts=sample_artifacts, total_count=10)
        block_dict = block.to_letta_block()

        # Must not raise ValidationError
        letta_block = Block(**block_dict)

        assert letta_block.label == "artifacts"
        assert letta_block.read_only is True
        assert "README.md" in letta_block.value

    def test_conversation_block_valid_letta_schema(self, sample_messages):
        """MemoGardenConversationBlock produces valid Letta Block."""
        block = MemoGardenConversationBlock(
            log_uuid="log_root",
            messages=sample_messages,
            total_count=15,
        )
        block_dict = block.to_letta_block()

        # Must not raise ValidationError
        letta_block = Block(**block_dict)

        assert letta_block.label == "conversation"
        assert letta_block.read_only is True
        assert "operator" in letta_block.value.lower()

    def test_context_block_valid_letta_schema(self):
        """MemoGardenContextBlock produces valid Letta Block."""
        block = MemoGardenContextBlock(
            participant_uuid="agt_123",
            containers=["core_456", "art_789"],
            head_item="msg_abc",
        )
        block_dict = block.to_letta_block()

        # Must not raise ValidationError
        letta_block = Block(**block_dict)

        assert letta_block.label == "context_frame"
        assert letta_block.read_only is True
        assert "agt_123" in letta_block.value

    def test_create_memogarden_blocks_valid_letta_schemas(
        self, minimal_artifacts, minimal_messages
    ):
        """All blocks from create_memogarden_blocks are valid Letta Blocks."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
            artifact_summaries=minimal_artifacts,
            conversation_summaries=minimal_messages,
            context_containers=["core_456"],
            participant_uuid="agt_123",
        )

        # All blocks should be convertible to Letta Blocks without error
        letta_blocks = [Block(**b) for b in blocks]

        assert len(letta_blocks) == 4
        labels = [b.label for b in letta_blocks]
        assert "project_context" in labels
        assert "artifacts" in labels
        assert "conversation" in labels
        assert "context_frame" in labels


# =============================================================================
# Level 2: Block Content Invariants
# =============================================================================


class TestBlockContentInvariants:
    """Test invariants about block content structure."""

    def test_all_blocks_have_required_fields(self):
        """Every Letta-compatible block has required fields."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
        )

        for block_dict in blocks:
            # Required by Letta Block schema
            assert "value" in block_dict
            assert isinstance(block_dict["value"], str)

            # Optional but we always set them
            assert "label" in block_dict
            assert "read_only" in block_dict

    def test_all_blocks_marked_read_only(self):
        """All MemoGarden blocks are marked read-only."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
        )

        for block_dict in blocks:
            assert block_dict.get("read_only") is True

    def test_all_blocks_have_metadata_block_type(self):
        """All blocks have block_type in metadata for identification."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
        )

        for block_dict in blocks:
            assert "metadata" in block_dict
            assert "block_type" in block_dict["metadata"]
            # block_type should start with "memogarden_"
            assert block_dict["metadata"]["block_type"].startswith("memogarden_")

    def test_all_blocks_have_unique_labels(self, minimal_artifacts, minimal_messages):
        """No duplicate labels in block list (Letta requirement)."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
            artifact_summaries=minimal_artifacts,
            conversation_summaries=minimal_messages,
            context_containers=["core_456"],
            participant_uuid="agt_123",
        )

        labels = [b["label"] for b in blocks]
        assert len(labels) == len(set(labels)), f"Duplicate labels found: {labels}"

    def test_blocks_are_json_serializable(self):
        """Blocks can be serialized to JSON for API requests."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
        )

        # Should not raise TypeError
        json_str = json.dumps(blocks)
        assert isinstance(json_str, str)

        # Should deserialize correctly
        deserialized = json.loads(json_str)
        assert len(deserialized) == len(blocks)

    def test_all_blocks_have_description(self):
        """All blocks have a description field for UX."""
        blocks = create_memogarden_blocks(
            scope_uuid="core_123",
            project_label="Test",
            participants=["usr_abc"],
        )

        for block_dict in blocks:
            assert "description" in block_dict
            assert isinstance(block_dict["description"], str)
            assert len(block_dict["description"]) > 0


# =============================================================================
# Level 3: Live API Tests (requires LETTA_API_KEY)
# =============================================================================


@pytest.mark.skipif(
    not os.getenv("LETTA_API_KEY"),
    reason="LETTA_API_KEY not set - set environment variable to run live API tests",
)
class TestLettaAPI:
    """Live tests against Letta API.

    To run these tests:
        export LETTA_API_KEY="your-api-key"
        pytest tests/test_letta_integration.py::TestLettaAPI -v
    """

    @pytest.mark.asyncio
    async def test_create_agent_with_memogarden_blocks(self):
        """Create a Letta agent with MemoGarden memory blocks."""
        from letta_client import LettaClient

        client = LettaClient(
            base_url=os.getenv("LETTA_API_URL", "https://api.letta.com"),
            token=os.getenv("LETTA_API_KEY"),
        )

        # Create MemoGarden blocks
        blocks = create_memogarden_blocks(
            scope_uuid="core_test_123",
            project_label="Test Project",
            participants=["usr_test"],
        )

        # Convert to Letta Blocks
        letta_blocks = [Block(**b) for b in blocks]

        # Verify blocks can be created via API
        created_blocks = []
        for block in letta_blocks:
            created = client.create_block(block)
            created_blocks.append(created)
            assert created.id is not None
            assert created.label == block.label

        # Cleanup
        for block in created_blocks:
            try:
                client.delete_block(block.id)
            except Exception as e:
                # Best effort cleanup - don't fail test if cleanup fails
                print(f"Warning: Failed to cleanup block {block.id}: {e}")

    @pytest.mark.asyncio
    async def test_block_persistence_and_retrieval(self):
        """Blocks can be created and retrieved from the API."""
        from letta_client import LettaClient

        client = LettaClient(
            base_url=os.getenv("LETTA_API_URL", "https://api.letta.com"),
            token=os.getenv("LETTA_API_KEY"),
        )

        # Create a project block
        project_block = MemoGardenProjectBlock(
            scope_uuid="core_persist_123",
            label="Persistence Test Project",
            active_participants=["usr_test"],
            artifact_count=3,
            active_branches=1,
        )

        letta_block = Block(**project_block.to_letta_block())
        created = client.create_block(letta_block)

        try:
            # Retrieve by ID
            retrieved = client.get_block(created.id)
            assert retrieved.id == created.id
            assert retrieved.label == "project_context"
            assert retrieved.value == created.value
            assert retrieved.read_only is True
        finally:
            # Cleanup
            try:
                client.delete_block(created.id)
            except Exception as e:
                # Best effort cleanup
                print(f"Warning: Failed to cleanup block {created.id}: {e}")
