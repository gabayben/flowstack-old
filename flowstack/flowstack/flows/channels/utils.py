"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/io.py
"""

from typing import Any, Mapping, Optional, Sequence, Union

from flowstack.flows.channels import Channel
from flowstack.flows.errors import EmptyChannelError

def read_channel(
    channels: Mapping[str, Channel],
    chan: str,
    *,
    catch: bool = True,
    return_exception: bool = False
) -> Optional[Any]:
    try:
        return channels[chan].get()
    except EmptyChannelError as e:
        if return_exception:
            return e
        elif catch:
            return None
        raise e

def read_channels(
    channels: Mapping[str, Channel],
    select: Union[str, Sequence[str]],
    *,
    skip_empty: bool = True
) -> Union[Any, dict[str, Any]]:
    if isinstance(select, str):
        return read_channel(channels, select)
    values: dict[str, Any] = {}
    for chan in select:
        try:
            values[chan] = read_channel(channels, chan, catch=not skip_empty)
        except EmptyChannelError:
            pass
    return values