"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/base.py
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator, Optional, Self, Sequence

class Channel[Value, Update, State](ABC):
    @property
    @abstractmethod
    def ValueType(self) -> Any:
        """
        The type of the value stored in the channel.
        """

    @property
    @abstractmethod
    def UpdateType(self) -> Any:
        """
        The type of the update received by the channel.
        """

    @abstractmethod
    @contextmanager
    def from_checkpoint(self, state: Optional[State], **kwargs) -> Generator[Self, None, None]:
        """
        Return a new identical channel, optionally initialized from a checkpoint state.
        If the checkpoint state contains complex data structures, they should be copied.
        """

    @asynccontextmanager
    async def afrom_checkpoint(self, state: Optional[State], **kwargs) -> AsyncGenerator[Self, None, None]:
        """
        Return a new identical channel, optionally initialized from a checkpoint state.
        If the checkpoint state contains complex data structures, they should be copied.
        """
        with self.from_checkpoint(state, **kwargs) as channel:
            yield channel

    @abstractmethod
    def checkpoint(self) -> Optional[State]:
        """
        Return a serializable representation of the channel's current state.
        Raises EmptyChannelError if the channel is empty (never updated yet), or doesn't support checkpoints.
        """

    @abstractmethod
    def get(self) -> Optional[Value]:
        """
        Return the current value of the channel.
        Raises EmptyChannelError if the channel is empty (never updated yet).
        """

    @abstractmethod
    def update(self, values: Sequence[Update]) -> bool:
        """
        Update the channel's value with the given sequence of updates.
        The order of the updates in the sequence is arbitrary.
        This method is called by Pregel for all channels at the end of each step.
        If there are no updates, it is called with an empty sequence.
        Raises InvalidUpdateError if the sequence of updates is invalid.
        Returns True if the channel was updated, False otherwise.
        """

    def consume(self) -> bool:
        """
        Mark the current value of the channel as consumed. By default, no-op.
        This is called by Pregel before the start of the next step, for all
        channels that triggered a node. If the channel was updated, return True.
        """
        return False