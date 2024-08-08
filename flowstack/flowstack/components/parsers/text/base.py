from abc import ABC, abstractmethod
from typing import final, override

from flowstack.artifacts import Artifact, ArtifactMetadata
from flowstack.components.parsers.base import BaseArtifactParser
from flowstack.components.parsers.utils import build_artifacts_from_splits
from flowstack.utils.threading import run_async

class TextSplitter(BaseArtifactParser, ABC):
    @final
    def _parse(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        chunks: list[Artifact] = []
        for artifact in artifacts:
            chunks.extend(
                build_artifacts_from_splits(
                    self._split_text(str(artifact), artifact.metadata, **kwargs),
                    artifact,
                    id_func=self.id_func
                )
            )
        return chunks

    @abstractmethod
    def _split_text(
        self,
        text: str,
        metadata: ArtifactMetadata,
        **kwargs
    ) -> list[str]:
        pass

    @final
    @override
    async def _aparse(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        chunks: list[Artifact] = []
        for artifact in artifacts:
            chunks.extend(
                build_artifacts_from_splits(
                    await self._asplit_text(str(artifact), artifact.metadata, **kwargs),
                    artifact,
                    id_func=self.id_func
                )
            )
        return chunks

    async def _asplit_text(
        self,
        text: str,
        metadata: ArtifactMetadata,
        **kwargs
    ) -> list[str]:
        return await run_async(self._split_text, text, metadata, **kwargs)