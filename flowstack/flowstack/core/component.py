from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    override
)

from langchain_core.runnables import Runnable
from pydantic import BaseModel, ConfigDict

from flowstack.typing import DrawableGraph, Serializable

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')
_Other = TypeVar('_Other')

class Component(Serializable, Runnable[_Input, _Output], ABC):
    model_config = ConfigDict(
        extra='allow',
        arbitrary_types_allowed=True
    )

    @override
    def __or__(
        self,
        other: Union['ComponentLike[_Output, _Other]', 'ComponentMapping[Any, _Other]']
    ) -> 'Component[_Input, _Other]':
        pass

    @override
    def __ror__(
        self,
        other: Union['ComponentLike[_Other, _Input]', 'ComponentMapping[_Other, Any]']
    ) -> 'Component[_Other, _Output]':
        pass

    def cast_in(self, mapper: 'ComponentLike[_Other, _Input]') -> 'Component[_Other, _Output]':
        return mapper | self

    def cast_out(self, mapper: 'ComponentLike[_Output, _Other]') -> 'Component[_Input, _Other]':
        return self | mapper

    def cast(
        self,
        in_mapper: 'ComponentLike[_Other, _Input]',
        out_mapper: 'ComponentLike[_Output, _Other]'
    ) -> 'Component[_Other, _Other]':
        return in_mapper | self | out_mapper

    @override
    def get_name(
        self,
        suffix: Optional[str] = None,
        *,
        name: Optional[str] = None
    ) -> str:
        return super().get_name(suffix=suffix, name=name)

    @override
    def get_input_schema(self, **kwargs) -> Type[BaseModel]:
        return super().get_input_schema(**kwargs)

    @override
    def get_output_schema(self, **kwargs) -> Type[BaseModel]:
        return super().get_output_schema(**kwargs)

    @override
    def get_graph(self, **kwargs) -> DrawableGraph:
        return super().get_graph(**kwargs)

    @abstractmethod
    def invoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        return super().ainvoke(input, **kwargs)

    @override
    def batch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        return super().batch(inputs, **kwargs)

    @override
    async def abatch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        return await super().abatch(inputs, **kwargs)

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        yield from super().stream(input, **kwargs)

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        async for chunk in super().astream(input, **kwargs):
            yield chunk

    @override
    def transform(self, inputs: Iterator[_Input], **kwargs) -> Iterator[_Output]:
        yield from super().transform(inputs, **kwargs)

    @override
    async def atransform(self, inputs: AsyncIterator[_Input], **kwargs) -> AsyncIterator[_Output]:
        async for chunk in super().atransform(inputs, **kwargs):
            yield chunk

class _CoercedRunnable(Component[_Input, _Output]):
    def __init__(self, runnable: Runnable[_Input, _Output]):
        self._runnable = runnable

    @override
    def get_name(
        self,
        suffix: Optional[str] = None,
        *,
        name: Optional[str] = None
    ) -> str:
        return self._runnable.get_name(suffix=suffix, name=name)

    @override
    def get_input_schema(self, **kwargs) -> Type[BaseModel]:
        return self._runnable.get_input_schema(**kwargs)

    @override
    def get_output_schema(self, **kwargs) -> Type[BaseModel]:
        return self._runnable.get_output_schema(**kwargs)

    @override
    def get_graph(self, **kwargs) -> DrawableGraph:
        return self._runnable.get_graph(**kwargs)

    def invoke(self, input: _Input, **kwargs) -> _Output:
        return self.bound.invoke(input, **kwargs)

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        return await self.bound.ainvoke(input, **kwargs)

    @override
    def batch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        return self.bound.batch(inputs, **kwargs)

    @override
    async def abatch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        return await self.bound.abatch(inputs, **kwargs)

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        yield from self.bound.stream(input, **kwargs)

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        async for chunk in self.bound.astream(input, **kwargs):
            yield chunk

    @override
    def transform(self, inputs: Iterator[_Input], **kwargs) -> Iterator[_Output]:
        yield from self.bound.transform(inputs, **kwargs)

    @override
    async def atransform(self, inputs: AsyncIterator[_Input], **kwargs) -> AsyncIterator[_Output]:
        async for chunk in self.bound.atransform(inputs, **kwargs):
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
    if isinstance(thing, Component):
        return thing
    elif isinstance(thing, Runnable):
        return _CoercedRunnable(thing)

def component(
    function: Optional[ComponentFunction[_Input, _Output]] = None,
    name: Optional[str] = None,
    input_schema: Optional[Type[BaseModel]] = None,
    output_schema: Optional[Type[BaseModel]] = None
) -> Component[_Input, _Output]:
    def decorator(function: ComponentFunction[_Input, _Output]) -> Component[_Input, _Output]:
        pass
    return decorator(function) if function else decorator