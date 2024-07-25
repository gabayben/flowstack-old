from datetime import datetime, timezone
from typing import Mapping, Optional, TYPE_CHECKING

from uuid6 import uuid6

from flowstack.flows import Checkpoint

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
    pass