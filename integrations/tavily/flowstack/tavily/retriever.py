from flowstack.artifacts import Artifact
from flowstack.components.retrievers.base import BaseRetriever

class TavilyApiRetriever(BaseRetriever):
    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass