from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator, Optional, final, override

from flowstack.artifacts import Artifact
from flowstack.core import Component
from flowstack.typing import Embedding
from flowstack.utils.threading import run_async

Embedder = Component[list[Artifact], list[Artifact]]

class BaseEmbedder(Embedder, ABC):
    """
    Base text embedder.
    """

    # Sync

    @final
    def invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    def _invoke(self, artifacts: list[Artifact], **kwargs) -> list[Optional[Embedding]]:
        pass

    # Async

    @final
    @override
    async def ainvoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, artifacts: list[Artifact], **kwargs) -> list[Optional[Embedding]]:
        return await run_async(self._invoke, artifacts, **kwargs)

    # Stream

    @final
    @override
    def stream(self, artifacts: list[Artifact], **kwargs) -> Iterator[list[Artifact]]:
        pass

    def _stream(self, artifacts: list[Artifact], **kwargs) -> Iterator[list[Optional[Embedding]]]:
        pass

    # Async Stream

    @final
    @override
    async def astream(self, artifacts: list[Artifact], **kwargs) -> AsyncIterator[list[Artifact]]:
        pass

    async def _astream(self, artifacts: list[Artifact], **kwargs) -> AsyncIterator[list[Optional[Embedding]]]:
        pass

    # Transform

    @final
    @override
    def transform(self, artifacts: Iterator[list[Artifact]], **kwargs) -> Iterator[list[Artifact]]:
        pass

    def _transform(self, artifacts: Iterator[list[Artifact]], **kwargs) -> Iterator[list[Optional[Embedding]]]:
        pass

    # Async Transform

    @final
    @override
    def atransform(self, artifacts: AsyncIterator[list[Artifact]], **kwargs) -> AsyncIterator[list[Artifact]]:
        pass

    async def _atransform(self, artifacts: AsyncIterator[list[Artifact]], **kwargs) -> AsyncIterator[list[Optional[Embedding]]]:
        pass