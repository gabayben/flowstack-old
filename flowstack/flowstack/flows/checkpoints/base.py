from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Iterator, Literal, NamedTuple, Optional, TypeVar, TypedDict

from flowstack.flows import Channel, ChannelVersion, Send
from flowstack.flows.serde import JsonPlusSerializer, Serializer

_V = TypeVar('_V', int, float, str)
PendingWrite = tuple[str, str, Any]

class TaskInfo(TypedDict, total=False):
    status: Literal['scheduled', 'success', 'error']

class CheckpointMetadata(TypedDict, total=False):
    """
    Metadata associated with a checkpoint.
    """

    source: Literal['input', 'loop', 'update']
    """
    The source of the checkpoint.
    - "input": The checkpoint was created from an input to invoke/stream.
    - "loop": The checkpoint was created from inside the pregel loop.
    - "update": The checkpoint was created from a manual state update.
    """

    step: int
    """
    The step number of the checkpoint.
    -1 for the first "input" checkpoint.
    0 for the first "loop" checkpoint.
    ... for the nth checkpoint afterwards.
    """

    writes: dict[str, Any]
    """
    The writes that were made between the previous checkpoint and this one.
    Mapping from node name to writes emitted by that node.
    """

    score: Optional[int]
    """
    The score of the checkpoint.
    The score can be used to mark a checkpoint as "good".
    """

class Checkpoint(TypedDict):
    version: int
    """
    The version of the checkpoint format. Currently 1.
    """

    id: str
    """
    The ID of the checkpoint. This is both unique and monotonically 
    increasing, so can be used for sorting checkpoints from first to last.
    """

    timestamp: str
    """
    The timestamp of the checkpoint in ISO 8601 format.
    """

    channel_values: dict[str, Any]
    """
    The values of the channels at the time of the checkpoint.
    Mapping from channel name to channel snapshot value.
    """

    channels_versions: dict[str, ChannelVersion]
    """
    The versions of the channels at the time of the checkpoint.

    The keys are channel names and the values are the logical time step
    at which the channel was last updated.
    """

    versions_seen: dict[str, dict[str, ChannelVersion]]
    """
    Map from node ID to map from channel name to version seen.

    This keeps track of the versions of the channels that each node has seen.

    Used to determine which nodes to execute next.
    """

    pending_sends: list[Send]
    """
    List of packets sent to nodes but not yet processed.
    Cleared by the next checkpoint.
    """

    current_tasks: dict[str, TaskInfo]
    """
    Map from task ID to task info.
    """

class CheckpointTuple(NamedTuple):
    """
    A tuple containing a checkpoint and its associated data.
    """

    checkpoint: Checkpoint
    metadata: CheckpointMetadata
    config: dict[str, Any]
    pending_writes: Optional[list[PendingWrite]] = None

class CheckpointConfigSpec(TypedDict):
    id: str
    annotation: Any
    default: Any

class Checkpointer(ABC):
    """Base class for creating a flow checkpointer.

    Checkpointers allow builders to persist their state
    within and across multiple interactions.

    Attributes:
        serde (Serializer): Serializer for encoding/decoding checkpoints.

    Note:
        When creating a custom checkpointer, consider implementing async
        versions to avoid blocking the main thread.
    """

    serde: Serializer

    @property
    def config_specs(self) -> list[CheckpointConfigSpec]:
        return [
            CheckpointConfigSpec(
                id='thread_id',
                annotation=str,
                default=None
            ),
            CheckpointConfigSpec(
                id='thread_ts',
                annotation=str,
                default=None
            )
        ]

    def __init__(
        self,
        *,
        serde: Optional[Serializer] = None
    ):
        self.serde = serde or JsonPlusSerializer()

    @abstractmethod
    def get_many(
        self,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> Iterator[CheckpointTuple]:
        """
        List checkpoints that match the given criteria.

        Args:
            filter (Optional[Dict[str, Any]]): Additional filtering criteria.
            limit (Optional[int]): Maximum number of checkpoints to return.
            kwargs: Configuration.

        Returns:
            Iterator[CheckpointTuple]: Iterator of matching checkpoint tuples.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """

    @abstractmethod
    async def aget_many(
        self,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[CheckpointTuple]:
        """
        List checkpoints that match the given criteria.

        Args:
            filter (Optional[Dict[str, Any]]): Additional filtering criteria.
            limit (Optional[int]): Maximum number of checkpoints to return.
            kwargs: Configuration.

        Returns:
            Iterator[CheckpointTuple]: Iterator of matching checkpoint tuples.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """

    @abstractmethod
    def get(self, **kwargs) -> Optional[CheckpointTuple]:
        """
        Fetch a checkpoint.
        """

    @abstractmethod
    async def aget(self, **kwargs) -> Optional[CheckpointTuple]:
        """
        Fetch a checkpoint.
        """

    @abstractmethod
    def put(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        """
        Store a checkpoint with its configuration and metadata.

        Args:
            checkpoint (Checkpoint): The checkpoint to store.
            metadata (CheckpointMetadata): Additional metadata for the checkpoint.
            kwargs: Configuration

        Returns:
            dict[str, Any]: Updated configuration after storing the checkpoint.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """

    @abstractmethod
    async def aput(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        """
        Store a checkpoint with its configuration and metadata.

        Args:
            checkpoint (Checkpoint): The checkpoint to store.
            metadata (CheckpointMetadata): Additional metadata for the checkpoint.
            kwargs: Configuration

        Returns:
            dict[str, Any]: Updated configuration after storing the checkpoint.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """

    @abstractmethod
    def put_writes(
        self,
        writes: list[tuple[str, Any]],
        task_id: str,
        **kwargs
    ) -> None:
        """
        Store intermediate writes linked to a checkpoint.

        Args:
            writes (List[Tuple[str, Any]]): List of writes to store.
            task_id (str): Identifier for the task creating the writes.
            kwargs: Configuration.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """

    @abstractmethod
    async def aput_writes(
        self,
        writes: list[tuple[str, Any]],
        task_id: str,
        **kwargs
    ) -> None:
        """
        Store intermediate writes linked to a checkpoint.

        Args:
            writes (List[Tuple[str, Any]]): List of writes to store.
            task_id (str): Identifier for the task creating the writes.
            kwargs: Configuration.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """

    def get_next_version[V: (int, float, str)](
        self,
        channel: Channel,
        current: Optional[V] = None
    ) -> V:
        return current + 1 if current is not None else 1