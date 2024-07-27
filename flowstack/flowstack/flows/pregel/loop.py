"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/loop.py
"""

from collections import deque
import concurrent.futures
from typing import Any, Callable, Literal, Mapping, Optional, Sequence, TYPE_CHECKING

from flowstack.flows.channels import Channel
from flowstack.flows.checkpoints import Checkpoint, CheckpointMetadata, Checkpointer, PendingWrite
from flowstack.flows.checkpoints.utils import copy_checkpoint, create_checkpoint
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
    put_checkpoint_future: concurrent.futures.Future

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

    def _put_checkpoint(self, metadata: CheckpointMetadata) -> None:
        # assign step
        metadata['step'] = self.step
        # bail if no checkpointer
        if self._put_after_previous is not None:
            # create new checkpoint
            self.checkpoint_metadata = metadata
            self.checkpoint = create_checkpoint(
                self.checkpoint,
                self.channels,
                self.step,
                # child graphs keep at most one checkpoint per parent checkpoint
                # this is achieved by writing child checkpoints as progress is made
                # (so that error recovery / resuming from interrupt don't lose work)
                # but doing so always with an id equal to that of the parent checkpoint
                id=self.config.get('thread_ts') if self.is_nested else None
            )
            # save it, without blocking
            # if there's a previous checkpoint save in progress, wait for it
            # ensuring checkpointers receive checkpoints in order
            self.put_checkpoint_future = self.submit(
                self._put_after_previous,
                getattr(self, 'put_checkpoint_future', None),
                copy_checkpoint(self.checkpoint),
                self.checkpoint_metadata,
                self.checkpoint_config
            )
            self.checkpoint_config = {**self.checkpoint_config, 'thread_ts': self.checkpoint['id']}
            # produce debug output
            # TODO
        # increment step
        self.step += 1