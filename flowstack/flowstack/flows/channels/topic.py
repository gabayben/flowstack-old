"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/topic.py
"""

from contextlib import contextmanager
from typing import Generator, Iterator, Optional, Self, Sequence, Type, Union

from flowstack.flows import Channel, EmptyChannelError

type _Update[Value] = Union[Value, list[Value]]
type _State[Value] = tuple[set[Value], list[Value]]

class Topic[Value](Channel[Sequence[Value], _Update[Value], _State[Value]]):
    """
    A configurable PubSub Topic.

    Args:
        type_: The type of the value stored in the channel.
        unique: Whether to discard duplicate values.
        accumulate: Whether to accumulate values across steps. If False, the channel will be emptied after each step.
    """

    @property
    def ValueType(self) -> Type[Sequence[Value]]:
        return Sequence[self._type] #type: ignore[name-defined]

    @property
    def UpdateType(self) -> Type[_Update[Value]]:
        return Union[self._type, list[self._type]] #type: ignore[name-defined]

    def __init__(
        self,
        type_: Type[Value],
        unique: bool = False,
        accumulate: bool = False
    ):
        self._type = type_
        self._unique = unique
        self._accumulate = accumulate
        self._seen: set[Value] = set()
        self._values: list[Value] = list()

    @contextmanager
    def from_checkpoint(self, state: Optional[_State[Value]], **kwargs) -> Generator[Self, None, None]:
        checkpoint = self.__class__(self._type, self._unique, self._accumulate)
        if state is not None:
            checkpoint._seen = state[0].copy()
            checkpoint._values = state[1].copy()
        try:
            yield checkpoint
        finally:
            pass

    def checkpoint(self) -> _State[Value]:
        return self._seen, self._values

    def get(self) -> Sequence[Value]:
        if self._values:
            return list(self._values)
        raise EmptyChannelError()

    def update(self, values: Sequence[_Update[Value]]) -> bool:
        current = list(self._values)
        if not self._accumulate:
            self._values = list[Value]()
        if flat_values := _flatten(values):
            if self._unique:
                for value in flat_values:
                    self._seen.add(value)
                    self._values.append(value)
            else:
                self._values.extend(flat_values)
        return current != self._values

def _flatten[Value](values: Sequence[Union[Value, list[Value]]]) -> Iterator[Value]:
    for value in values:
        if isinstance(value, list):
            yield from value
        else:
            yield value