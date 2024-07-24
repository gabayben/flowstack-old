from typing import Any, Type, override

from pydantic import BaseModel

from flowstack.core import SerializableComponent

class PromptTemplate(SerializableComponent[dict[str, Any], str]):
    def __init__(self):
        pass

    def run(self, input: dict[str, Any], **kwargs) -> str:
        pass

    @override
    def input_schema(self) -> Type[BaseModel]:
        pass

    @override
    def output_schema(self) -> Type[BaseModel]:
        pass