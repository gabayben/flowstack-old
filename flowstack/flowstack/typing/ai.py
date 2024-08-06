from typing import Any, NotRequired, Optional, TypedDict

class ToolCall(TypedDict):
    name: str
    args: dict[str, Any]
    id: NotRequired[Optional[str]]

class ToolCallChunk(TypedDict):
    name: NotRequired[Optional[str]]
    args: NotRequired[Optional[str]]
    id: NotRequired[Optional[str]]
    index: NotRequired[Optional[int]]

class InvalidToolCall(TypedDict):
    name: NotRequired[Optional[str]]
    args: NotRequired[Optional[str]]
    id: NotRequired[Optional[str]]
    error: NotRequired[Optional[str]]

class UsageMetadata(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int