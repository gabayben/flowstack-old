from dataclasses import dataclass, field
import json
import os.path
from typing import Any, Optional, Unpack

from dataclasses_json import DataClassJsonMixin
import fsspec

from flowstack.artifacts import Artifact
from flowstack.stores import VectorStore, VectorStoreQuery, VectorStoreQueryResult
from flowstack.typing import Embedding, MetadataFilters

@dataclass
class SimpleVectorStoreData(DataClassJsonMixin):
    embeddings: dict[str, Embedding] = field(default_factory=dict)
    ref_id_mapping: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

class SimpleVectorStore(VectorStore):
    def __init__(
        self,
        data: Optional[SimpleVectorStoreData] = None,
        fs: Optional[fsspec.AbstractFileSystem] = None
    ):
        self._data: SimpleVectorStoreData = data or SimpleVectorStoreData()
        self._fs: fsspec.AbstractFileSystem = fs or fsspec.filesystem('file')

    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> None:
        fs = fs or self._fs
        dirname = os.path.dirname(path)
        if not fs.exists(dirname):
            fs.makedirs(dirname)
        with fs.open(path, 'w') as f:
            json.dump(self._data.to_dict(), f)

    def retrieve(self, **query: Unpack[VectorStoreQuery]) -> VectorStoreQueryResult:
        pass

    async def aretrieve(self, **query: Unpack[VectorStoreQuery]) -> VectorStoreQueryResult:
        pass

    def insert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    def delete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    async def adelete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    def delete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    async def adelete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    def clear(self, **kwargs) -> None:
        pass

    async def aclear(self, **kwargs) -> None:
        pass