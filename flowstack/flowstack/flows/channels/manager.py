"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/manager.py
"""

from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Mapping

from flowstack.flows.channels import Channel
from flowstack.flows.checkpoints import Checkpoint

@contextmanager
def ChannelManager(
    channels: Mapping[str, Channel],
    checkpoint: Checkpoint,
    **kwargs
) -> Generator[Mapping[str, Channel], None, None]:
    """
    Manage channels for the lifetime of a Pregel invocation (multiple steps).
    """
    with ExitStack() as stack:
        yield {
            name: stack.enter_context(
                channel.from_checkpoint(checkpoint['channel_values'].get(name), **kwargs)
            )
            for name, channel in channels.items()
        }

@asynccontextmanager
async def AsyncChannelManager(
    channels: Mapping[str, Channel],
    checkpoint: Checkpoint,
    **kwargs
) -> AsyncGenerator[Mapping[str, Channel], None, None]:
    """
    Manage channels for the lifetime of a Pregel invocation (multiple steps).
    """
    async with AsyncExitStack() as stack:
        yield {
            name: await stack.enter_async_context(
                channel.afrom_checkpoint(checkpoint['channel_values'].get(name), **kwargs)
            )
            for name, channel in channels.items()
        }