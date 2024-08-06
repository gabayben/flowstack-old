from abc import ABC
from typing import Any, Self, Union, override

from flowstack.artifacts import ArtifactMetadata, Modality, Utf8Artifact

class TextBase(Utf8Artifact, ABC):
    content: str

    @property
    @override
    def modality(self) -> Modality:
        return Modality.TEXT

    def __init__(
        self,
        content: str,
        metadata: ArtifactMetadata = ArtifactMetadata(),
        **kwargs
    ):
        super().__init__(
            content=content,
            metadata=metadata,
            **kwargs
        )

    @classmethod
    def from_bytes(cls, data: bytes, **kwargs) -> Self:
        return cls(data.decode('utf-8'))

    @override
    def store_model_dump(self, **kwargs) -> dict[str, Any]:
        return super().store_model_dump(exclude={'content'}, **kwargs)

    def to_utf8(self) -> str:
        return self.content

    def set_content(self, content: Union[str, bytes]) -> None:
        if isinstance(content, str):
            self.content = content
        else:
            self.content = content.decode('utf-8')

class Text(TextBase):
    """Artifact for capturing free text from within document."""