from typing import Optional

from flowstack.artifacts import Artifact, GetArtifactId

def build_artifacts_from_splits(
    splits: list[str],
    artifact: Artifact,
    ref_artifact: Optional[Artifact] = None,
    id_func: Optional[GetArtifactId] = None
) -> list[Artifact]:
    pass