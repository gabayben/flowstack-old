from typing import AsyncIterator, Iterator, override

from langchain_core.runnables import RunnableSerializable

from flowstack.components.ai import LLMInput
from flowstack.messages import BaseMessage

class InstructorChatGenerator(RunnableSerializable[LLMInput, BaseMessage]):
    def invoke(self, input: LLMInput, **kwargs) -> BaseMessage:
        pass

    @override
    async def ainvoke(self, input: LLMInput, **kwargs) -> BaseMessage:
        pass

    @override
    def stream(self, input: LLMInput, **kwargs) -> Iterator[BaseMessage]:
        pass

    @override
    async def astream(self, input: LLMInput, **kwargs) -> AsyncIterator[BaseMessage]:
        pass