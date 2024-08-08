from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator, Union, final, override

from flowstack.core import Component
from flowstack.messages import BaseMessage, MessageContent
from flowstack.utils.threading import run_async

LLMInput = Union[MessageContent, list[BaseMessage]]
ChatGenerator = Component[LLMInput, BaseMessage]

class ChatPrompt:
    @property
    def messages(self) -> list[BaseMessage]:
        raise NotImplementedError()

    @property
    def system(self) -> BaseMessage:
        raise NotImplementedError()

    @property
    def current(self) -> BaseMessage:
        raise NotImplementedError()

    def __init__(self, input: LLMInput):
        pass

class BaseChatGenerator(ChatGenerator, ABC):
    """
    Base chat generator.
    """

    # Sync

    @final
    def invoke(self, input: LLMInput, **kwargs) -> BaseMessage:
        pass

    @abstractmethod
    def _invoke(self, prompt: ChatPrompt, **kwargs) -> BaseMessage:
        pass

    # Async

    @final
    @override
    async def ainvoke(self, input: LLMInput, **kwargs) -> BaseMessage:
        pass

    async def _ainvoke(self, prompt: ChatPrompt, **kwargs) -> BaseMessage:
        return await run_async(self._invoke, prompt, **kwargs)

    # Batch

    @final
    @override
    def batch(self, input: list[LLMInput], **kwargs) -> list[BaseMessage]:
        pass

    def _batch(self, prompts: list[ChatPrompt], **kwargs) -> list[BaseMessage]:
        pass

    # Async Batch

    @final
    @override
    async def abatch(self, input: list[LLMInput], **kwargs) -> list[BaseMessage]:
        pass

    async def _abatch(self, prompts: list[ChatPrompt], **kwargs) -> list[BaseMessage]:
        pass

    # Stream

    @final
    @override
    def stream(self, input: LLMInput, **kwargs) -> Iterator[BaseMessage]:
        pass

    def _stream(self, prompt: ChatPrompt, **kwargs) -> Iterator[BaseMessage]:
        yield self._invoke(prompt, **kwargs)

    # Async Stream

    @final
    @override
    async def astream(self, input: LLMInput, **kwargs) -> AsyncIterator[BaseMessage]:
        pass

    async def _astream(self, prompt: ChatPrompt, **kwargs) -> AsyncIterator[BaseMessage]:
        yield await self._ainvoke(prompt, **kwargs)

    # Transform

    @final
    @override
    def transform(self, input: Iterator[LLMInput], **kwargs) -> Iterator[BaseMessage]:
        pass

    def _transform(self, prompts: Iterator[ChatPrompt], **kwargs) -> Iterator[BaseMessage]:
        pass

    # Async Transform

    @final
    @override
    async def atransform(self, input: AsyncIterator[LLMInput], **kwargs) -> AsyncIterator[BaseMessage]:
        pass

    async def _atransform(self, prompts: AsyncIterator[ChatPrompt], **kwargs) -> AsyncIterator[BaseMessage]:
        pass