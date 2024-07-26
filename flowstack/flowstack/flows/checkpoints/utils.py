"""
Credit to LangGraph -
https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/base.py
https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/manager.py
"""

from datetime import datetime, timezone
from typing import Any, Mapping, Optional, TYPE_CHECKING

from uuid6 import uuid6

from flowstack.flows.checkpoints import Checkpoint
from flowstack.flows.errors import EmptyChannelError

if TYPE_CHECKING:
    from flowstack.flows.channels.base import Channel

def empty_checkpoint() -> Checkpoint:
    return Checkpoint(
        version=1,
        id=str(uuid6(clock_seq=-2)),
        timestamp=datetime.now(timezone.utc).isoformat(),
        channel_values={},
        channels_versions={},
        versions_seen={},
        pending_sends=[],
        current_tasks={}
    )

def copy_checkpoint(checkpoint: Checkpoint) -> Checkpoint:
    return Checkpoint(
        version=checkpoint['version'],
        id=checkpoint['id'],
        timestamp=checkpoint['timestamp'],
        channel_values=checkpoint['channel_values'].copy(),
        channels_versions=checkpoint['channels_versions'].copy(),
        versions_seen={node: versions.copy() for node, versions in checkpoint['versions_seen'].items()},
        pending_sends=checkpoint.get('pending_sends', []),
        current_tasks=checkpoint.get('current_tasks', {})
    )

def create_checkpoint(
    checkpoint: Checkpoint,
    channels: Mapping[str, 'Channel'],
    step: int,
    *,
    id: Optional[str] = None
) -> Checkpoint:
    timestamp = datetime.now(timezone.utc).isoformat()
    values: dict[str, Any] = {}
    for name, channel in channels.items():
        try:
            values[name] = channel.checkpoint()
        except EmptyChannelError:
            pass
    return Checkpoint(
        version=1,
        timestamp=timestamp,
        id=id or str(uuid6(clock_seq=step)),
        channel_values=values,
        channels_versions=checkpoint['channels_versions'],
        versions_seen=checkpoint['versions_seen'],
        pending_sends=checkpoint.get('pending_sends', []),
        current_tasks={}
    )