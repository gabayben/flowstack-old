from typing import Optional, Sequence, TypedDict, Union

from langchain_core.runnables import RunnableConfig
from langgraph.pregel import All, StreamMode

class WorkflowOptions(TypedDict, total=False):
    stream_mode: StreamMode
    output_keys: Optional[Union[str, Sequence[str]]]
    interrupt_before: Optional[Union[All, Sequence[str]]]
    interrupt_after: Optional[Union[All, Sequence[str]]]
    debug: Optional[bool]
    config: Optional[RunnableConfig]