"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/named_barrier_value.py
"""

from contextlib import contextmanager
from typing import Generator, Optional, Self, Sequence, Type, override

from flowstack.flows import Channel, EmptyChannelError, InvalidUpdateError

class NamedBarrierValue[Value](Channel[Value, Value, set[Value]]):
    """
    A channel that waits until all named values are received before making the value available.
    """

    @property
    def ValueType(self) -> Value:
        return self._type

    @property
    def UpdateType(self) -> Value:
        return self._type

    def __init__(self, type_: Type[Value], names: set[Value]):
        self._type = type_
        self._names = names
        self._seen: set[Value] = set()

    @contextmanager
    def from_checkpoint(self, state: Optional[set[Value]], **kwargs) -> Generator[Self, None, None]:
        channel = self.__class__(self._type, self._names)
        if state is not None:
            channel._seen = state.copy()
        try:
            yield channel
        finally:
            pass

    def checkpoint(self) -> set[Value]:
        return self._seen

    def get(self) -> Optional[Value]:
        if self._seen != self._names:
            raise EmptyChannelError()
        return None

    def update(self, values: Sequence[Value]) -> bool:
        updated = False
        for value in values:
            if value in self._names:
                if value not in self._seen:
                    self._seen.add(value)
                    updated = True
            else:
                raise InvalidUpdateError(f'Value {value} not in {self._names}.')
        return updated

    @override
    def consume(self) -> bool:
        if self._seen == self._names:
            self._seen = set()
            return True
        return False