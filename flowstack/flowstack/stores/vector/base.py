from abc import ABC, abstractmethod
from typing import Optional, Unpack

import fsspec

from flowstack.artifacts import Artifact
from flowstack.stores import VectorStoreQuery, VectorStoreQueryResult
from flowstack.typing import MetadataFilters

class VectorStore(ABC):
    @abstractmethod
    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    def retrieve(self, **query: Unpack[VectorStoreQuery]) -> VectorStoreQueryResult:
        pass

    @abstractmethod
    async def aretrieve(self, **query: Unpack[VectorStoreQuery]) -> VectorStoreQueryResult:
        pass

    @abstractmethod
    def insert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    @abstractmethod
    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    @abstractmethod
    def delete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def adelete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    def delete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    async def adelete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    def clear(self, **kwargs) -> None:
        pass

    @abstractmethod
    async def aclear(self, **kwargs) -> None:
        pass