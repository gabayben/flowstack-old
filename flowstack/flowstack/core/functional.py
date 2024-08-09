import inspect
from typing import AsyncIterator, Iterator, Optional, Type, TypeVar, override

from overrides.typing_utils import issubtype
from pydantic import BaseModel

from flowstack.core import Component, ComponentFunction
from flowstack.utils.reflection import get_return_type
from flowstack.utils.threading import run_async, run_async_iter, run_sync, run_sync_iter

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

        self._is_async_stream = issubtype(self._output_type, AsyncIterator)
        self._is_stream = issubtype(self._output_type, Iterator)
        self._is_async = inspect.iscoroutinefunction(function)
        self._is_sync = not self._is_async_stream and not self._is_stream and not self._is_async

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
        if self._is_sync:
            return self._function(input, **kwargs)
        elif self._is_async:
            return run_sync(self._function(input, **kwargs))
        elif self._is_stream:
            return list(self._function(input, **kwargs))[0]
        return run_sync(self.ainvoke(input, **kwargs))

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        if self._is_async:
            return await self._function(input, **kwargs)
        elif self._is_sync:
            return await run_async(self._function, input, **kwargs)
        elif self._is_async_stream:
            value: _Output = None
            async for chunk in self._function(input, **kwargs):
                value = chunk
            return value
        return await run_async(self.invoke, input, **kwargs)

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        if self._is_stream:
            yield from self._function(input, **kwargs)
        elif self._is_async_stream:
            yield from run_sync_iter(self._function, input, **kwargs)
        elif self._is_sync:
            yield self._function(input, **kwargs)
        else:
            yield run_sync(self._function(input, **kwargs))

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        if self._is_async_stream:
            async for chunk in self._function(input, **kwargs):
                yield chunk
        elif self._is_stream:
            async for chunk in run_async_iter(self._function, input, **kwargs):
                yield chunk
        elif self._is_async:
            yield await self._function(input, **kwargs)
        else:
            yield await run_async(self._function, input, **kwargs)