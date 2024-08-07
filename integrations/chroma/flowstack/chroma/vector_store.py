import json
import logging
import math
import os.path
from typing import Any, Generator, Optional, Unpack

import chromadb
from chromadb.api.models.Collection import Collection
import fsspec

from flowstack.artifacts import Artifact, artifact_registry
from flowstack.stores import VectorStore, VectorStoreQuery, VectorStoreQueryResult
from flowstack.typing import Embedding, FilterCondition, FilterOperator, MetadataFilter, MetadataFilters
from flowstack.utils.func import tzip
from flowstack.utils.string import truncate_text
from flowstack.utils.threading import run_async

MAX_CHUNK_SIZE = 41665
logger = logging.getLogger(__name__)

class ChromaVectorStore(VectorStore):
    _collection: Collection
    collection_name: Optional[str]
    collection_kwargs: dict[str, Any]
    host: Optional[str]
    port: Optional[int]
    headers: Optional[dict[str, str]]
    ssl: bool
    stores_text: bool = True
    is_flat_metadata: bool = True

    def __init__(
        self,
        collection: Optional[Collection] = None,
        collection_name: Optional[str] = None,
        collection_kwargs: Optional[dict[str, Any]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        headers: Optional[dict[str, str]] = None,
        ssl: bool = False,
        fs: Optional[fsspec.AbstractFileSystem] = None
    ):
        self.collection_name = collection_name
        self.collection_kwargs = collection_kwargs or {}
        self.host = host
        self.port = port
        self.headers = headers
        self.ssl = ssl
        if collection is None:
            client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                headers=self.headers,
                ssl=self.ssl
            )
            self._collection = client.get_or_create_collection(
                name=collection_name,
                **collection_kwargs
            )
        else:
            self._collection = collection
        self._fs: fsspec.AbstractFileSystem = fs or fsspec.filesystem('file')

    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> None:
        data = self._collection.get(offset=offset, limit=limit)
        fs = fs or self._fs
        dirname = os.path.dirname(path)
        if not fs.exists(dirname):
            fs.makedirs(dirname)
        with fs.open(path, 'w') as f:
            json.dump(data, f)

    def retrieve(self, **query: Unpack[VectorStoreQuery]) -> VectorStoreQueryResult:
        query.setdefault('similarity_top_k', 1)
        where = _to_chroma_filters(query['filters']) if query['filters'] else {}
        if not query['query_embedding']:
            return self._get(where, query['similarity_top_k'], **query)
        return self._retrieve(query['query_embedding'], where, query['similarity_top_k'], **query)

    def _retrieve(
        self,
        query_embedding: Embedding,
        where: dict,
        n_results: int,
        **kwargs
    ) -> VectorStoreQueryResult:
        result = self._collection.query(
            query_embeddings=query_embedding,
            where=where,
            n_results=n_results,
            **kwargs
        )

        logger.debug(f'> Top {len(result['documents'][0])} artifacts:')
        artifacts: list[Artifact] = []
        ids: list[str] = []
        similarities: list[float] = []

        for artifact_id, text, metadata, distance in tzip(
            result['ids'][0],
            result['documents'][0],
            result['metadatas'][0],
            result['distances'][0]
        ):
            artifact = artifact_registry.deserialize(dict(metadata))
            artifact.set_content(text)
            similarity = math.exp(-distance)

            artifacts.append(artifact)
            ids.append(artifact_id)
            similarities.append(similarity)
            logger.debug(
                f"> [Artifact {artifact_id}] [Similarity score: {similarity} - using query()] "
                f"{truncate_text(str(text), 100)}"
            )

        return VectorStoreQueryResult(artifacts=artifacts, ids=ids, similarities=similarities)

    def _get(
        self,
        where: dict,
        limit: Optional[int],
        **kwargs
    ) -> VectorStoreQueryResult:
        result = self._collection.get(where=where, limit=limit, **kwargs)

        logger.debug(f'> Top {len(result['documents'])} artifacts:')
        artifacts: list[Artifact] = []
        ids: list[str] = []

        if not result['ids']:
            result['ids'] = []

        for artifact_id, text, metadata in tzip(
            result['ids'],
            result['documents'],
            result['metadatas']
        ):
            artifact = artifact_registry.deserialize(metadata)
            artifact.set_content(text)

            artifacts.append(artifact)
            ids.append(artifact_id)
            logger.debug(
                f"> [Artifact {artifact_id}] [Similarity score: N/A - using get()] "
                f"{truncate_text(str(text), 100)}"
            )

        return VectorStoreQueryResult(artifacts=artifacts, ids=ids)

    async def aretrieve(self, **query: Unpack[VectorStoreQuery]) -> VectorStoreQueryResult:
        return await run_async(self.retrieve, **query)

    def insert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        all_ids = []
        chunks_list = _chunks_list(artifacts, MAX_CHUNK_SIZE)
        for chunks in chunks_list:
            texts = []
            ids = []
            embeddings = []
            metadatas = []
            for chunk in chunks:
                if not chunk.embedding:
                    raise ValueError(f'No embedding set for {chunk.name or chunk.id}.')
                texts.append(str(chunk))
                ids.append(chunk.id)
                embeddings.append(chunk.embedding)
                metadatas.append(chunk.model_dump(exclude={*chunk._content_keys, 'embedding'}))
            self._collection.add(
                documents=texts,
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            all_ids.extend(ids)
        return all_ids

    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        return await run_async(self.insert, artifacts, **kwargs)

    def delete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        self._collection.delete(
            ids=artifact_ids or [],
            where=_to_chroma_filters(filters) if filters else {}
        )

    async def adelete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        await run_async(self.delete, artifact_ids, filters, **kwargs)

    def delete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        self._collection.delete(where={'ref_id': ref_artifact_id})

    async def adelete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        await run_async(self.delete_ref, ref_artifact_id, **kwargs)

    def clear(self, **kwargs) -> None:
        self._collection.delete(ids=self._collection.get()['ids'])

    async def aclear(self, **kwargs) -> None:
        await run_async(self.clear, **kwargs)

def _filter_condition(condition: FilterCondition) -> str:
    return {
        FilterCondition.AND: '$and',
        FilterCondition.OR: '$or'
    }[condition]

def _filter_operator(operator: FilterOperator) -> str:
    supported_operators = {
        FilterOperator.EQ: '$eq',
        FilterOperator.NE: '$ne',
        FilterOperator.GT: '$gt',
        FilterOperator.GTE: '$gte',
        FilterOperator.LT: '$lt',
        FilterOperator.LTE: '$lte',
        FilterOperator.IN: '$in',
        FilterOperator.NIN: '$nin'
    }
    if operator not in supported_operators:
        raise ValueError(f'Filter operator {operator} not supported.')
    return supported_operators[operator]

def _to_chroma_filters(standard_filters: MetadataFilters) -> dict:
    filters = {}
    filters_list = []
    condition = standard_filters.condition or FilterCondition.AND
    condition = _filter_condition(condition)
    if standard_filters.filters:
        for filter_ in standard_filters.filters:
            if isinstance(filter_, MetadataFilter):
                filters_list.append({
                    filter_.key: {
                        _filter_operator(filter_.operator): filter_.value
                    }
                })
            else:
                filters_list.append(_to_chroma_filters(filter_))
    if len(filters_list) == 1:
        return filters_list[0]
    elif len(filters_list) > 1:
        filters[condition] = filters_list
    return filters

def _chunks_list(
    artifacts: list[Artifact],
    max_chunk_size: int
) -> Generator[list[Artifact], None, None]:
    for i in range(0, len(artifacts), max_chunk_size):
        yield artifacts[i : i + max_chunk_size]