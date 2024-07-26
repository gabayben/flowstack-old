"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/binop.py
"""

import collections.abc
from contextlib import contextmanager
from typing import Callable, Generator, NotRequired, Optional, Required, Self, Sequence, Type

from flowstack.flows.channels import Channel
from flowstack.flows.errors import EmptyChannelError

class BinaryOperatorAggregate[Value](Channel[Value, Value, Value]):
    """
    Stores the result of applying a binary operator to the current value and each new value.

    ```python
    import operator

    total = BinaryOperatorAggregate(int, operator.add)
    ```
    """

    value: Value

    @property
    def ValueType(self) -> Type[Value]:
        return self._type

    @property
    def UpdateType(self) -> Type[Value]:
        return self._type

    def __init__(
        self,
        type_: Type[Value],
        operator: Callable[[Value, Value], Value]
    ):
        self._type = type_
        self._operator = operator

        type_ = _strip_extras(type_)
        if type_ in (collections.abc.Sequence, collections.abc.MutableSequence):
            type_ = list
        if type_ in (collections.abc.Set, collections.abc.MutableSet):
            type_ = set
        if type_ in (collections.abc.Mapping, collections.abc.MutableMapping):
            type_ = dict

        try:
            self.value = type_()
        except BaseException:
            pass

    @contextmanager
    def from_checkpoint(self, state: Optional[Value], **kwargs) -> Generator[Self, None, None]:
        channel = self.__class__(self._type, self._operator)
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
        if not values:
            return False
        if not hasattr(self, 'value'):
            self.value = values[0]
            values = values[1:]
        for value in values:
            self.value = self._operator(self.value, value)
        return True

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BinaryOperatorAggregate) and (
            self._operator == other._operator
            if self._operator.__name__ != '<lambda>'
            and other._operator.__name__ != '<lambda>'
            else True
        )

def _strip_extras(type_: type) -> type:
    """
    Strips Annotated, Required and NotRequired from a given type.
    """
    if hasattr(type_, '__origin__'):
        return _strip_extras(type_.__origin__)
    if hasattr(type_, '__origin__') and type_.__origin__ in (Required, NotRequired): #type: ignore
        return _strip_extras(type_.__args__[0])
    return type_