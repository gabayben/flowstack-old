"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/managed/few_shot.py
"""

from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, AsyncIterator, Callable, Generator, Iterator, Optional, Self, Sequence, TYPE_CHECKING, Union, override

from flowstack.flows import AsyncChannelManager, ChannelManager, ConfiguredManagedValue, ManagedValue, PregelTaskDescription
from flowstack.flows.channels.utils import read_channels

if TYPE_CHECKING:
    from flowstack.flows.pregel.graph import Pregel

_MetadataFilter = Union[dict[str, Any], Callable[[dict[str, Any]], dict[str, Any]]]

class FewShotExamples[Value](ManagedValue[Sequence[Value]]):
    examples: list[Value]

    @property
    def _metadata_filter_dict(self) -> dict[str, Any]:
        if callable(self._metadata_filter):
            return self._metadata_filter(self.config)
        return self._metadata_filter

    def __init__(
        self,
        graph: 'Pregel',
        limit: int = 5,
        metadata_filter: Optional[_MetadataFilter] = None,
        **config
    ):
        super().__init__(graph, **config)
        self._limit = limit
        self._metadata_filter: _MetadataFilter = metadata_filter or {}

    @classmethod
    @contextmanager
    @override
    def enter(cls, graph: 'Pregel', **kwargs) -> Generator[Self, None, None]:
        with super().enter(graph, **kwargs) as value:
            value.examples = list(value.iter())
            yield value

    def iter(self, score: int = 1) -> Iterator[Value]:
        if self.graph.checkpointer:
            for saved in self.graph.checkpointer.get_many(
                filters={
                    'score': score,
                    **self._metadata_filter_dict
                },
                limit=self._limit
            ):
                with ChannelManager(
                    self.graph.channels,
                    saved.checkpoint,
                    **saved.config
                ) as channels:
                    yield read_channels(channels, self.graph.output_channels)

    @classmethod
    @asynccontextmanager
    @override
    async def aenter(cls, graph: 'Pregel', **kwargs) -> AsyncGenerator[Self, None, None]:
        async with super().aenter(graph, **kwargs) as value:
            value.examples = [chunk async for chunk in value.aiter()]
            yield value

    async def aiter(self, score: int = 1) -> AsyncIterator[Value]:
        if self.graph.checkpointer:
            async for saved in self.graph.checkpointer.aget_many( #type: ignore
                filters={
                    'score': score,
                    **self._metadata_filter
                },
                limit=self._limit
            ):
                async with AsyncChannelManager(
                    self.graph.channels,
                    saved.checkpoint,
                    **saved.config
                ) as channels:
                    yield read_channels(channels, self.graph.output_channels)

    @classmethod
    def configure(
        cls,
        limit: int = 5,
        metadata_filter: Optional[_MetadataFilter] = None
    ):
        return ConfiguredManagedValue(
            cls,
            {
                'k': limit,
                'metadata_filter': metadata_filter
            }
        )

    def __call__(self, step: int, task: PregelTaskDescription) -> Sequence[Value]:
        return self.examples