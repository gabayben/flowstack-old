from abc import ABC, abstractmethod
from datetime import datetime
import datetime as dt
from enum import StrEnum, auto
from hashlib import sha256
import os
from pathlib import Path
from typing import Any, Literal, Optional, Self, TYPE_CHECKING, TypedDict, Union, override

from docarray.base_doc.doc import BaseDocWithoutId, IncEx
from docarray.typing import AnyUrl, ID
from pydantic import Field

from flowstack.typing import ModelDict, Embedding, PydanticRegistry, Serializable
from flowstack.utils.constants import DATETIMETZ_FORMAT, SCHEMA_TYPE
from flowstack.utils.paths import get_mime_type, last_modified_date
from flowstack.utils.string import type_name

if TYPE_CHECKING:
    from flowstack.artifacts.link import Link
    # from flowstack.stores import GraphNode, GraphRelation

class Modality(StrEnum):
    TEXT = 'text'
    TABLE = 'table'
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    MESH_3D = 'mesh_3d'
    POINT_CLOUD_3D = 'point_cloud_3d'

##### Hierarchy

class ArtifactRelationship(StrEnum):
    REF = auto()
    PREVIOUS = auto()
    NEXT = auto()
    PARENT = auto()
    CHILDREN = auto()

class ArtifactInfo(Serializable):
    id: str
    type: Optional[str] = None
    hash: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        id_: str,
        type_: Optional[str] = None,
        hash_: Optional[str] = None,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            id=id_,
            type=type_,
            hash=hash_,
            metadata=metadata,
            **kwargs
        )

RelatedArtifact = Union[ArtifactInfo, list[ArtifactInfo]]

