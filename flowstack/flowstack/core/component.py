from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncIterator,
    Callable, Iterator,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    final, override
)

from langchain_core.runnables import Runnable
from pydantic import BaseModel

from flowstack.typing import (
    AfterRetryFailure,
    DrawableGraph,
    RetryStrategy,
    ReturnType, Serializable,
    StopStrategy,
    WaitStrategy
)
from flowstack.utils.reflection import get_type_arg

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')
_Other = TypeVar('_Other')

class Component(Serializable, Runnable[_Input, _Output], ABC):
    @property
    @override
    def InputType(self) -> Type[_Input]:
        return get_type_arg(self.__class__, 0, raise_error=True)

    @property
    @override
    def OutputType(self) -> Type[_Output]:
        return get_type_arg(self.__class__, 1, raise_error=True)

    @override
    def __or__(
        self,
        other: Union['ComponentLike[_Output, _Other]', 'ComponentMapping[Any, _Other]']
    ) -> 'Component[_Input, _Other]':
        from flowstack.core.sequential import Sequential
        return Sequential(self, coerce_to_component(other))

    @override
    def __ror__(
        self,
        other: Union['ComponentLike[_Other, _Input]', 'ComponentMapping[_Other, Any]']
    ) -> 'Component[_Other, _Output]':
        from flowstack.core.sequential import Sequential
        return Sequential(coerce_to_component(other), self)

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
    def bind(self, **kwargs) -> 'Component[_Input, _Output]':
        from flowstack.core.decorator import Decorator
        return Decorator(self, kwargs=kwargs)

    @override
    def with_types(
        self,
        custom_input_type: Optional[Type[_Input]] = None,
        custom_output_type: Optional[Type[_Output]] = None
    ) -> 'Component[_Input, _Output]':
        from flowstack.core.decorator import Decorator
        return Decorator(
            self,
            custom_input_type=custom_input_type,
            custom_output_type=custom_output_type
        )

    def with_schemas(
        self,
        custom_input_schema: Optional[Type[BaseModel]] = None,
        custom_output_schema: Optional[Type[BaseModel]] = None
    ) -> 'Component[_Input, _Output]':
        from flowstack.core.decorator import Decorator
        return Decorator(
            self,
            custom_input_schema=custom_input_schema,
            custom_output_schema=custom_output_schema
        )

    @override
    def with_retry(
        self,
        *,
        retry_stategy: Optional[RetryStrategy] = None,
        stop_strategy: Optional[StopStrategy] = None,
        wait_strategy: Optional[WaitStrategy] = None,
        after: Optional[AfterRetryFailure] = None,
        **kwargs
    ) -> 'Component[_Input, _Output]':
        pass

    @override
    def with_fallbacks(
        self,
        fallbacks: Sequence['ComponentLike[_Input, _Output]'],
        *,
        exceptions_to_handle: Optional[tuple[Type[BaseException], ...]] = None,
        **kwargs
    ) -> 'Component[_Input, _Output]':
        pass

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

    @final
    @override
    def batch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        return super().batch(inputs, **kwargs)

    @final
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
    @property
    @override
    def InputType(self) -> Type[_Input]:
        return self._runnable.InputType

    @property
    @override
    def OutputType(self) -> Type[_Output]:
        return self._runnable.OutputType

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

ComponentFunction = Callable[[_Input, ...], ReturnType[_Output]]
ComponentLike = Union[
    Runnable[_Input, _Output],
    Component[_Input, _Output],
    ComponentFunction[_Input, _Output]
]
ComponentMapping = Mapping[str, Union[ComponentLike[_Input, _Output], Any]]

def coerce_to_component(
    thing: Union[ComponentLike[_Input, _Output], ComponentMapping[Any, Any]]
) -> Component[_Input, _Output]:
    from flowstack.core.functional import Functional
    if isinstance(thing, Component):
        return thing
    elif isinstance(thing, Runnable):
        return _CoercedRunnable(thing)
    elif callable(thing):
        return Functional(thing)

def component(
    function: Optional[ComponentFunction[_Input, _Output]] = None,
    name: Optional[str] = None,
    input_schema: Optional[Type[BaseModel]] = None,
    output_schema: Optional[Type[BaseModel]] = None
) -> Component[_Input, _Output]:
    from flowstack.core.functional import Functional
    def decorator(function: ComponentFunction[_Input, _Output]) -> Component[_Input, _Output]:
        return Functional(
            function,
            name=name,
            input_schema=input_schema,
            output_schema=output_schema
        )
    return decorator(function) if function else decorator