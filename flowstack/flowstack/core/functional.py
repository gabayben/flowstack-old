import inspect
from typing import Optional, Type, TypeVar, override

from pydantic import BaseModel

from flowstack.core import Component, ComponentFunction, ReturnType
from flowstack.typing import CallableType
from flowstack.utils.reflection import get_callable_type

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Functional(Component[_Input, _Output]):
    @property
    @override
    def InputType(self) -> Type[_Input]:
        return self._parameter.annotation or super().InputType

    @property
    @override
    def OutputType(self) -> Type[_Output]:
        return self._signature.return_annotation or super().OutputType

    @property
    @override
    def callable_type(self) -> CallableType:
        return get_callable_type(self._function)

    def __init__(
        self,
        function: ComponentFunction[_Input, _Output],
        name: Optional[str] = None,
        input_schema: Optional[Type[BaseModel]] = None,
        output_schema: Optional[Type[BaseModel]] = None
    ):
        self._signature = inspect.signature(function)
        parameters = {
            key: value
            for key, value in self._signature.parameters.items()
            if value.annotation != inspect.Parameter.empty
        }
        if len(parameters) == 0:
            raise ValueError('A function that is decorated with @component must have an input.')
        self._parameter = list(parameters.values())[0]

        self._function = function
        self._name = name or function.__name__
        self._input_schema = input_schema
        self._output_schema = output_schema

    @override
    def get_name(
        self,
        suffix: Optional[str] = None,
        *,
        name: Optional[str] = None
    ) -> str:
        return super().get_name(suffix=suffix, name=self._name or name)

    @override
    def input_schema(self) -> Type[BaseModel]:
        return self._input_schema or super().input_schema()

    @override
    def output_schema(self) -> Type[BaseModel]:
        return self._output_schema or super().output_schema()

    def __call__(self, input: _Input, **kwargs) -> ReturnType[_Output]:
        return self._function(input, **kwargs)