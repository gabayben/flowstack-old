from typing import Optional

from flowstack.artifacts import Artifact
from flowstack.components.ai.embedder import BaseEmbedder
from flowstack.typing import Embedding

class OpenAIEmbedder(BaseEmbedder):
    def _invoke(self, artifacts: list[Artifact], **kwargs) -> list[Optional[Embedding]]:
        pass