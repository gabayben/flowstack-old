from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, Mapping, Optional, Type, TypeVar, Union, override

from langchain_core.runnables import Runnable
from pydantic import BaseModel, ConfigDict

from flowstack.typing import Serializable

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Component(Serializable, Runnable[_Input, _Output], ABC):
    model_config = ConfigDict(
        extra='allow',
        arbitrary_types_allowed=True
    )

    @abstractmethod
    def invoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        return super().ainvoke(input, **kwargs)

    @override
    def batch(self, input: list[_Input], **kwargs) -> list[_Output]:
        return super().batch(input, **kwargs)

    @override
    async def abatch(self, input: list[_Input], **kwargs) -> list[_Output]:
        return await super().abatch(input, **kwargs)

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        yield from super().stream(input, **kwargs)

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        async for chunk in super().astream(input, **kwargs):
            yield chunk

    @override
    def transform(self, input: Iterator[_Input], **kwargs) -> Iterator[_Output]:
        yield from super().transform(input, **kwargs)

    @override
    async def atransform(self, input: AsyncIterator[_Input], **kwargs) -> AsyncIterator[_Output]:
        async for chunk in super().atransform(input, **kwargs):
            yield chunk

ComponentFunction = Union[
    Callable[[_Input, ...], _Output],
    Callable[[_Input, ...], Awaitable[_Output]],
    Callable[[list[_Input], ...], list[_Output]],
    Callable[[list[_Input], ...], Awaitable[list[_Output]]],
    Callable[[_Input, ...], Iterator[_Output]],
    Callable[[_Input, ...], AsyncIterator[_Output]],
    Callable[[Iterator[_Input], ...], Iterator[_Output]],
    Callable[[AsyncIterator[_Input], ...], AsyncIterator[_Output]]
]
ComponentLike = Union[
    Runnable[_Input, _Output],
    Component[_Input, _Output],
    ComponentFunction[_Input, _Output]
]
ComponentMapping = Mapping[str, Union[ComponentLike[_Input, _Output], Any]]

def coerce_to_component(
    thing: Union[ComponentLike[_Input, _Output], ComponentMapping[Any, Any]]
) -> Component[_Input, _Output]:
    pass

def component(
    function: Optional[ComponentFunction[_Input, _Output]] = None,
    name: Optional[str] = None,
    input_schema: Optional[Type[BaseModel]] = None,
    output_schema: Optional[Type[BaseModel]] = None
) -> Component[_Input, _Output]:
    def decorator(function: ComponentFunction[_Input, _Output]) -> Component[_Input, _Output]:
        pass
    return decorator(function) if function else decorator