import inspect
from typing import AsyncIterator, Iterator, Optional, Type, TypeVar, override

from pydantic import BaseModel

from flowstack.core import Component, ComponentFunction
from flowstack.utils.reflection import get_return_type

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Functional(Component[_Input, _Output]):
    @property
    @override
    def InputType(self) -> Type[_Input]:
        return self._parameter.annotation

    @property
    @override
    def OutputType(self) -> Type[_Output]:
        return self._output_type

    def __init__(
        self,
        function: ComponentFunction[_Input, _Output],
        name: Optional[str] = None,
        input_schema: Optional[Type[BaseModel]] = None,
        output_schema: Optional[Type[BaseModel]] = None
    ):
        signature = inspect.signature(function)
        parameters = {
            key: value
            for key, value in signature.parameters.items()
            if value.annotation != inspect.Parameter.empty
        }
        if len(parameters) == 0:
            raise ValueError(
                'A function that is decorated with @component must have an input.'
            )
        self._parameter = list(parameters.values())[0]
        self._output_type = get_return_type(function)

        self._function = function
        self._input_schema = input_schema
        self._output_schema = output_schema
        super().__init__(name=name or function.__name__)

    @override
    def get_input_schema(self, **kwargs) -> Type[BaseModel]:
        return self._input_schema or super().get_input_schema(**kwargs)

    @override
    def get_output_schema(self, **kwargs) -> Type[BaseModel]:
        return self._output_schema or super().get_output_schema(**kwargs)

    def invoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        pass

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        pass