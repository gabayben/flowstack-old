"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/any_value.py
"""

from contextlib import contextmanager
from typing import Generator, Optional, Self, Sequence, Type

from flowstack.flows import Channel, EmptyChannelError

class AnyValue[Value](Channel[Value, Value, Value]):
    """
    Stores the last value received, assumes that if multiple values are received, they are all equal.
    """

    value: Value

    @property
    def ValueType(self) -> Type[Value]:
        return self._type

    @property
    def UpdateType(self) -> Type[Value]:
        return self._type

    def __init__(self, type_: Type[Value]):
        self._type = type_

    @contextmanager
    def from_checkpoint(self, state: Optional[Value], **kwargs) -> Generator[Self, None, None]:
        channel = self.__class__(self._type)
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
            return EmptyChannelError()

    def get(self) -> Value:
        return self.checkpoint()

    def update(self, values: Sequence[Value]) -> bool:
        if len(values) == 0:
            try:
                del self.value
                return True
            except AttributeError:
                return False
        self.value = values[-1]
        return True

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AnyValue)