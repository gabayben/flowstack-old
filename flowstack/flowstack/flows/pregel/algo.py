"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/algo.py
"""

from collections import defaultdict, deque
from functools import partial
import json
import logging
from typing import Any, Callable, Iterator, Literal, Mapping, NamedTuple, Optional, Protocol, Sequence, Union, overload
from uuid import UUID, uuid5

from flowstack.flows import (
    All,
    Channel,
    ChannelManager,
    ChannelVersion, Checkpoint,
    Checkpointer, ContextValue,
    EmptyChannelError, InvalidUpdateError,
    PregelExecutableTask, PregelNode, PregelTaskDescription, PregelTaskMetadata, Send
)
from flowstack.flows.channels.utils import read_channel, read_channels
from flowstack.flows.checkpoints.utils import copy_checkpoint, create_checkpoint
from flowstack.flows.constants import HIDDEN, INTERRUPT, READ_KEY, RESERVED, TASKS, WRITE_KEY
from flowstack.flows.managed.base import ManagedValue, is_managed_value

logger = logging.getLogger(__name__)

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
    null_version = _get_null_version(checkpoint)
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

def increment(current: Optional[int], channel: Channel) -> int:
    raise current + 1 if current is not None else 1

def apply_writes(
    checkpoint: Checkpoint,
    channels: Mapping[str, Channel],
    tasks: Sequence[WritesProtocol],
    get_next_version: Optional[Callable[[int, Channel], int]] = None
) -> None:
    # update seen versions
    for task in tasks:
        checkpoint['versions_seen'].setdefault(task.name, {}).update({
            chan: checkpoint['channels_versions'][chan]
            for chan in task.triggers
            if chan in checkpoint['channels_versions']
        })

    max_version = _get_max_version(checkpoint)

    # consume all channels that were read
    for chan in {
        chan for task in tasks for chan in task.triggers if chan not in RESERVED
    }:
        if channels[chan].consume():
            if get_next_version is not None:
                checkpoint['channels_versions'][chan] = get_next_version(max_version, channels[chan])

    # clear pending sends
    if checkpoint['pending_sends']:
        checkpoint['pending_sends'].clear()

    # group writes by channel
    pending_writes_by_channel: dict[str, list[Any]] = defaultdict(list)
    for task in tasks:
        for chan, value in task.writes:
            if chan == TASKS:
                checkpoint['pending_sends'].append(value)
            else:
                pending_writes_by_channel[chan].append(value)

    max_version = _get_max_version(checkpoint)

    # apply writes to channels
    updated_channels: set[str] = set()
    for chan, values in pending_writes_by_channel.items():
        if chan in channels:
            try:
                updated = channels[chan].update(values)
            except InvalidUpdateError as e:
                raise InvalidUpdateError(
                    f'Invalid update for channel {chan} with values {values}'
                ) from e
            if updated and get_next_version is not None:
                checkpoint['channels_versions'][chan] = get_next_version(max_version, channels[chan])
            updated_channels.add(chan)

    # channels that weren't updated in this step are notified of a new step
    for chan in channels:
        if chan not in updated_channels:
            if channels[chan].update([]) and get_next_version is not None:
                checkpoint['channels_versions'][chan] = get_next_version(max_version, channels[chan])

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

def local_write(
    commit: Callable[[Sequence[tuple[str, Any]]], None],
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    writes: Sequence[tuple[str, Any]]
) -> None:
    for chan, value in writes:
        if chan == TASKS:
            if not isinstance(value, Send):
                raise InvalidUpdateError(
                    f'Invalid packet type, expected Send, got {value}.'
                )
            if value.node not in processes:
                raise InvalidUpdateError(f'Invalid node name {value.node} in packet.')
        elif chan not in channels:
            logger.warning(f'Skipping write for channel {chan} which has no readers.')
    commit(writes)

@overload
def prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    managed: dict[str, ManagedValue],
    step: int,
    for_execution: Literal[False],
    is_resuming: bool = False,
    checkpointer: Literal[None] = None,
    **config
) -> list[PregelTaskDescription]: ...

@overload
def prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    managed: dict[str, ManagedValue],
    step: int,
    for_execution: Literal[True],
    is_resuming: bool,
    checkpointer: Optional[Checkpointer],
    **config
) -> list[PregelExecutableTask]: ...

def prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    managed: dict[str, ManagedValue],
    step: int,
    for_execution: bool,
    is_resuming: bool = False,
    checkpointer: Optional[Checkpointer] = None,
    **config
) -> Union[list[PregelTaskDescription], list[PregelExecutableTask]]:
    tasks: list[Union[PregelTaskDescription, PregelExecutableTask]] = []
    config.pop('fresh', None)

    # consume pending packets
    for packet in checkpoint['pending_sends']:
        if not isinstance(packet, Send):
            logger.warning(f'Ignoring invalid packet type {type(packet)} in pending sends.')
            continue
        if packet.node not in processes:
            logger.warning(f'Ignoring unknown packet node {packet.node} in pending sends.')
            continue

        if for_execution:
            process = processes[packet.node]
            if node := process.get_node():
                triggers = [TASKS]
                metadata = PregelTaskMetadata(
                    step=step,
                    node=packet.node,
                    triggers=triggers,
                    task_idx=len(tasks)
                )
                task_id = _get_task_id(checkpoint['id'], metadata)
                writes = deque()
                tasks.append(PregelExecutableTask(
                    name=packet.node,
                    input=packet.arg,
                    process=node,
                    writes=writes,
                    triggers=triggers,
                    id=task_id,
                    metadata=metadata,
                    config={
                        **config,
                        **processes[packet.node].kwargs,
                        WRITE_KEY: partial(
                            local_write,
                            writes.extend,
                            processes,
                            channels
                        ),
                        READ_KEY: partial(
                            local_read,
                            checkpoint,
                            channels,
                            PregelTaskWrites(packet.node, writes, triggers),
                            **config
                        )
                    }
                ))
        else:
            tasks.append(PregelTaskDescription(packet.node, packet.arg))

    # Check if any processes should be run in next step
    # If so, prepare the values to be passed to them
    null_version = _get_null_version(checkpoint)
    if null_version is None:
        return tasks
    for name, process in processes.items():
        seen = checkpoint['versions_seen'].get(name, {})
        # If any of the channels read by this process were updated
        if triggers := sorted(
            chan
            for chan in process.triggers
            if (
                not isinstance(
                    read_channel(channels, chan, return_exception=True), EmptyChannelError
                ) and
                checkpoint['channels_versions'].get(chan, null_version) > seen.get(chan, null_version)
            )
        ):
            try:
                value = next(_process_input(step, name, process, channels, managed))
            except StopIteration:
                continue

            if for_execution:
                if node := process.get_node():
                    metadata = PregelTaskMetadata(
                        step=step,
                        node=name,
                        triggers=triggers,
                        task_idx=len(tasks)
                    )
                    task_id = _get_task_id(checkpoint['id'], metadata)
                    if parent_thread_id := config.get('thread_id'):
                        thread_id = f'{parent_thread_id}-{name}'
                    else:
                        thread_id = None
                    writes = deque()
                    tasks.append(PregelExecutableTask(
                        name=name,
                        input=value,
                        process=node,
                        writes=writes,
                        triggers=triggers,
                        id=task_id,
                        metadata=metadata,
                        retry_policy=process.retry_policy,
                        checkpointer=checkpointer,
                        is_resuming=is_resuming,
                        config={
                            **config,
                            **process.kwargs,
                            WRITE_KEY: partial(
                                local_write,
                                writes.extend,
                                processes,
                                channels,
                                writes
                            ),
                            READ_KEY: partial(
                                local_read,
                                checkpoint,
                                channels,
                                PregelTaskWrites(name, writes, triggers),
                                **config
                            ),
                            'thread_id': thread_id,
                            'thread_ts': checkpoint['id']
                        }
                    ))
            else:
                tasks.append(PregelTaskDescription(name, value))

    return tasks

def _process_input(
    step: int,
    name: str,
    process: PregelNode,
    channels: Mapping[str, Channel],
    managed: dict[str, ManagedValue]
) -> Iterator[Any]:
    # If all trigger channels subscribed by this process are not empty
    # then invoke the process with the values of all non-empty channels
    if isinstance(process.channels, dict):
        try:
            value = {
                key: read_channel(channels, chan, catch=chan not in process.triggers)
                for key, chan in process.channels.items()
                if isinstance(chan, str)
            }
            managed_values = {}
            for key, chan in process.channels.items():
                if is_managed_value(chan):
                    managed_values[key] = chan(step, PregelTaskDescription(name, value))
            value.update(managed_values)
        except EmptyChannelError:
            return
    elif isinstance(process.channels, list):
        for chan in process.channels:
            try:
                value = read_channel(channels, chan, catch=False)
            except EmptyChannelError:
                pass
        else:
            return
    else:
        raise RuntimeError(
            f'Invalid channels type for process. Expected list or dict, got {process.channels}.'
        )

    if process.mapper is not None:
        value = process.mapper(value)

    yield value

def _get_max_version(checkpoint: Checkpoint) -> Optional[ChannelVersion]:
    if checkpoint['channels_versions']:
        return max(checkpoint['channels_versions'].values())
    return None

def _get_null_version(checkpoint: Checkpoint) -> Any:
    version_type = type(next(iter(checkpoint['channels_versions'].values()), None))
    return version_type()

def _get_task_id(id: str, metadata: dict) -> str:
    return str(uuid5(UUID(id), json.dumps(metadata)))