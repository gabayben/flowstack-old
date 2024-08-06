from functools import partial
from typing import AsyncIterator, Iterator

from flowstack.components.ai import LLMInput
from flowstack.core import Component, Effect, Effects
from flowstack.messages import BaseMessage

class InstructorChatGenerator(Component[LLMInput, BaseMessage]):
    def __call__(self, input: LLMInput, **kwargs) -> Effect[BaseMessage]:
        return Effects.From(
            invoke=partial(self._invoke, input, **kwargs),
            ainvoke=partial(self._ainvoke, input, **kwargs),
            iter_=partial(self._stream, input, **kwargs),
            aiter_=partial(self._astream, input, **kwargs)
        )

    def _invoke(self, input: LLMInput, **kwargs) -> BaseMessage:
        pass

    async def _ainvoke(self, input: LLMInput, **kwargs) -> BaseMessage:
        pass

    def _stream(self, input: LLMInput, **kwargs) -> Iterator[BaseMessage]:
        pass

    async def _astream(self, input: LLMInput, **kwargs) -> AsyncIterator[BaseMessage]:
        pass