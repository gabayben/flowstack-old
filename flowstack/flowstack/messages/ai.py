from typing import Any, Literal

from flowstack.messages import BaseMessage, MessageContent, MessageType

class AIMessage(BaseMessage):
    message_type: Literal[MessageType.AI]

    def __init__(
        self,
        content: MessageContent,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            message_type=MessageType.AI,
            content=content,
            metadata=metadata,
            **kwargs
        )