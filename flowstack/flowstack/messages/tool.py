from typing import Any, Literal

from flowstack.messages import BaseMessage, MessageContent, MessageType

class ToolMessage(BaseMessage):
    message_type: Literal[MessageType.TOOL]

    def __init__(
        self,
        content: MessageContent,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            message_type=MessageType.TOOL,
            content=content,
            metadata=metadata,
            **kwargs
        )