from typing import AsyncIterator, Iterator, Optional, Type, TypeVar, override

from pydantic import BaseModel

from flowstack.core import Component, ComponentFunction

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Functional(Component[_Input, _Output]):
    def __init__(
        self,
        function: ComponentFunction[_Input, _Output],
        input_schema: Optional[Type[BaseModel]] = None,
        output_schema: Optional[Type[BaseModel]] = None
    ):

    def invoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    def batch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        pass

    @override
    async def abatch(self, inputs: list[_Input], **kwargs) -> list[_Output]:
        pass

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        pass

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        pass

    @override
    def transform(self, inputs: Iterator[_Input], **kwargs) -> Iterator[_Output]:
        pass

    @override
    async def atransform(self, inputs: AsyncIterator[_Input], **kwargs) -> AsyncIterator[_Output]:
        pass