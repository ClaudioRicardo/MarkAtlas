"""Modelos e estruturas de dados para representação de grafos Mermaid."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class NodeShape(str, Enum):
    """Formatos geométricos de nós suportados em fluxogramas Mermaid."""

    RECTANGLE = "rectangle"              # [Texto]
    ROUNDED = "rounded"                  # (Texto)
    STADIUM = "stadium"                  # ([Texto])
    SUBROUTINE = "subroutine"            # [[Texto]]
    CYLINDER = "cylinder"                # [(Texto)]
    CIRCLE = "circle"                    # ((Texto))
    DOUBLE_CIRCLE = "double_circle"      # (((Texto)))
    ASYMMETRIC = "asymmetric"            # >Texto]
    DECISION = "decision"                # {Texto}
    HEXAGON = "hexagon"                  # {{Texto}}
    PARALLELOGRAM = "parallelogram"      # [/Texto/]
    PARALLELOGRAM_ALT = "parallelogram_alt"  # [\Texto\]
    TRAPEZOID = "trapezoid"              # [/Texto\]
    TRAPEZOID_ALT = "trapezoid_alt"      # [\Texto/]


@dataclass
class MermaidNode:
    """Representa um nó individual em um diagrama Mermaid."""

    id: str
    label: str
    shape: NodeShape = NodeShape.RECTANGLE

    # Posições e dimensões calculadas pelo motor de layout
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    level: int = 0
    subgraph_id: Optional[str] = None


@dataclass
class MermaidEdge:
    """Representa uma aresta/conexão entre dois nós."""

    source: str
    target: str
    label: str = ""
    style: str = "solid"          # solid, dotted, thick
    has_arrow_start: bool = False
    has_arrow_end: bool = True


@dataclass
class MermaidSubgraph:
    """Representa um subgrafo (agrupamento visual) no diagrama."""

    id: str
    title: str
    node_ids: List[str] = field(default_factory=list)


@dataclass
class SequenceMessage:
    """Representa uma mensagem em um diagrama de sequência."""

    sender: str
    receiver: str
    text: str
    style: str = "solid"          # solid, dotted
    is_async: bool = False


@dataclass
class SequenceParticipant:
    """Representa um participante ou ator em um diagrama de sequência."""

    id: str
    label: str
    is_actor: bool = False


@dataclass
class ErAttribute:
    """Representa um atributo/coluna em uma entidade de diagrama ER."""

    type_name: str
    name: str
    key_type: str = ""           # PK, FK, UK
    comment: str = ""


@dataclass
class ErEntity:
    """Representa uma tabela/entidade em um diagrama ER."""

    name: str
    attributes: List[ErAttribute] = field(default_factory=list)

    # Coordenadas e dimensões calculadas
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    level: int = 0


@dataclass
class ErRelationship:
    """Representa um relacionamento entre duas entidades ER."""

    entity1: str
    cardinality1: str            # ||, |o, o|, }|, |{, }o, o{
    rel_type: str                # solid (--), dashed (..)
    cardinality2: str
    entity2: str
    label: str = ""


@dataclass
class ClassMember:
    """Representa um atributo ou método em um diagrama de classe."""

    visibility: str = "+"        # +, -, #, ~
    name: str = ""
    member_type: str = "field"   # field ou method
    return_type: str = ""


@dataclass
class ClassEntity:
    """Representa uma classe em um diagrama de classes."""

    name: str
    annotation: str = ""         # <<interface>>, <<abstract>>, <<service>>
    members: List[ClassMember] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    level: int = 0


@dataclass
class ClassRelation:
    """Representa herança, implementação, agregação ou composição."""

    class1: str
    rel_type: str                # inheritance (<|--), composition (*--), aggregation (o--), association (-->), dependency (..>)
    class2: str
    label: str = ""


@dataclass
class StateTransition:
    """Representa uma transição de estado."""

    source: str
    target: str
    label: str = ""


@dataclass
class PieSlice:
    """Representa uma fatia em um gráfico de pizza."""

    label: str
    value: float


@dataclass
class MindmapNode:
    """Representa um nó na árvore de mapa mental."""

    id: str
    label: str
    depth: int = 0
    children: List[MindmapNode] = field(default_factory=list)


@dataclass
class TimelineEvent:
    """Representa um evento ou período na linha do tempo."""

    period: str
    events: List[str] = field(default_factory=list)


@dataclass
class JourneyTask:
    """Representa uma etapa/tarefa em uma jornada do usuário."""

    name: str
    score: int = 3               # 1 a 5
    actors: List[str] = field(default_factory=list)
    section: str = ""


@dataclass
class KanbanColumn:
    """Representa uma coluna em um quadro Kanban."""

    title: str
    cards: List[str] = field(default_factory=list)


@dataclass
class GanttTask:
    """Representa uma barra de tarefa em um gráfico de Gantt."""

    name: str
    status: str = "active"       # done, active, crit
    start_date: str = ""
    duration: str = ""
    section: str = ""


@dataclass
class MermaidGraph:
    """Representa a árvore sintática (AST) de qualquer diagrama Mermaid suportado."""

    diagram_type: str = "flowchart"  # "flowchart", "sequence", "erDiagram", "classDiagram", "stateDiagram", "pie", "mindmap", "timeline", "journey", "kanban", "gantt"
    direction: str = "TD"            # TD, TB, LR, RL, BT
    title: str = ""
    nodes: Dict[str, MermaidNode] = field(default_factory=dict)
    edges: List[MermaidEdge] = field(default_factory=list)
    subgraphs: List[MermaidSubgraph] = field(default_factory=list)

    # Sequence Diagram
    participants: Dict[str, SequenceParticipant] = field(default_factory=dict)
    messages: List[SequenceMessage] = field(default_factory=list)
    has_autonumber: bool = False

    # ER Diagram
    er_entities: Dict[str, ErEntity] = field(default_factory=dict)
    er_relationships: List[ErRelationship] = field(default_factory=list)

    # Class Diagram
    classes: Dict[str, ClassEntity] = field(default_factory=dict)
    class_relations: List[ClassRelation] = field(default_factory=list)

    # State Diagram
    states: Set[str] = field(default_factory=set)
    state_transitions: List[StateTransition] = field(default_factory=list)

    # Pie Chart
    pie_slices: List[PieSlice] = field(default_factory=list)

    # Mindmap
    mindmap_root: Optional[MindmapNode] = None

    # Timeline
    timeline_periods: List[TimelineEvent] = field(default_factory=list)

    # User Journey
    journey_tasks: List[JourneyTask] = field(default_factory=list)

    # Kanban
    kanban_columns: List[KanbanColumn] = field(default_factory=list)

    # Gantt
    gantt_tasks: List[GanttTask] = field(default_factory=list)

    def add_node(self, node_id: str, label: Optional[str] = None, shape: NodeShape = NodeShape.RECTANGLE) -> MermaidNode:
        """Adiciona ou atualiza um nó no grafo sem sobrescrever rótulos customizados pré-existentes."""
        clean_id = node_id.strip()
        if clean_id not in self.nodes:
            self.nodes[clean_id] = MermaidNode(
                id=clean_id,
                label=label if label is not None else clean_id,
                shape=shape,
            )
        else:
            if label is not None and (label != clean_id or self.nodes[clean_id].label == clean_id):
                self.nodes[clean_id].label = label
            if shape != NodeShape.RECTANGLE:
                self.nodes[clean_id].shape = shape
        return self.nodes[clean_id]

    def get_or_add_class(self, class_name: str) -> ClassEntity:
        """Obtém ou cria uma classe no diagrama de classes."""
        clean_name = class_name.strip()
        if clean_name not in self.classes:
            self.classes[clean_name] = ClassEntity(name=clean_name)
        return self.classes[clean_name]

    def add_edge(self, edge: MermaidEdge) -> None:
        """Adiciona uma aresta ao grafo, garantindo que os nós existam."""
        if edge.source not in self.nodes:
            self.add_node(edge.source)
        if edge.target not in self.nodes:
            self.add_node(edge.target)
        self.edges.append(edge)

    def add_participant(self, p_id: str, label: Optional[str] = None, is_actor: bool = False) -> None:
        """Adiciona ou atualiza um participante no diagrama de sequência."""
        clean_id = p_id.strip()
        if clean_id not in self.participants:
            self.participants[clean_id] = SequenceParticipant(
                id=clean_id,
                label=label if label is not None else clean_id,
                is_actor=is_actor,
            )
        else:
            if label is not None and (label != clean_id or self.participants[clean_id].label == clean_id):
                self.participants[clean_id].label = label
            if is_actor:
                self.participants[clean_id].is_actor = True

    def get_or_add_er_entity(self, entity_name: str) -> ErEntity:
        """Obtém ou cria uma entidade de banco de dados no diagrama ER."""
        clean_name = entity_name.strip()
        if clean_name not in self.er_entities:
            self.er_entities[clean_name] = ErEntity(name=clean_name)
        return self.er_entities[clean_name]
