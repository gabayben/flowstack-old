"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/ephemeral_value.py
"""

from contextlib import contextmanager
from typing import Generator, Optional, Self, Sequence, Type

from flowstack.flows import Channel, EmptyChannelError, InvalidUpdateError

class EphemeralValue[Value](Channel[Value, Value, Value]):
    value: Value

    @property
    def ValueType(self) -> Type[Value]:
        return self._type

    @property
    def UpdateType(self) -> Type[Value]:
        return self._type

    def __init__(self, type_: Type[Value], guard: bool = True):
        self._type = type_
        self._guard = guard

    @contextmanager
    def from_checkpoint(self, state: Optional[Value], **kwargs) -> Generator[Self, None, None]:
        channel = self.__class__(self._type, self._guard)
        if state is not None:
            channel.value = state
        try:
            yield channel
        finally:
            try:
                del channel.value
            except AttributeError:
                pass

    def checkpoint(self) -> Value:
        try:
            return self.value
        except AttributeError:
            raise EmptyChannelError()

    def get(self) -> Value:
        return self.checkpoint()

    def update(self, values: Sequence[Value]) -> bool:
        if len(values) == 0:
            try:
                del self.value
                return True
            except AttributeError:
                raise False
        if len(values) != 1 and self._guard:
            raise InvalidUpdateError(
                "EphemeralValue cannot only receive one value per step."
            )
        self.value = values[-1]
        return True