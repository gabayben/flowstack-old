from typing import Union

from flowstack.artifacts import Artifact, Modality

class Table(Artifact):
    @property
    def modality(self) -> Modality:
        return Modality.TABLE

    def get_hash(self) -> str:
        pass

    def set_content(self, content: Union[str, bytes]) -> None:
        pass