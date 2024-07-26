"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/read.py
"""

from typing import Any, Callable, Optional, Sequence, Union

from flowstack.core import Component
from flowstack.flows.constants import READ_KEY

READ_TYPE = Callable[[Union[str, Sequence[str]], bool], Union[Any, dict[str, Any]]]

class ChannelRead(Component[Any, Union[str, dict[str, Any]]]):
    def __init__(
        self,
        channels: Union[str, Sequence[str]],
        *,
        mapper: Optional[Callable[[Any], Any]] = None,
        tags: Optional[list[str]] = None,
        fresh: bool = False
    ):
        self._channels = channels
        self._mapper = mapper
        self._tags = tags
        self._fresh = fresh

    def run(self, _: Any, **kwargs) -> Union[str, dict[str, Any]]:
        return self.do_read(
            self._channels,
            mapper=self._mapper,
            fresh=self._fresh,
            **kwargs
        )

    @staticmethod
    def do_read(
        channels: Union[str, Sequence[str]],
        *,
        mapper: Optional[Callable[[Any], Any]] = None,
        fresh: bool = False,
        **config
    ) -> Union[Any, dict[str, Any]]:
        try:
            read: READ_TYPE = config[READ_KEY]
        except KeyError:
            raise RuntimeError(
                'Not configured with a read function.'
                'Make sure to call in the context of a Pregel process.'
            )
        if mapper:
            return mapper(read(channels, fresh))
        return read(channels, fresh)