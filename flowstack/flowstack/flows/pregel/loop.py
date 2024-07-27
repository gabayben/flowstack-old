"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/loop.py
"""

from collections import deque
import concurrent.futures
from typing import Any, Callable, Literal, Mapping, Optional, Sequence, TYPE_CHECKING

from flowstack.flows.channels import Channel
from flowstack.flows.checkpoints import Checkpoint, CheckpointMetadata, Checkpointer, PendingWrite
from flowstack.flows.constants import READ_KEY
from flowstack.flows.managed import ManagedValue
from flowstack.flows.pregel.executor import Submit
from flowstack.flows.typing import PregelExecutableTask

if TYPE_CHECKING:
    from flowstack.flows.pregel.graph import Pregel

INPUT_DONE = object()
INPUT_RESUMING = object()
EMPTY_SEQUENCE = ()

_Status = Literal['pending', 'done', 'interrupt_before', 'interrupt_after', 'out_of_steps']
_PutWrites = Callable[
    [
        Sequence[tuple[str, Any]],
        str,
        dict[str, Any]
    ],
    Any
]
_PutAfterPrevious = Callable[
    [
        Sequence[tuple[str, Any]],
        str,
        dict[str, Any],
        Optional[concurrent.futures.Future]
    ],
    Any
]

class PregelLoopBase[V]:
    graph: 'Pregel'
    channels: Mapping[str, Channel]
    managed: dict[str, ManagedValue]
    tasks: Sequence[PregelExecutableTask]
    input: Optional[Any]
    stream: deque[tuple[str, Any]]
    submit: Submit
    config: dict[str, Any]

    step: int
    stop: int
    status: _Status
    is_nested: bool

    checkpoint: Checkpoint
    checkpoint_metadata: CheckpointMetadata
    checkpoint_pending_writes: list[PendingWrite]
    checkpoint_config: dict[str, Any]

    checkpointer: Optional[Checkpointer]
    get_next_version: Callable[[Optional[V]], V]
    put_writes: Optional[_PutWrites]
    _put_after_previous: Optional[_PutAfterPrevious]

    def __init__(
        self,
        graph: 'Pregel',
        input: Optional[Any],
        checkpointer: Optional[Checkpointer],
        **config
    ):
        self.graph = graph
        self.input = input
        self.stream = deque()
        self.config = config
        self.checkpointer = checkpointer
        self.is_nested = READ_KEY in self.config