"""
Credit to LangGraph -
https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/types.py
https://github.com/langchain-ai/langgraph/tree/main/langgraph/constants.py
"""

from collections import deque
from typing import Any, Literal, NamedTuple, Optional, TYPE_CHECKING, TypedDict, Union

from flowstack.core import Component

if TYPE_CHECKING:
    from flowstack.flows.checkpoints.base import CheckpointMetadata

PregelData = Union[Any, dict[str, Any]]
ChannelVersion = Union[int, float, str]
All = Literal['*']

StreamMode = Literal['values', 'updates', 'debug']
"""
How the stream method should emit outputs.

- 'values': Emit all values of the state for each step.
- 'updates': Emit only the node name(s) and updates that were returned by the node(s) **after** each step.
- 'debug': Emit debug events for each step.
"""

class RetryPolicy(NamedTuple):
    """
    Configuration for retrying nodes.
    """

class PregelTaskMetadata(TypedDict, total=False):
    step: int
    node: str
    triggers: list[str]
    task_idx: int

class PregelTaskDescription(NamedTuple):
    name: str
    input: Any

class PregelExecutableTask(NamedTuple):
    name: str
    input: Any
    process: Component
    writes: deque[tuple[str, Any]]
    trigger: list[str]
    id: str
    metadata: PregelTaskMetadata
    config: dict[str, Any]
    retry_policy: Optional[RetryPolicy] = None

class StateSnapshot(NamedTuple):
    values: PregelData
    """Current values of channels."""

    next: tuple[str]
    """Nodes to execute in the next step, if any."""

    metadata: 'CheckpointMetadata'
    """Metadata associated with this snapshot."""

    created_at: Optional[str]
    """Timestamp of snapshot creation."""

    config: dict[str, Any]
    """Config used to fetch this snapshot."""

    parent_config: Optional[dict[str, Any]] = None
    """Config used to fetch the parent snapshot, if any."""

class Send:
    """A message or packet to send to a specific node in the graph.

    The `Send` class is used within a `StateFlow`'s conditional edges to dynamically
    route states to different nodes based on certain conditions. This enables
    creating "map-reduce" like workflows, where a node can be invoked multiple times
    in parallel on different states, and the results can be aggregated back into the
    main graph's state.

    Attributes:
        node (str): The name of the target node to send the message to.
        arg (Any): The state or message to send to the target node.

    Examples:
        >> class OverallState(TypedDict):
        ..     subjects: list[str]
        ..     jokes: Annotated[list[str], operator.add]
        ..
        >> def continue_to_jokes(state: OverallState):
        ..     return [Send("generate_joke", {"subject": s}) for s in state['subjects']]
        ..
        >> builder = StateGraph(OverallState)
        >> builder.add_node("generate_joke", lambda state: {"jokes": [f"Joke about {state['subject']}"]})
        >> builder.add_conditional_edges(START, continue_to_jokes)
        >> builder.add_edge("generate_joke", END)
        >> graph = builder.compile()
        >> graph.invoke({"subjects": ["cats", "dogs"]})
        {'subjects': ['cats', 'dogs'], 'jokes': ['Joke about cats', 'Joke about dogs']}
    """

    def __init__(self, node: str, arg: Any):
        """
        Initialize a new instance of the Send class.

        Args:
            node (str): The name of the target node to send the message to.
            arg (Any): The state or message to send to the target node.
        """
        self.node = node
        self.arg = arg

    def __hash__(self) -> int:
        return hash((self.node, self.arg))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Send) and
            self.node == other.node
            and self.arg == other.arg
        )

    def __repr__(self) -> str:
        return f'Send(node={self.node!r}, arg={self.arg!r})'