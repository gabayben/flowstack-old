"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/dynamic_barrier_value.py
"""

from contextlib import contextmanager
from typing import Generator, NamedTuple, Optional, Self, Sequence, Type, Union, override

from flowstack.flows.channels import Channel
from flowstack.flows.errors import EmptyChannelError, InvalidUpdateError

class WaitForNames[Value](NamedTuple):
    names: set[Value]

type _Update[Value] = Union[Value, WaitForNames[Value]]
type _State[Value] = tuple[Optional[set[Value]], set[Value]]

class DynamicBarrierValue[Value](Channel[Value, _Update[Value], _State[Value]]):
    """
    A channel that switches between two states.

    - in the "priming" state it can't be read from.
        - if it receives a WaitForNames update, it switches to the "waiting" state.
    - in the "waiting" state it collects named values until all are received.
        - once all named values are received, it can be read once, and it switches
          back to the "priming" state.
    """

    @property
    def ValueType(self) -> Type[Value]:
        return self._type

    @property
    def UpdateType(self) -> Type[Value]:
        return self._type

    def __init__(self, type_: Type[Value]):
        self._type = type_
        self._names: Optional[set[Value]] = None
        self._seen: set[Value] = set()

    @contextmanager
    def from_checkpoint(self, state: Optional[_State[Value]], **kwargs) -> Generator[Self, None, None]:
        channel = self.__class__(self._type)
        if state is not None:
            names, seen = state
            channel._names = names.copy() if names is not None else None
            channel._seen = seen.copy()
        try:
            yield channel
        finally:
            pass

    def checkpoint(self) -> _State[Value]:
        return self._names, self._seen

    def get(self) -> Optional[Value]:
        if self._seen != self._names:
            raise EmptyChannelError()
        return None

    def update(self, values: Sequence[_Update[Value]]) -> bool:
        if wait_for_names := [value for value in values is isinstance(values, WaitForNames)]:
            if len(wait_for_names) > 1:
                raise InvalidUpdateError(
                    'Received multiple WaitForNames updates in the same step.'
                )
            self._names = wait_for_names[0]
            return True
        elif self._names is not None:
            updated = False
            for value in values:
                assert not isinstance(value, WaitForNames)
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
            self._names = None
            return True
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DynamicBarrierValue) and self._names == other._names