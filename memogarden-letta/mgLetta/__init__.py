"""MemoGarden-Letta: MemoGarden memory blocks for Letta agents.

This package provides memory projection functions that convert MemoGarden state
into Letta-compatible memory blocks, enabling agents to maintain context about
projects, artifacts, and conversations.

Example:
    from mgLetta import create_memogarden_agent

    agent = create_memogarden_agent(
        memogarden_url="http://localhost:5000",
        api_key="mg_sk_agent_...",
        scope_uuid="core_123",
        agent_name="ProjectAgent"
    )
"""

# Block imports (always available)
from mgLetta.blocks import (
    MemoGardenProjectBlock,
    MemoGardenArtifactBlock,
    MemoGardenConversationBlock,
    MemoGardenContextBlock,
)

# Optional imports that require mg_client
# Use importlib to check availability without triggering F401
import importlib.util
_has_client = importlib.util.find_spec("mg_client") is not None

if _has_client:
    from mgLetta.client import MemoGardenMemoryClient
    from mgLetta.agent import create_memogarden_agent, create_memogarden_blocks
    from mgLetta.tools import (
        memogarden_send_message,
        memogarden_commit_artifact,
        memogarden_create_artifact,
        memogarden_get_artifact,
        memogarden_search,
    )

__all__ = [
    # Blocks (always available)
    "MemoGardenProjectBlock",
    "MemoGardenArtifactBlock",
    "MemoGardenConversationBlock",
    "MemoGardenContextBlock",
]

# Add client-dependent exports if available
if _has_client:
    __all__.extend([
        "MemoGardenMemoryClient",
        "create_memogarden_agent",
        "create_memogarden_blocks",
        "memogarden_send_message",
        "memogarden_commit_artifact",
        "memogarden_create_artifact",
        "memogarden_get_artifact",
        "memogarden_search",
    ])

__version__ = "0.1.0"
