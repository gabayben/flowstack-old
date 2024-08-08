from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator, Union, final, override

from flowstack.artifacts import Artifact
from flowstack.core import Component
from flowstack.typing import Embedding
from flowstack.utils.threading import run_async

RetrieverInput = Union[str, Embedding, Artifact]
Retriever = Component[RetrieverInput, list[Artifact]]

class BaseRetriever(Retriever, ABC):
    """
    Base retriever.
    """

    # Sync

    @final
    def invoke(self, query: RetrieverInput, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass

    # Async

    @final
    @override
    async def ainvoke(self, query: RetrieverInput, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        return await run_async(self._invoke, query, **kwargs)

    # Batch

    @final
    @override
    def batch(self, queries: list[RetrieverInput], **kwargs) -> list[list[Artifact]]:
        pass

    def _batch(self, queries: list[Artifact], **kwargs) -> list[list[Artifact]]:
        pass

    # Async Batch

    @final
    @override
    async def abatch(self, queries: list[RetrieverInput], **kwargs) -> list[list[Artifact]]:
        pass

    async def _abatch(self, queries: list[Artifact], **kwargs) -> list[list[Artifact]]:
        pass

    # Stream

    @final
    @override
    def stream(self, query: RetrieverInput, **kwargs) -> Iterator[list[Artifact]]:
        pass

    def _stream(self, query: Artifact, **kwargs) -> Iterator[list[Artifact]]:
        pass

    # Async Stream

    @final
    @override
    async def astream(self, query: RetrieverInput, **kwargs) -> AsyncIterator[list[Artifact]]:
        pass

    async def _astream(self, query: Artifact, **kwargs) -> AsyncIterator[list[Artifact]]:
        pass

    # Transform

    @final
    @override
    def transform(self, queries: Iterator[RetrieverInput], **kwargs) -> Iterator[list[Artifact]]:
        pass

    def _transform(self, queries: Iterator[Artifact], **kwargs) -> Iterator[list[Artifact]]:
        pass

    # Async Transform

    @final
    @override
    async def atransform(self, queries: AsyncIterator[RetrieverInput], **kwargs) -> AsyncIterator[list[Artifact]]:
        pass

    async def _atransform(self, queries: AsyncIterator[Artifact], **kwargs) -> AsyncIterator[list[Artifact]]:
        pass