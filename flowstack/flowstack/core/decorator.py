from abc import ABC
from typing import Any, AsyncIterator, Iterator, Optional, Type, TypeVar, cast, override

from pydantic import BaseModel, Field

from flowstack.core import Component
from flowstack.typing import DrawableGraph

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class BaseDecorator(Component[_Input, _Output], ABC):
    bound: Component[_Input, _Output]
    custom_input_type: Optional[Type[_Input]] = None
    custom_output_type: Optional[Type[_Output]] = None
    custom_input_schema: Optional[Type[BaseModel]] = None
    custom_output_schema: Optional[Type[BaseModel]] = None
    kwargs: dict[str, Any] = Field(default_factory=dict)

    @property
    @override
    def InputType(self) -> Type[_Input]:
        return (
            cast(Type[_Input], self.custom_input_type)
            if self.custom_input_type
            else super().InputType
        )

    @property
    @override
    def OutputType(self) -> Type[_Output]:
        return (
            cast(Type[_Output], self.custom_output_type)
            if self.custom_output_type
            else super().OutputType
        )

    def __init__(
        self,
        bound: Component[_Input, _Output],
        custom_input_type: Optional[Type[_Input]] = None,
        custom_output_type: Optional[Type[_Output]] = None,
        custom_input_schema: Optional[Type[BaseModel]] = None,
        custom_output_schema: Optional[Type[BaseModel]] = None,
        kwargs: dict[str, Any] = {}
    ):
        super().__init__(
            bound=bound,
            custom_input_type=custom_input_type,
            custom_output_type=custom_output_type,
            custom_input_schema=custom_input_schema,
            custom_output_schema=custom_output_schema,
            kwargs=kwargs
        )

    @override
    def get_name(
        self,
        suffix: Optional[str] = None,
        *,
        name: Optional[str] = None
    ) -> str:
        return self.bound.get_name(suffix=suffix, name=name)

    @override
    def get_input_schema(self, **kwargs) -> Type[BaseModel]:
        return self.custom_input_schema or self.bound.get_input_schema(**kwargs)

    @override
    def get_output_schema(self, **kwargs) -> Type[BaseModel]:
        return self.custom_output_schema or self.bound.get_output_schema(**kwargs)

    @override
    def get_graph(self, **kwargs) -> DrawableGraph:
        return self.bound.get_graph(**kwargs)

    def invoke(self, input: _Input, **kwargs) -> _Output:
        return self.bound.invoke(input, **self.kwargs, **kwargs)

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        return await self.bound.ainvoke(input, **self.kwargs, **kwargs)

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        yield from self.bound.stream(input, **self.kwargs, **kwargs)

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        async for chunk in self.bound.astream(input, **self.kwargs, **kwargs):
            yield chunk

    @override
    def transform(self, inputs: Iterator[_Input], **kwargs) -> Iterator[_Output]:
        yield from self.bound.transform(inputs, **self.kwargs, **kwargs)

    @override
    async def atransform(self, inputs: AsyncIterator[_Input], **kwargs) -> AsyncIterator[_Output]:
        async for chunk in self.bound.atransform(inputs, **self.kwargs, **kwargs):
            yield chunk

class Decorator(BaseDecorator[_Input, _Output]):
    @override
    def bind(self, **kwargs) -> Component[_Input, _Output]:
        return self.__class__(
            self.bound,
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            kwargs={**self.kwargs, **kwargs}
        )

    @override
    def with_types(
        self,
        custom_input_type: Optional[Type[_Input]] = None,
        custom_output_type: Optional[Type[_Output]] = None
    ) -> Component[_Input, _Output]:
        return self.__class__(
            self.bound,
            custom_input_type=custom_input_type or self.custom_input_type,
            custom_output_type=custom_output_type or self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            kwargs=self.kwargs
        )

    @override
    def with_schemas(
        self,
        custom_input_schema: Optional[Type[BaseModel]] = None,
        custom_output_schema: Optional[Type[BaseModel]] = None
    ) -> Component[_Input, _Output]:
        return self.__class__(
            self.bound,
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=custom_input_schema or self.custom_input_schema,
            custom_output_schema=custom_output_schema or self.custom_output_schema,
            kwargs=self.kwargs
        )

    @override
    def with_retry(self, **kwargs) -> Component[_Input, _Output]:
        return self.__class__(
            self.bound.with_retry(**kwargs),
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            kwargs=self.kwargs
        )

    @override
    def with_fallbacks(self, *args, **kwargs) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound.with_fallbacks(*args, **kwargs),
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            kwargs=self.kwargs
        )