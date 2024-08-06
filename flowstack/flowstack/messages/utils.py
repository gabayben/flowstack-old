from typing import Union

from flowstack.messages import BaseMessage, HumanMessage, MessageContent

def coerce_to_messages(content: Union[MessageContent, list[BaseMessage]]) -> list[BaseMessage]:
    if isinstance(content, list) and isinstance(content[0], BaseMessage):
        return content
    return [HumanMessage(content)]