from abc import ABC, abstractmethod
from functools import cached_property, partial
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Mapping, Optional, Type, TypeVar, Union, final, get_args

from pydantic import BaseModel

from flowstack.typing import CallableType, Effect, Effects, ReturnType, Serializable
from flowstack.utils.reflection import get_callable_type
from flowstack.utils.serialization import create_schema, from_dict, to_dict

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')
_Other = TypeVar('_Other')

class Component(Generic[_Input, _Output], ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def description(self) -> str:
        return self.__class__.__doc__ or ''

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
    def run_type(self) -> CallableType:
        return get_callable_type(self.run)

    def __or__(self, other: 'ComponentLike[_Output, _Other]') -> 'Component[_Input, _Other]':
        from flowstack.core.sequential import Sequential
        return Sequential(self, coerce_to_component(other))

    def __ror__(self, other: 'ComponentLike[_Other, _Input]') -> 'Component[_Other, _Output]':
        from flowstack.core.sequential import Sequential
        return Sequential(coerce_to_component(other), self)

    def map_in(self, mapper: 'ComponentLike[_Other, _Input]') -> 'Component[_Other, _Output]':
        return mapper | self

    def map_out(self, mapper: 'ComponentLike[_Output, _Other]') -> 'Component[_Input, _Other]':
        return self | mapper

    def map(
        self,
        in_mapper: 'ComponentLike[_Other, _Input]',
        out_mapper: 'ComponentLike[_Output, _Other]'
    ) -> 'Component[_Other, _Other]':
        return in_mapper | self | out_mapper

    def bind(self, **kwargs) -> 'Component[_Input, _Output]':
        from flowstack.core.decorator import Decorator
        return Decorator(self, **kwargs)

    def with_types(
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

    @abstractmethod
    def run(self, input: _Input, **kwargs) -> ReturnType[_Output]:
        pass

    @final
    def effect(self, input: _Input, **kwargs) -> Effect[_Output]:
        callable_type = self.run_type
        if callable_type == 'effect':
            return self.run(input, **kwargs)
        function = partial(self.run, input, **kwargs)
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
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        return await self.effect(input, **kwargs).ainvoke()

    @final
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        yield from self.effect(input, **kwargs).iter()

    @final
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        async for chunk in self.effect(input, **kwargs).aiter(): #type: ignore
            yield chunk

    def input_schema(self) -> Type[BaseModel]:
        return create_schema(f'{self.name}Input', self.InputType)

    def output_schema(self) -> Type[BaseModel]:
        return create_schema(f'{self.name}Output', self.OutputType)

    def construct_input(self, data: dict[str, Any]) -> _Input:
        return from_dict(data, self.input_schema())

    def construct_output(self, data: _Output) -> dict[str, Any]:
        return to_dict(data)

class SerializableComponent(Serializable, Component[_Input, _Output], ABC):
    pass

ComponentFunction = Callable[[_Input, ...], ReturnType[_Output]]
ComponentLike = Union[Component[_Input, _Output], ComponentFunction[_Input, _Output]]
ComponentMapping = Mapping[str, ComponentLike[_Input, Any]]

def coerce_to_component(
    thing: Union[ComponentLike[_Input, _Output], ComponentMapping[_Input]]
) -> Component[_Input, _Output]:
    from flowstack.core.functional import Functional
    from flowstack.core.parallel import Parallel
    if isinstance(thing, Component):
        return thing
    elif isinstance(thing, Mapping):
        return Parallel(thing)
    return Functional(thing)

def component(
    function: Optional[ComponentFunction[_Input, _Output]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_schema: Optional[Type[BaseModel]] = None,
    output_schema: Optional[Type[BaseModel]] = None
) -> Component[_Input, _Output]:
    from flowstack.core.functional import Functional
    def wrapper(function: ComponentFunction[_Input, _Output]) -> Component[_Input, _Output]:
        return Functional(
            function,
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema
        )
    return wrapper(function) if function else wrapper