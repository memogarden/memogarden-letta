"""Tests for MemoGardenMemoryClient.

Note: These tests require a running MemoGarden API server.
Use pytest fixtures to mock responses for unit testing.

These tests are skipped if mg_client is not available.
"""

import pytest

# Skip all tests in this module if mg_client is not available
pytest.importorskip("mg_client")

from unittest.mock import AsyncMock, MagicMock, patch

from mgLetta.client import MemoGardenMemoryClient, MemoGardenMemoryConfig
from mgLetta.blocks import ArtifactSummary, MessageSummary


class TestMemoGardenMemoryConfig:
    """Test MemoGardenMemoryConfig."""

    def test_config_creation(self):
        """Test creating config."""
        config = MemoGardenMemoryConfig(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
            participant_uuid="agt_456",
            artifact_limit=20,
            message_limit=100,
        )

        assert config.base_url == "http://localhost:5000"
        assert config.api_key == "mg_sk_test"
        assert config.scope_uuid == "core_123"
        assert config.artifact_limit == 20
        assert config.message_limit == 100


class TestMemoGardenMemoryClient:
    """Test MemoGardenMemoryClient."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        assert client.config.base_url == "http://localhost:5000"
        assert client.config.scope_uuid == "core_123"
        assert client._client is None  # Lazy loading

    @pytest.mark.asyncio
    async def test_get_project_context(self):
        """Test getting project context."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        # Mock the semantic API
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.result = {
            "uuid": "core_123",
            "data": {
                "label": "Test Project",
                "active_participants": ["usr_abc", "agt_def"],
                "artifact_uuids": ["art_001", "art_002"],
            },
        }

        with patch.object(client.semantic, "get_async", new=AsyncMock(return_value=mock_response)):
            project = await client.get_project_context()

        assert project.scope_uuid == "core_123"
        assert project.label == "Test Project"
        assert project.active_participants == ["usr_abc", "agt_def"]
        assert project.artifact_count == 2

    @pytest.mark.asyncio
    async def test_get_project_context_error(self):
        """Test error handling when getting project context."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.error = {"message": "Not found"}

        with patch.object(client.semantic, "get_async", new=AsyncMock(return_value=mock_response)):
            with pytest.raises(ValueError, match="Failed to get scope"):
                await client.get_project_context()

    @pytest.mark.asyncio
    async def test_get_artifact_summaries(self):
        """Test getting artifact summaries."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.result = {
            "results": [
                {
                    "uuid": "art_001",
                    "data": {
                        "label": "README.md",
                        "content_type": "text/markdown",
                        "content": "# Project\n\nLine 1\nLine 2\nLine 3",
                    },
                    "updated_at": "2026-02-15T10:00:00Z",
                },
                {
                    "uuid": "art_002",
                    "data": {
                        "label": "main.py",
                        "content_type": "text/x-python",
                        "content": "def main():\n    pass",
                    },
                    "updated_at": "2026-02-15T11:00:00Z",
                },
            ],
            "total": 2,
        }

        with patch.object(client.semantic, "query_async", new=AsyncMock(return_value=mock_response)):
            artifacts = await client.get_artifact_summaries()

        assert len(artifacts) == 2
        assert artifacts[0].uuid == "art_001"
        assert artifacts[0].label == "README.md"
        assert artifacts[0].line_count == 4
        assert artifacts[1].label == "main.py"

    @pytest.mark.asyncio
    async def test_get_artifact_summaries_empty(self):
        """Test getting artifact summaries when none exist."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.result = {"results": [], "total": 0}

        with patch.object(client.semantic, "query_async", new=AsyncMock(return_value=mock_response)):
            artifacts = await client.get_artifact_summaries()

        assert len(artifacts) == 0

    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """Test getting conversation history."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        # Currently returns empty list - will be implemented
        messages = await client.get_conversation_history()

        assert messages == []

    @pytest.mark.asyncio
    async def test_get_context_frame(self):
        """Test getting context frame."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
            participant_uuid="agt_456",
        )

        context = await client.get_context_frame()

        assert context.participant_uuid == "agt_456"
        assert context.containers == []

    @pytest.mark.asyncio
    async def test_get_context_frame_no_participant(self):
        """Test that context frame requires participant_uuid."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        with pytest.raises(ValueError, match="participant_uuid required"):
            await client.get_context_frame()

    @pytest.mark.asyncio
    async def test_refresh_memory(self):
        """Test refreshing all memory blocks."""
        client = MemoGardenMemoryClient(
            base_url="http://localhost:5000",
            api_key="mg_sk_test",
            scope_uuid="core_123",
        )

        # Mock project context
        mock_project_response = MagicMock()
        mock_project_response.ok = True
        mock_project_response.result = {
            "uuid": "core_123",
            "data": {
                "label": "Test Project",
                "active_participants": ["usr_abc"],
                "artifact_uuids": [],
            },
        }

        # Mock artifacts query
        mock_artifacts_response = MagicMock()
        mock_artifacts_response.ok = True
        mock_artifacts_response.result = {"results": [], "total": 0}

        with patch.object(client.semantic, "get_async", new=AsyncMock(return_value=mock_project_response)):
            with patch.object(client.semantic, "query_async", new=AsyncMock(return_value=mock_artifacts_response)):
                blocks = await client.refresh_memory()

        assert len(blocks) >= 1
        assert any(b["label"] == "project_context" for b in blocks)
