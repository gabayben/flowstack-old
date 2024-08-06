from abc import ABC
from enum import StrEnum
from typing import Any, Union

from pydantic import Field

from flowstack.artifacts import Artifact, Text
from flowstack.typing import Serializable

MessageValue = Union[str, Artifact]
MessageContent = Union[MessageValue, list[MessageValue]]

class MessageType(StrEnum):
    HUMAN = 'human'
    SYSTEM = 'system'
    AI = 'assistant'
    TOOL = 'tool'

class BaseMessage(Serializable, ABC):
    message_type: str
    content: list[Artifact]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        message_type: str,
        content: MessageContent,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            message_type=message_type,
            content=_to_artifacts(content),
            metadata=metadata,
            **kwargs
        )

    def __str__(self) -> str:
        return '\n\n'.join(str(artifact) for artifact in self.content)

def _to_artifacts(content: MessageContent) -> list[Artifact]:
    content = [content] if not isinstance(content, list) else content
    return [Text(value) if isinstance(value, str) else value for value in content]