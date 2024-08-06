from abc import abstractmethod
from functools import cached_property, partial
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    final,
    get_args,
    override
)

from langchain_core.runnables import Runnable, RunnableSerializable
from pydantic import BaseModel

from flowstack.core import Effect, Effects, ReturnType
from flowstack.typing import AfterRetryFailure, CallableType, RetryStrategy, StopStrategy, WaitStrategy
from flowstack.utils.reflection import get_callable_type
from flowstack.utils.serialization import create_schema

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')
_Other = TypeVar('_Other')

class Component(RunnableSerializable[_Input, _Output]):
    @override
    @property
    def InputType(self) -> Type[_Input]:
        for cls in self.__class__.__orig_bases__: # type: ignore[attr-defined]
            type_args = get_args(cls)
            if type_args and len(type_args) == 1:
                return type_args[0]
        raise TypeError(
            f"Module {self.name} doesn't have an inferrable InputType."
            'Override the OutputType property to specify the output type.'
        )

    @override
    @property
    def OutputType(self) -> Type[_Output]:
        for cls in self.__class__.__orig_bases__: # type: ignore[attr-defined]
            type_args = get_args(cls)
            if type_args and len(type_args) == 2:
                return type_args[1]
        raise TypeError(
            f"Module {self.name} doesn't have an inferrable OutputType."
            'Override the OutputType property to specify the output type.'
        )

    @cached_property
    def callable_type(self) -> CallableType:
        return get_callable_type(self)

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

    @final
    def cast_in(self, mapper: 'ComponentLike[_Other, _Input]') -> 'Component[_Other, _Output]':
        return mapper | self

    @final
    def cast_out(self, mapper: 'ComponentLike[_Output, _Other]') -> 'Component[_Input, _Other]':
        return self | mapper

    @final
    def cast(
        self,
        in_mapper: 'ComponentLike[_Other, _Input]',
        out_mapper: 'ComponentLike[_Output, _Other]'
    ) -> 'Component[_Other, _Other]':
        return in_mapper | self | out_mapper

    @override
    def bind(self, **kwargs) -> 'Component[_Input, _Output]':
        pass

    @override
    def with_types(
        self,
        input_type: Optional[Type[_Input]] = None,
        output_type: Optional[Type[_Output]] = None
    ) -> 'Component[_Input, _Output]':
        pass

    @override
    def with_retry(
        self,
        *,
        retry: Optional[RetryStrategy] = None,
        stop: Optional[StopStrategy] = None,
        wait: Optional[WaitStrategy] = None,
        after_retry_failure: Optional[AfterRetryFailure] = None,
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
    def input_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Input'), self.InputType)

    @override
    def output_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Output'), self.OutputType)

    @abstractmethod
    def __call__(self, input: _Input, **kwargs) -> ReturnType[_Output]:
        pass

    @final
    def effect(self, input: _Input, **kwargs) -> Effect[_Output]:
        callable_type = self.callable_type
        if callable_type == 'effect':
            return self(input, **kwargs)
        function = partial(self, input, **kwargs)
        if callable_type == 'aiter':
            return Effects.AsyncIterator(function)
        elif callable_type == 'iter':
            return Effects.Iterator(function)
        elif callable_type == 'ainvoke':
            return Effects.Async(function)
        return Effects.Sync(function)

    @final
    def invoke(self, input: _Input, **kwargs) -> _Output:
        return self.effect(input, **kwargs).invoke()

    @final
    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        return await self.effect(input, **kwargs).ainvoke()

    @final
    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        yield from self.effect(input, **kwargs).iter()

    @final
    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        async for chunk in self.effect(input, **kwargs).aiter(): #type: ignore
            yield chunk

    @final
    @override
    def batch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        return super().batch(inputs, **kwargs)

    @final
    @override
    async def abatch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        return await super().abatch(inputs, **kwargs)

    @final
    @override
    def transform(self, inputs: Iterator[_Input], **kwargs) -> Iterator[_Output]:
        yield from super().transform(inputs, **kwargs)

    @final
    @override
    async def atransform(self, inputs: AsyncIterator[_Input], **kwargs) -> AsyncIterator[_Output]:
        async for chunk in super().atransform(inputs, **kwargs):
            yield chunk

class _CoercedRunnable(Component[_Input, _Output]):
    def __init__(self, runnable: Runnable[_Input, _Output]):
        self._runnable = runnable

    def __call__(self, input: _Input, **kwargs) -> Effect[_Output]:
        return Effects.From(
            invoke=partial(self._runnable.invoke, input, **kwargs),
            ainvoke=partial(self._runnable.ainvoke, input, **kwargs),
            iter_=partial(self._runnable.stream, input, **kwargs),
            aiter_=partial(self._runnable.astream, input, **kwargs)
        )

ComponentFunction = Callable[[_Input, ...], ReturnType[_Output]]
ComponentLike = Union[Runnable[_Input, _Output], Component[_Input, _Output], ComponentFunction[_Input, _Output]]
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
    input_schema: Optional[BaseModel] = None,
    output_schema: Optional[BaseModel] = None
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