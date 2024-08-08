from abc import ABC, abstractmethod

from flowstack.artifacts import Artifact
from flowstack.utils.threading import run_async

class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, **kwargs) -> list[Artifact]:
        pass

    async def aretrieve(self, query: str, **kwargs) -> list[Artifact]:
        return await run_async(self.retrieve, query, **kwargs)