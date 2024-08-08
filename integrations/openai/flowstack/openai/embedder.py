from flowstack.artifacts import Artifact
from flowstack.core import Component

class OpenAIEmbedder(Component[list[Artifact], list[Artifact]]):
    def invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass