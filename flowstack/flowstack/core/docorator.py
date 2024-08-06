from functools import cached_property
from typing import Any, Optional, Type, TypeVar, cast, override

from pydantic import BaseModel, Field

from flowstack.core import Component, ReturnType
from flowstack.typing import CallableType
from flowstack.utils.reflection import get_callable_type

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class DecoratorBase(Component[_Input, _Output]):
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

    @cached_property
    @override
    def callable_type(self) -> CallableType:
        return get_callable_type(self.bound)

    def __init__(
        self,
        bound: Component[_Input, _Output],
        custom_input_type: Optional[Type[_Input]] = None,
        custom_output_type: Optional[Type[_Output]] = None,
        custom_input_schema: Optional[Type[BaseModel]] = None,
        custom_output_schema: Optional[Type[BaseModel]] = None,
        **kwargs
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
    def input_schema(self) -> Type[BaseModel]:
        return self.custom_input_schema or self.bound.input_schema()

    @override
    def output_schema(self) -> Type[BaseModel]:
        return self.custom_output_schema or self.bound.output_schema()

    def __call__(self, input: _Input, **kwargs) -> ReturnType[_Output]:
        return self.bound(input, **self.kwargs, **kwargs)

class Decorator(DecoratorBase[_Input, _Output]):
    @override
    def bind(self, **kwargs) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound,
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            **self.kwargs,
            **kwargs
        )

    @override
    def with_types(
        self,
        custom_input_type: Optional[Type[_Input]] = None,
        custom_output_type: Optional[Type[_Output]] = None
    ) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound,
            custom_input_type=custom_input_type or self.custom_input_type,
            custom_output_type=custom_output_type or self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            **self.kwargs
        )

    @override
    def with_schemas(
        self,
        custom_input_schema: Optional[Type[BaseModel]] = None,
        custom_output_schema: Optional[Type[BaseModel]] = None
    ) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound,
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=custom_input_schema or self.custom_input_schema,
            custom_output_schema=custom_output_schema or self.custom_output_schema,
            **self.kwargs
        )

    @override
    def with_retry(self, **kwargs) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound.with_retry(**kwargs),
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            **self.kwargs
        )

    @override
    def with_fallbacks(self, **kwargs) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound.with_fallbacks(**kwargs),
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            **self.kwargs
        )