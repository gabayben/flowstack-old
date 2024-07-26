"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/__init__.py
"""

from functools import partial
from typing import AsyncIterator, Iterator, Mapping, Optional, Sequence, Union, final

from pydantic import Field

from flowstack.core import SerializableComponent
from flowstack.flows.channels import Channel
from flowstack.flows.checkpoints import Checkpointer
from flowstack.flows.typing import PregelData, StreamMode
from flowstack.typing import Effect, Effects

class Pregel(SerializableComponent[PregelData, PregelData]):
    channels: Mapping[str, Channel] = Field(default_factory=dict)
    input_channels: Union[str, Sequence[str]]
    output_channels: Union[str, Sequence[str]]
    stream_channels: Optional[Union[str, Sequence[str]]] = None
    checkpointer: Optional[Checkpointer] = None
    stream_mode: StreamMode = 'values'

    @final
    def run(self, data: PregelData, **kwargs) -> Effect[PregelData]:
        return Effects.From(
            invoke=partial(self._invoke, data, **kwargs),
            ainvoke=partial(self._ainvoke, data, **kwargs),
            iter_=partial(self._stream, data, **kwargs),
            aiter_=partial(self._astream, data, **kwargs)
        )

    def _invoke(self, data: PregelData, **kwargs) -> PregelData:
        pass

    async def _ainvoke(self, data: PregelData, **kwargs) -> PregelData:
        pass

    def _stream(self, data: PregelData, **kwargs) -> Iterator[PregelData]:
        pass

    async def _astream(self, data: PregelData, **kwargs) -> AsyncIterator[PregelData]:
        pass