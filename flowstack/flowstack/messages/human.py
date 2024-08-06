from typing import Any, Literal

from flowstack.messages import BaseMessage, MessageContent, MessageType

class HumanMessage(BaseMessage):
    message_type: Literal[MessageType.HUMAN]

    def __init__(
        self,
        content: MessageContent,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            message_type=MessageType.HUMAN,
            content=content,
            metadata=metadata,
            **kwargs
        )