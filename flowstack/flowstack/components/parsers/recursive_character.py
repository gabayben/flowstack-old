from langchain_core.runnables import RunnableSerializable

from flowstack.artifacts import Artifact

class RecursiveCharacterSplitter(RunnableSerializable[list[Artifact], list[Artifact]]):
    def invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass