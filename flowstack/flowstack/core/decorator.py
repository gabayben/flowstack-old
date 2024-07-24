from functools import cached_property
from typing import Any, Optional, Type, TypeVar, override

from pydantic import BaseModel

from flowstack.core import Component, SerializableComponent
from flowstack.typing import CallableType, ReturnType

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class DecoratorBase(SerializableComponent[_Input, _Output]):
    bound: Component[_Input, _Output]
    kwargs: dict[str, Any]
    custom_input_schema: Optional[Type[BaseModel]] = None
    custom_output_schema: Optional[Type[BaseModel]] = None

    @property
    @override
    def name(self) -> str:
        return self.bound.name

    @property
    @override
    def description(self) -> str:
        return self.bound.description

    @property
    @override
    def InputType(self) -> Type[_Input]:
        return self.bound.InputType

    @property
    @override
    def OutputType(self) -> Type[_Output]:
        return self.bound.OutputType

    @override
    @cached_property
    def run_type(self) -> CallableType:
        return self.bound.run_type

    def __init__(
        self,
        bound: Component[_Input, _Output],
        custom_input_schema: Optional[Type[BaseModel]] = None,
        custom_output_schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ):
        super().__init__(
            bound=bound,
            custom_input_schema=custom_input_schema,
            custom_output_schema=custom_output_schema,
            kwargs=kwargs
        )

    def run(self, input: _Input, **kwargs) -> ReturnType[_Output]:
        return self.bound.run(input, **self.kwargs, **kwargs)

    @override
    def input_schema(self) -> Type[BaseModel]:
        return self.custom_input_schema or self.bound.input_schema()

    @override
    def output_schema(self) -> Type[BaseModel]:
        return self.custom_output_schema or self.bound.output_schema()

    @override
    def construct_input(self, data: dict[str, Any]) -> _Input:
        return self.bound.construct_input(data)

    @override
    def construct_output(self, data: _Output) -> dict[str, Any]:
        return self.bound.construct_output(data)

class Decorator(DecoratorBase[_Input, _Output]):
    @override
    def bind(self, **kwargs) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound,
            custom_input_schema=self.custom_input_schema,
            custom_output_schema=self.custom_output_schema,
            **{**self.kwargs, **kwargs}
        )

    @override
    def with_types(
        self,
        custom_input_schema: Optional[Type[BaseModel]] = None,
        custom_output_schema: Optional[Type[BaseModel]] = None
    ) -> 'Component[_Input, _Output]':
        return self.__class__(
            self.bound,
            custom_input_schema=custom_input_schema or self.custom_input_schema,
            custom_output_schema=custom_output_schema or self.custom_output_schema,
            **self.kwargs
        )