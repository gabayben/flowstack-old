"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/write.py
"""

import asyncio
from functools import partial
from typing import Any, Callable, NamedTuple, Optional, Sequence, Union

from flowstack.core import Component
from flowstack.flows.constants import IS_CHANNEL_WRITER, TASKS
from flowstack.flows.errors import InvalidUpdateError
from flowstack.flows.typing import Send
from flowstack.typing import Effect, Effects
from flowstack.utils.func import tzip

WRITE_TYPE = Callable[[Sequence[tuple[str, Any]]], None]
SKIP_WRITE = object()
PASSTHROUGH = object()

class ChannelWriteEntry(NamedTuple):
    channel: str
    value: Any = PASSTHROUGH
    mapper: Optional[Component] = None
    skip_none: bool = False

class ChannelWrite(Component):
    def __init__(
        self,
        writes: Sequence[Union[ChannelWriteEntry, Send]],
        *,
        required_channels: Optional[Sequence[str]] = None,
        tags: Optional[list[str]] = None
    ):
        self.writes = writes
        self.required_channels = required_channels
        self.tags = tags

    def run(self, input: Any, **kwargs) -> Effect[Any]:
        return Effects.From(
            invoke=partial(self._write, input, **kwargs),
            ainvoke=partial(self._awrite, input, **kwargs)
        )

    def _write(self, input: Any, **kwargs) -> Any:
        packets = [(TASKS, packet) for packet in self.writes if isinstance(packet, Send)]
        entries = [entry for entry in self.writes if isinstance(entry, ChannelWriteEntry)]
        for entry in entries:
            if entry.channel is TASKS:
                raise InvalidUpdateError(f'Cannot write to the reserved channel {TASKS}')
        values = [input if entry.value is PASSTHROUGH else entry.value for entry in entries]
        values = [
            value if entry.mapper is not None else entry.mapper.invoke(value, **kwargs)
            for value, entry in tzip(values, entries)
        ]
        values = [
            (entry.channel, value)
            for value, entry in tzip(values, entries)
            if not entry.skip_none or value is not None
        ]
        self.do_write(
            values + packets,
            required_channels=self.required_channels if input is not None else None,
            **kwargs
        )
        return input

    async def _awrite(self, input: Any, **kwargs) -> Any:
        packets = [(TASKS, packet) for packet in self.writes if isinstance(packet, Send)]
        entries = [entry for entry in self.writes if isinstance(entry, ChannelWriteEntry)]
        for entry in entries:
            if entry.channel is TASKS:
                raise InvalidUpdateError(f'Cannot write to the reserved channel {TASKS}')
        values = [input if entry.value is PASSTHROUGH else entry.value for entry in entries]
        values = await asyncio.gather(
            *(
                _make_future(value)
                if entry.mapper is None
                else entry.mapper.ainvoke(value, **kwargs)
                for value, entry in tzip(values, entries)
            )
        )
        values = [
            (entry.channel, value)
            for value, entry in tzip(values, entries)
            if not entry.skip_none or value is not None
        ]
        self.do_write(
            values + packets,
            required_channels=self.required_channels if input is not None else None,
            **kwargs
        )
        return input

    @staticmethod
    def do_write(
        values: list[tuple[str, Any]],
        required_channels: Optional[Sequence[str]] = None,
        **config
    ) -> None:
        filtered = [(chan, value) for chan, value in values if value is not SKIP_WRITE]
        if required_channels is not None:
            if not {chan for chan, _ in filtered} and set(filtered):
                raise InvalidUpdateError(
                    f'Must write to at least one of {required_channels}'
                )
        try:
            write: WRITE_TYPE = config[WRITE_TYPE]
            write(filtered)
        except KeyError:
            raise RuntimeError(
                'Not configured with a write function.'
                'Make sure to call in the context of a Pregel process.'
            )

    @staticmethod
    def register_writer(component: Component) -> None:
        object.__setattr__(component, IS_CHANNEL_WRITER, True)

    @staticmethod
    def is_writer(component: Component) -> bool:
        return (
            isinstance(component, ChannelWrite) or
            getattr(component, IS_CHANNEL_WRITER, False)
        )

def _make_future(value: Any) -> asyncio.Future:
    future = asyncio.Future()
    future.set_result(value)
    return future