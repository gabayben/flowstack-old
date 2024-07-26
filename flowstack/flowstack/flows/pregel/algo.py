"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/algo.py
"""

from typing import Any, Callable, Mapping, NamedTuple, Optional, Protocol, Sequence, Union

from flowstack.flows import All, Channel, ChannelManager, Checkpoint, ContextValue, PregelExecutableTask
from flowstack.flows.channels.utils import read_channels
from flowstack.flows.checkpoints.utils import copy_checkpoint, create_checkpoint
from flowstack.flows.constants import HIDDEN, INTERRUPT

class WritesProtocol(Protocol):
    name: str
    writes: Sequence[tuple[str, Any]]
    triggers: Sequence[str]

class PregelTaskWrites(NamedTuple):
    name: str
    writes: Sequence[tuple[str, Any]]
    triggers: Sequence[str]

def should_interrupt(
    checkpoint: Checkpoint,
    interrupt_nodes: Union[All, Sequence[str]],
    tasks: list[PregelExecutableTask]
) -> bool:
    version_type = type(next(iter(checkpoint['channels_versions'].values()), None))
    null_version = version_type()
    seen = checkpoint['versions_seen'].get(INTERRUPT, {})
    return (
        # interrupt if any channel has been updated since last interrupt
        any(
            version > seen.get(chan, null_version)
            for chan, version in checkpoint['channels_versions'].items()
        ) and
        # and any triggered node is in interrupt_nodes list
        any(
            task
            for task in tasks
            if (
                (not task.config or HIDDEN not in task.config.get('tags', []))
                if interrupt_nodes == '*'
                else task.name in interrupt_nodes
            )
        )
    )

def apply_writes(
    checkpoint: Checkpoint,
    channels: Mapping[str, Channel],
    tasks: Sequence[WritesProtocol],
    get_next_version: Optional[Callable[[int, Channel], int]] = None
) -> None:
    pass

def local_read(
    checkpoint: Checkpoint,
    channels: Mapping[str, Channel],
    task: WritesProtocol,
    select: Union[str, Sequence[str]],
    fresh: bool = False,
    **config
) -> Union[Any, dict[str, Any]]:
    if fresh:
        new_checkpoint = create_checkpoint(copy_checkpoint(checkpoint), channels, -1)
        context_channels = {name: channel for name, channel in channels.items() if isinstance(channel, ContextValue)}
        with ChannelManager(
            {name: channel for name, channel in channels.items() if name not in context_channels},
            new_checkpoint,
            **config
        ) as channels:
            all_channels = {**channels, **context_channels}
            apply_writes(new_checkpoint, all_channels, [task])
            return read_channels(all_channels, select)
    return read_channels(channels, select)