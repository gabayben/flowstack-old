from typing import Any

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