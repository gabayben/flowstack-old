from typing import Any, Literal

from flowstack.messages import BaseMessage, MessageContent, MessageType

class SystemMessage(BaseMessage):
    message_type: Literal[MessageType.SYSTEM]

    def __init__(
        self,
        content: MessageContent,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            message_type=MessageType.SYSTEM,
            content=content,
            metadata=metadata,
            **kwargs
        )