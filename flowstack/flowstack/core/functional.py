from functools import cached_property
import inspect
from typing import Optional, Type, TypeVar, override

from pydantic import BaseModel

from flowstack.core import Component, ComponentFunction
from flowstack.typing import CallableType, ReturnType
from flowstack.utils.reflection import get_callable_type

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Functional(Component[_Input, _Output]):
    @override
    @property
    def name(self) -> str:
        return self._name or super().name

    @override
    @property
    def description(self) -> str:
        return self._description or super().description

    @override
    @property
    def InputType(self) -> Type[_Input]:
        return self._parameter.annotation or super().InputType

    @override
    @property
    def OutputType(self) -> Type[_Output]:
        return self._signature.return_annotation or super().OutputType

    @override
    @cached_property
    def run_type(self) -> CallableType:
        return get_callable_type(self._function)

    def __init__(
        self,
        function: ComponentFunction[_Input, _Output],
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_schema: Optional[Type[BaseModel]] = None,
        output_schema: Optional[Type[BaseModel]] = None
    ):
        self._signature = inspect.signature(function)
        parameters = {key: value for key, value in self._signature.parameters.items() if
                      value.annotation != inspect.Parameter.empty}
        if len(parameters) == 0:
            raise ValueError('A function that is decorated with `@module` must have an input.')
        self._parameter = list(parameters.values())[0]

        self._function = function
        self._name = name or function.__name__
        self._description = description or function.__doc__
        self._input_schema = input_schema
        self._output_schema = output_schema

    def run(self, input: _Input, **kwargs) -> ReturnType[_Output]:
        return self._function(input, **kwargs)

    @override
    def input_schema(self) -> Type[BaseModel]:
        return self._input_schema or super().input_schema()

    @override
    def output_schema(self) -> Type[BaseModel]:
        return self._output_schema or super().output_schema()