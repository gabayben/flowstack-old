from typing import Union

from flowstack.messages import BaseMessage, MessageContent

LLMInput = Union[MessageContent, list[BaseMessage]]