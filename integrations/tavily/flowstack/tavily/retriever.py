from flowstack.artifacts import Artifact
from flowstack.core import Component

class TavilyApiRetriever(Component[str, list[Artifact]]):
    def __call__(self, query: str, **kwargs) -> list[Artifact]:
        pass