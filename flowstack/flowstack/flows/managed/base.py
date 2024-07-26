"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/managed/base.py
"""

from abc import ABC, abstractmethod
import asyncio
from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
import inspect
from typing import Any, AsyncGenerator, Generator, NamedTuple, Self, TYPE_CHECKING, Type, TypeGuard, Union

from flowstack.flows.typing import PregelTaskDescription

if TYPE_CHECKING:
    from flowstack.flows.pregel.graph import Pregel

class ManagedValue[Value](ABC):
    def __init__(self, graph: 'Pregel', **config):
        self.graph = graph
        self.config = config

    @contextmanager
    @classmethod
    def enter(cls, graph: 'Pregel', **kwargs) -> Generator[Self, None, None]:
        try:
            value = cls(graph, **kwargs)
            yield value
        finally:
            try:
                del value
            except UnboundLocalError:
                pass

    @asynccontextmanager
    @classmethod
    async def aenter(cls, graph: 'Pregel', **kwargs) -> AsyncGenerator[Self, None, None]:
        try:
            value = cls(graph, **kwargs)
            yield value
        finally:
            try:
                del value
            except UnboundLocalError:
                pass

    @abstractmethod
    def __call__(self, step: int, task: PregelTaskDescription) -> Value:
        pass

class ConfiguredManagedValue(NamedTuple):
    cls: Type[ManagedValue]
    kwargs: dict[str, Any]

ManagedValueSpec = Union[Type[ManagedValue], ConfiguredManagedValue]

@contextmanager
def ManagedValueManager(
    values: dict[str, ManagedValueSpec],
    graph: 'Pregel',
    **kwargs
) -> Generator[dict[str, ManagedValue], None, None]:
    if values:
        with ExitStack() as stack:
            yield {
                name: stack.enter_context(
                    spec.cls.enter(graph, **spec.kwargs, **kwargs)
                    if isinstance(spec, ConfiguredManagedValue)
                    else spec.enter(graph, **kwargs)
                )
                for name, spec in values.items()
            }
    else:
        yield {}

@asynccontextmanager
async def AsyncManagedValueManager(
    values: dict[str, ManagedValueSpec],
    graph: 'Pregel',
    **kwargs
) -> AsyncGenerator[dict[str, ManagedValue], None, None]:
    if values:
        async with AsyncExitStack() as stack:
            tasks = {
                asyncio.create_task(
                    stack.enter_async_context(
                        spec.cls.aenter(graph, **spec.kwargs, **kwargs)
                        if isinstance(spec, ConfiguredManagedValue)
                        else spec.aenter(graph, **kwargs)
                    )
                ): name
                for name, spec in values.items()
            }
            done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            yield {tasks[task]: task.result() for task in done}
    else:
        yield {}

def is_managed_value(value: Any) -> TypeGuard[ManagedValueSpec]:
    return (
        (inspect.isclass(value) and issubclass(value, ManagedValue)) or
        isinstance(value, ConfiguredManagedValue)
    )