import os.path
from typing import Any, Optional, Unpack

import fsspec

from flowstack.stores import Graph, GraphNode, GraphNodeQuery, GraphRelation, GraphStore, GraphTriplet, GraphTripletQuery, VectorStoreQuery
from flowstack.typing import Embedding

class SimpleGraphStore(GraphStore):
    def __init__(
        self,
        graph: Optional[Graph] = None,
        fs: Optional[fsspec.AbstractFileSystem] = None
    ):
        self._graph: Graph = graph or Graph()
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
            f.write(self._graph.model_dump_json())

    def get_schema(self, refresh: bool = False, **kwargs) -> Any:
        pass

    def structured_query(
        self,
        query: str,
        param_map: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        raise NotImplementedError()

    async def astructured_query(
        self,
        query: str,
        param_map: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        raise NotImplementedError()

    def vector_query(self, **query: Unpack[VectorStoreQuery]) -> tuple[list[GraphNode], Embedding]:
        raise NotImplementedError()

    async def avector_query(self, **query: Unpack[VectorStoreQuery]) -> tuple[list[GraphNode], Embedding]:
        raise NotImplementedError()

    def get(self, **query: Unpack[GraphNodeQuery]) -> list[GraphNode]:
        pass

    async def aget(self, **query: Unpack[GraphNodeQuery]) -> list[GraphNode]:
        pass

    def get_triplets(self, **query: Unpack[GraphTripletQuery]) -> list[GraphTriplet]:
        pass

    async def aget_triplets(self, **query: Unpack[GraphTripletQuery]) -> list[GraphTriplet]:
        pass

    def get_rel_map(
        self,
        nodes: list[GraphNode],
        ignore_rels: Optional[list[str]] = None,
        depth: int = 2,
        limit: int = 30,
        **kwargs
    ) -> list[GraphTriplet]:
        pass

    async def aget_rel_map(
        self,
        nodes: list[GraphNode],
        ignore_rels: Optional[list[str]] = None,
        depth: int = 2,
        limit: int = 30,
        **kwargs
    ) -> list[GraphTriplet]:
        pass

    async def aupsert_nodes(self, nodes: list[GraphNode], **kwargs) -> None:
        pass

    def upsert_nodes(self, nodes: list[GraphNode], **kwargs) -> None:
        pass

    def upsert_relations(self, relations: list[GraphRelation], **kwargs) -> None:
        pass

    async def aupsert_relations(self, relations: list[GraphRelation], **kwargs) -> None:
        pass

    def delete(self, **query: Unpack[GraphNodeQuery]) -> None:
        pass

    async def adelete(self, **query: Unpack[GraphNodeQuery]) -> None:
        pass