"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/io.py
"""

from collections import defaultdict
import logging
from typing import Any, Iterator, Mapping, Optional, Sequence, Union, override

from flowstack.flows.channels import Channel
from flowstack.flows.channels.utils import read_channel, read_channels
from flowstack.flows.constants import HIDDEN
from flowstack.flows.typing import PregelData, PregelExecutableTask
from flowstack.typing import AddableDict

logger = logging.getLogger(__name__)

def map_input(
    input_channels: Union[str, Sequence[str]],
    chunk: Optional[PregelData]
) -> Iterator[tuple[str, Any]]:
    """
    Map input chunk to a sequence of pending writes in the form (channel, value).
    """
    if chunk is None:
        return
    if isinstance(input_channels, str):
        yield (input_channels, chunk)
    else:
        if not isinstance(chunk, dict):
            raise TypeError(f'Expected chunk to be a dict, got {type(chunk).__name__}.')
        for key, value in chunk.items():
            if key in input_channels:
                yield (key, value)
            else:
                logger.warning(f'Channel {key} not found in {input_channels}.')

class AddableValuesDict(AddableDict):
    @override
    def __add__(self, other: dict[str, Any]) -> 'AddableValuesDict':
        return self | other #type: ignore

    @override
    def __radd__(self, other: dict[str, Any]) -> 'AddableValuesDict':
        return other | self #type: ignore

def map_output_values(
    output_channels: Union[str, Sequence[str]],
    writes: Sequence[tuple[str, Any]],
    channels: Mapping[str, Channel]
) -> Iterator[PregelData]:
    """
    Map pending writes (a sequence of tuples (channel, value)) to output chunk.
    """
    if isinstance(output_channels, str):
        if any(chan == output_channels for chan, _ in writes):
            yield read_channel(channels, output_channels)
        else:
            if {chan for chan, _ in writes if chan in output_channels}:
                yield AddableValuesDict(read_channels(channels, output_channels))

class AddableUpdatesDict(AddableDict):
    @override
    def __add__(self, other: dict[str, Any]) -> 'AddableUpdatesDict':
        yield [self, other]

    @override
    def __radd__(self, other: dict[str, Any]) -> 'AddableUpdatesDict':
        raise TypeError('AddableUpdatesDict does not support right-side addition.')

def map_output_updates(
    output_channels: Union[str, Sequence[str]],
    tasks: list[PregelExecutableTask]
) -> Iterator[dict[str, PregelData]]:
    """
    Map pending writes (a sequence of tuples (channel, value)) to output chunk.
    """
    output_tasks = [
        task for task in tasks
        if not task.config or HIDDEN not in task.config.get('tags', [])
    ]
    if isinstance(output_channels, str):
        if updated := [
            (task.name, value)
            for task in output_tasks
            for chan, value in task.writes
            if chan == output_channels
        ]:
            grouped: dict[str, list[Any]] = defaultdict(list)
            for node, value in updated:
                grouped[node].append(value)
            for node, values in grouped.items():
                if len(values) == 1:
                    grouped[node] = values[0]
            yield AddableUpdatesDict(grouped)
    else:
        if updated := [
            (
                task.name,
                {chan: value for chan, value in task.writes if chan in output_channels}
            )
            for task in output_tasks
            if any(chan in output_channels for chan in task.triggers)
        ]:
            grouped: dict[str, list[Any]] = defaultdict(list)
            for node, value in updated:
                grouped[node].append(value)
            for node, values in grouped.items():
                if len(value) == 1:
                    grouped[node] = values[0]
            yield AddableUpdatesDict(grouped)

def single[T](iterator: Iterator[T]) -> Optional[T]:
    for chunk in iterator:
        return chunk