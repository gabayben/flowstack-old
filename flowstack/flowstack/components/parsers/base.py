from abc import ABC, abstractmethod
from typing import Optional, final, override

from pydantic import Field

from flowstack.artifacts import Artifact, GetArtifactId
from flowstack.core import Component
from flowstack.utils.threading import run_async

class ArtifactParser(Component[list[Artifact], list[Artifact]], ABC):
    id_func: Optional[GetArtifactId] = Field(default=None, exclude=True)

    @final
    def invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        parent_map = {artifact.id: artifact for artifact in artifacts}
        artifacts = self._parse(artifacts, **kwargs)
        return self._postprocess_artifacts(artifacts, parent_map)

    @abstractmethod
    def _parse(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    @final
    @override
    async def ainvoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        parent_map = {artifact.id: artifact for artifact in artifacts}
        artifacts = await self._aparse(artifacts, **kwargs)
        return self._postprocess_artifacts(artifacts, parent_map)

    async def _aparse(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        return await run_async(self._parse, artifacts, **kwargs)

    def _postprocess_artifacts(
        self,
        artifacts: list[Artifact],
        parent_map: dict[str, Artifact]
    ) -> list[Artifact]:
        pass