"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/read.py
"""

from typing import Any, Callable, Mapping, Optional, Sequence, Union, override

from pydantic import Field

from flowstack.core import Component, ComponentLike, DecoratorBase, Passthrough, Sequential
from flowstack.flows.managed import ManagedValueSpec
from flowstack.flows.pregel import ChannelWrite
from flowstack.flows.typing import RetryPolicy

DEFAULT_BOUND = Passthrough()

class PregelNode(DecoratorBase):
    channels: Union[Sequence[str], Mapping[str, Union[str, ManagedValueSpec]]]
    triggers: list[str] = Field(default_factory=list)
    bound: Component[Any, Any] = Field(default=DEFAULT_BOUND)
    writers: list[Component] = Field(default_factory=list)
    mapper: Optional[Callable[[Any], Any]] = None
    retry_policy: Optional[RetryPolicy] = None
    tags: Optional[list[str]] = None

    def __init__(
        self,
        channels: Union[Sequence[str], Mapping[str, Union[str, ManagedValueSpec]]],
        triggers: list[str] = [],
        bound: Component[Any, Any] = DEFAULT_BOUND,
        writers: list[Component] = [],
        mapper: Optional[Callable[[Any], Any]] = None,
        retry_policy: Optional[RetryPolicy] = None,
        tags: Optional[list[str]] = None,
        **kwargs
    ):
        super().__init__(
            channels=channels,
            triggers=triggers,
            bound=bound,
            writers=writers,
            mapper=mapper,
            retry_policy=retry_policy,
            tags=tags,
            **kwargs
        )

    @override
    def __or__(self, other: ComponentLike[Any, Any]) -> 'PregelNode':
        if ChannelWrite.is_writer(other):
            return self.model_copy(update=dict(writers=[*self.writers, other]))
        elif self.bound is DEFAULT_BOUND:
            return self.model_copy(update=dict(bound=other))
        return self.model_copy(update=dict(bound=self.bound | other))

    @override
    def __ror__(self, other: ComponentLike[Any, Any]) -> Component[Any, Any]:
        raise NotImplementedError()

    def get_node(self) -> Optional[Component[Any, Any]]:
        writers = self.get_writers()
        if self.bound is DEFAULT_BOUND and not writers:
            return None
        elif self.bound is DEFAULT_BOUND and len(writers) == 1:
            return writers[-1]
        elif self.bound is DEFAULT_BOUND:
            return Sequential(*writers)
        elif writers:
            return Sequential(self.bound, *writers)
        return self.bound

    def get_writers(self) -> list[Component]:
        """Get writers with optimizations applied."""
        writers = self.writers.copy()
        while (
            len(writers) > 1 and
            isinstance(writers[-2], ChannelWrite) and
            isinstance(writers[-1], ChannelWrite)
        ):
            writers[-2] = ChannelWrite(
                writes=writers[-2].writes + writers[-1].writes,
                required_channels=writers[-2].required_channels,
                tags=writers[-2].tags
            )
            writers.pop()
        return writers