class ArtifactHierarchy(dict[ArtifactRelationship, RelatedArtifact]):
    @property
    def ref(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.REF not in self:
            return None
        related = self[ArtifactRelationship.REF]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Ref object must be a single ArtifactInfo object.')
        return related

    @ref.setter
    def ref(self, ref: Optional[ArtifactInfo]) -> None:
        self[ArtifactRelationship.REF] = ref

    @property
    def previous(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.PREVIOUS not in self:
            return None
        related = self[ArtifactRelationship.PREVIOUS]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Previous object must be a single ArtifactInfo object.')
        return related

    @previous.setter
    def previous(self, previous: Optional[ArtifactInfo]) -> None:
        self[ArtifactRelationship.PREVIOUS] = previous

    @property
    def next(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.NEXT not in self:
            return None
        related = self[ArtifactRelationship.NEXT]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Next object must be a single ArtifactInfo object.')
        return related

    @next.setter
    def next(self, next_: Optional[ArtifactInfo]) -> None:
        self[ArtifactRelationship.NEXT] = next_

    @property
    def parent(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.PARENT not in self:
            return None
        related = self[ArtifactRelationship.PARENT]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Parent object must be a single ArtifactInfo object.')
        return related

    @parent.setter
    def parent(self, parent: Optional[ArtifactInfo]) -> None:
        self[ArtifactRelationship.PARENT] = parent

    @property
    def children(self) -> Optional[list[ArtifactInfo]]:
        if ArtifactRelationship.CHILDREN not in self:
            return None
        children = self[ArtifactRelationship.CHILDREN]
        if not isinstance(children, list):
            raise ValueError('Children objects must be a list of ArtifactInfo objects.')
        return children

    @children.setter
    def children(self, children: Optional[list[ArtifactInfo]]):
        self[ArtifactRelationship.CHILDREN] = children

#### Metadata

class DataSourceMetadata(TypedDict, total=False):
    """
    Metadata fields that pertain to the data source of the document.
    """

    url: Optional[str]
    version: Optional[str]
    date_created: Optional[str]
    date_modified: Optional[str]
    date_processed: Optional[str]
    record_locator: Optional[dict[str, Any]]
    permissions_data: Optional[list[dict[str, Any]]]

class RegexMetadata(TypedDict):
    """
    Metadata that is extracted from a document artifact via regex.
    """

    text: str
    start: int
    end: int

class ArtifactMetadata(ModelDict):
    hierarchy: ArtifactHierarchy
    # graph_nodes: Optional[list['GraphNode']]
    # graph_relations: Optional[list['GraphRelation']]
    datestamp: Optional[datetime]
    filename: Optional[str]
    filetype: Optional[str]
    url: Optional[str]
    mime_type: Optional[str]
    page_name: Optional[str]
    page_number: Optional[int]
    detection_origin: Optional[str]
    detection_class_prob: Optional[float]
    emphasized_text_contents: Optional[list[str]]
    emphasized_text_tags: Optional[list[str]]
    signature: Optional[str]
    languages: Optional[list[str]]
    is_continuation: Optional[bool]
    links: Optional[list['Link']]
    source: Optional[DataSourceMetadata]
    regex: Optional[RegexMetadata]

    def __init__(self, **data):
        data.setdefault('hierarchy', ArtifactHierarchy())
        super().__init__(**data)

#### Artifacts

class Artifact(BaseDocWithoutId, ABC):
    id: ID = Field(
        default_factory=lambda: ID(os.urandom(16).hex()),
        examples=[os.urandom(16).hex()],
        description=(
            'The ID of the BaseDoc. This is useful for indexing in vector stores. '
            'If not set by user, it will automatically be assigned a random value.'
        )
    )
    name: Optional[str] = None
    metadata: ArtifactMetadata = Field(default_factory=ArtifactMetadata)
    embedding: Optional[Embedding] = Field(default=None, exclude=True, kw_only=True)
    score: Optional[float] = Field(default=None, exclude=True, kw_only=True)

    @property
    @abstractmethod
    def modality(self) -> Modality:
        pass

    @property
    def datestamp(self) -> Optional[str]:
        return (
            dt.datetime.strftime(self.metadata.datestamp, DATETIMETZ_FORMAT)
            if self.metadata.datestamp
            else None
        )

    @property
    def last_modified(self) -> Optional[str]:
        filename = self.metadata.filename
        modified_date: Optional[str] = None
        if filename:
            modified_date = last_modified_date(filename)
        if not modified_date:
            modified_date = (
                self.datestamp
                or self.metadata.source.get('date_modified')
                or self.metadata.source.get('date_processed')
                or self.metadata.source.get('date_created')
            )
        return modified_date

    @property
    def hierarchy(self) -> ArtifactHierarchy:
        return self.metadata.hierarchy

    @property
    def ref(self) -> Optional[ArtifactInfo]:
        return self.hierarchy.ref

    @ref.setter
    def ref(self, ref: Optional[ArtifactInfo]) -> None:
        self.hierarchy.ref = ref

    @property
    def previous(self) -> Optional[ArtifactInfo]:
        return self.hierarchy.previous

    @previous.setter
    def previous(self, previous: Optional[ArtifactInfo]) -> None:
        self.hierarchy.previous = previous

    @property
    def next(self) -> Optional[ArtifactInfo]:
        return self.hierarchy.next

    @next.setter
    def next(self, next_: Optional[ArtifactInfo]) -> None:
        self.hierarchy.next = next_

    @property
    def parent(self) -> Optional[ArtifactInfo]:
        return self.hierarchy.parent

    @parent.setter
    def parent(self, parent: Optional[ArtifactInfo]) -> None:
        self.hierarchy.parent = parent

    @property
    def children(self) -> Optional[list[ArtifactInfo]]:
        return self.hierarchy.children

    @children.setter
    def children(self, children: Optional[list[ArtifactInfo]]) -> None:
        self.hierarchy.children = children

    @classmethod
    def from_source(cls, source: 'ArtifactSource', metadata: dict[str, Any] = {}) -> Self:
        if isinstance(source, Artifact):
            metadata['mime_type'] = metadata.get('mime_type', None)
            return cls.from_artifact(source, metadata)
        return cls.from_path(source, metadata)

    @classmethod
    def from_artifact(cls, other: 'Artifact', metadata: dict[str, Any] = {}) -> Self:
        artifact = cls.from_bytes(bytes(other))
        artifact.metadata.update({**other.metadata, **metadata})
        return artifact

    @classmethod
    def from_path(cls, path: str | Path, metadata: dict[str, Any] = {}) -> Self:
        if isinstance(path, Path):
            valid_path = path.as_uri()
        else:
            valid_path = path
        return cls.from_bytes(AnyUrl(valid_path).load_bytes())

    @override
    def model_dump(
        self,
        *,
        mode: Union[Literal['json', 'python'], str] = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, Any]:
        return {
            **super().model_dump(
                mode=mode,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                round_trip=round_trip,
                warnings=warnings
            ),
            SCHEMA_TYPE: type_name(self.__class__)
        }

    def store_model_dump(self, exclude: set[str] = {}, **kwargs) -> dict[str, Any]:
        return {
            **self.model_dump(
                **kwargs,
                exclude={*exclude, 'embedding', 'score', 'metadata'}
            ),
            **self.metadata
        }

    @abstractmethod
    def get_hash(self) -> str:
        pass

    def is_empty(self) -> bool:
        return bytes(self) == b''

    def pretty_repr(self, **kwargs) -> str:
        return repr(self)

    @abstractmethod
    def set_content(self, content: Union[str, bytes]) -> None:
        pass

    @staticmethod
    def get_mime_type(source: 'ArtifactSource') -> str:
        path: Path
        if isinstance(source, str):
            path = Path(source)
        if isinstance(source, Path):
            mime_type = get_mime_type(source)
        elif isinstance(source, AnyUrl):
            mime_type = source.mime_type()
        elif isinstance(source, Artifact):
            mime_type = source.metadata.mime_type
        else:
            raise ValueError(f'Unsupported data source type: {type(source).__name__}.')
        return mime_type

    class Config:
        extra = 'allow'
        arbitrary_types_allowed = True

StrictArtifactSource = Path | Artifact
ArtifactSource = str | StrictArtifactSource

class Utf8Artifact(Artifact, ABC):
    def __str__(self) -> str:
        return self.to_utf8()

    def __contains__(self, item: Any) -> bool:
        text = item if isinstance(item, str) else str(item)
        return str(self).__contains__(text)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return (
            str(self) == str(other)
            and self.embedding == other.embedding
            and self.metadata.coordinates == other.metadata.coordinates
        )

    @abstractmethod
    def to_utf8(self) -> str:
        pass

    def to_base64(self, **kwargs) -> str:
        return str(self)

    def to_bytes(self, **kwargs) -> bytes:
        return str(self).encode(encoding='utf-8')

    def get_hash(self) -> str:
        identity = self.to_utf8() + str(self.metadata)
        return sha256(identity.encode('utf-8', 'surrogatepass')).hexdigest()

    def _get_string_for_regex_filter(self) -> str:
        return str(self)

#### Registry

class _ArtifactRegistry(PydanticRegistry[Artifact]):
    pass

artifact_registry = _ArtifactRegistry()