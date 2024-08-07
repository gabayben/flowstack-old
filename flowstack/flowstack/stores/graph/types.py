from abc import ABC, abstractmethod
from typing import Any, NamedTuple, Optional, Self, Union, override

from pydantic import Field

from flowstack.artifacts import Artifact, ArtifactMetadata, Text
from flowstack.typing import Embedding, Serializable

class GraphElement(Serializable, ABC):
    label: Optional[str] = Field(default=None, kw_only=True)
    properties: dict[str, Any] = Field(default_factory=dict, kw_only=True)
    metadata: dict[str, Any] = Field(default_factory=dict, kw_only=True)

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    def name(self) -> str:
        return self.label or self.id

    @abstractmethod
    def __str__(self) -> str:
        pass

    def to_artifact(self) -> Artifact:
        return Text(
            str(self),
            id=self.id,
            name=self.name,
            metadata=ArtifactMetadata(**self.metadata),
            **self.properties
        )

class GraphNode(GraphElement, ABC):
    embedding: Optional[Embedding] = Field(default=None, kw_only=True)

    @override
    def to_artifact(self) -> Artifact:
        return Text(
            str(self),
            id=self.id,
            name=self.name,
            embedding=self.embedding,
            metadata=ArtifactMetadata(**self.metadata),
            **self.properties
        )

class EntityNode(GraphNode):
    name: str

    @property
    def id(self) -> str:
        return self.name.replace('"', ' ')

    def __str__(self) -> str:
        return self.name

class ChunkNode(GraphNode):
    text: str
    id_: Optional[str] = Field(default=None, kw_only=True)

    @property
    def id(self) -> str:
        return self.id_ or str(hash(self.text))

    @classmethod
    def from_artifact(cls, artifact: Artifact) -> Self:
        return cls(
            text=str(artifact),
            id_=artifact.id,
            label=artifact.name,
            embedding=artifact.embedding,
            properties={
                **artifact.model_dump(exclude={'id', 'name', 'embedding', 'metadata'})
            },
            metadata=artifact.metadata
        )

    def __str__(self) -> str:
        return self.text

class GraphRelation(GraphElement):
    source: str
    target: str

    @property
    def id(self) -> str:
        return _relation_id(self.source, self.target)

    def __str__(self) -> str:
        return self.label or f'{self.source} to {self.target}'

class GraphTripletMetadata(ArtifactMetadata):
    subject: dict[str, Any]
    relation: dict[str, Any]
    obj: dict[str, Any]

    def __init__(self, **data):
        data.setdefault('subject', {})
        data.setdefault('relation', {})
        data.setdefault('obj', {})
        super().__init__(**data)

class GraphTriplet(NamedTuple):
    subject: GraphNode
    relation: GraphRelation
    obj: GraphNode

    def __str__(self) -> str:
        return f'({str(self.subject)}, {str(self.relation)}, {str(self.obj)})'

    def to_artifact(self) -> Artifact:
        return Text(
            str(self),
            metadata=GraphTripletMetadata(
                subject=self.subject.properties,
                relation=self.relation.properties,
                obj=self.obj.properties
            )
        )

class Graph(Serializable):
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    relations: dict[str, GraphRelation] = Field(default_factory=dict)
    triplets: set[tuple[str, str, str]] = Field(default_factory=set)

    def ger_nodes(self) -> list[GraphNode]:
        return list(self.nodes.values())

    def get_relations(self) -> list[GraphRelation]:
        return list(self.relations.values())

    def get_triplets(self) -> list[GraphTriplet]:
        return [
            GraphTriplet(self.nodes[subject], self.relations[relation], self.nodes[obj])
            for subject, relation, obj in self.triplets
        ]

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_relation(self, relation: GraphRelation) -> None:
        if relation.source not in self.nodes:
            self.nodes[relation.source] = EntityNode(name=relation.source)
        if relation.target not in self.nodes:
            self.nodes[relation.target] = EntityNode(name=relation.target)
        self.add_triplet(GraphTriplet(
            self.nodes[relation.source],
            relation,
            self.nodes[relation.target]
        ))

    def add_triplet(self, triplet: GraphTriplet) -> None:
        subject, relation, obj = triplet
        if (subject.id, relation.id, obj.id) in self.triplets:
            return
        self.add_node(subject)
        self.add_node(obj)
        self.relations[relation.id] = relation
        self.triplets.add((subject.id, relation.id, obj.id))

    def delete_node(self, node_id: str) -> None:
        if node_id in self.nodes:
            del self.nodes[node_id]

    def delete_relation(self, relation_id: Union[str, tuple[str, str]]) -> None:
        relation_id = (
            relation_id
            if isinstance(relation_id, str)
            else _relation_id(relation_id[0], relation_id[1])
        )
        if relation_id in self.relations:
            del self.relations[relation_id]

    def delete_triplet(self, triplet: tuple[str, str, str]) -> None:
        if triplet not in self.triplets:
            return
        subject_id, relation_id, obj_id = triplet
        self.delete_node(subject_id)
        self.delete_node(relation_id)
        self.delete_relation(relation_id)
        self.triplets.remove(triplet)

def _relation_id(source: str, target: str) -> str:
    return f'{source}->{target}'