"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/context.py
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncContextManager, AsyncGenerator, ContextManager, Generator, Optional, Self, Sequence, Type, Union, override

from flowstack.flows.channels import Channel
from flowstack.flows.errors import EmptyChannelError, InvalidUpdateError

class ContextValue[Value](Channel[Value, None, None]):
    """
    Exposes the value of a context manager, for the duration of an invocation.
    Context manager is entered before the first step, and exited after the last step.
    Optionally, provide an equivalent async context manager, which will be used
    instead for async invocations.

    ```python
    import httpx

    client = Channels.Context(httpx.Client, httpx.AsyncClient)
    ```
    """

    value: Value

    @property
    def ValueType(self) -> Type[None]:
        return None

    @property
    def UpdateType(self) -> Type[None]:
        return None

    def __init__(
        self,
        manager: Optional[ContextManager[Value]] = None,
        async_manager: Optional[Union[ContextManager[Value], AsyncContextManager[Value]]] = None
    ):
        if manager is None and async_manager is None:
            raise ValueError('Must provide either sync or async context manager.')
        self._manager = manager
        self._async_manager = async_manager

    @contextmanager
    def from_checkpoint(self, state: None, **kwargs) -> Generator[Self, None, None]:
        if self._manager is None or not hasattr(self._manager, '__enter__'):
            raise ValueError('Cannot enter sync context manager.')
        channel = self.__class__(self._manager, self._async_manager)
        try:
            ctx = self._manager(**kwargs)
        except BaseException:
            ctx = self._manager()
        with ctx as value:
            channel.value = value
            yield channel

    @asynccontextmanager
    @override
    async def afrom_checkpoint(self, state: None, **kwargs) -> AsyncGenerator[Self, None, None]:
        channel = self.__class__(self._manager, self._async_manager)
        manager = (
            self._async_manager
            if self._async_manager is not None
            else self._manager
        )
        try:
            ctx = manager(**kwargs)
        except BaseException:
            ctx = manager()
        if hasattr(ctx, '__aenter__'):
            async with ctx as value:
                channel.value = value
                yield channel
        else:
            with ctx as value:
                channel.value = value
                yield channel

    def checkpoint(self) -> None:
        raise EmptyChannelError()

    def get(self) -> Value:
        try:
            return self.value
        except AttributeError:
            raise EmptyChannelError()

    def update(self, values: Sequence[None]) -> bool:
        if values:
            raise InvalidUpdateError('ContextValue does not accept writes.')
        return False

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ContextValue) and
            self._manager == other._manager and
            self._async_manager == other._async_manager
        )