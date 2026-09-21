"""Parser léxico e sintático de código Mermaid para AST de grafo."""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from src.services.markdown.mermaid_models import (
    ErAttribute,
    ErEntity,
    ErRelationship,
    MermaidEdge,
    MermaidGraph,
    MermaidNode,
    MermaidSubgraph,
    NodeShape,
    SequenceMessage,
    SequenceParticipant,
)

logger = logging.getLogger(__name__)


class MermaidParser:
    """Interpreta definições de diagramas Mermaid (flowchart / graph / sequenceDiagram)."""

    # Tipos de diagrama não suportados pelo motor nativo
    # (ativam a ponte CLI automaticamente quando retornam None)
    _UNSUPPORTED_PREFIXES = (
        "statediagram",   # stateDiagram, stateDiagram-v2
        "classdiagram",
        "gitgraph",
        "pie",
        "mindmap",
        "timeline",
        "journey",
        "gantt",
        "quadrantchart",
        "requirementdiagram",
        "c4context", "c4container", "c4component", "c4dynamic", "c4deployment",
        "sankey-beta",
        "xychart-beta",
        "block-beta",
        "packet-beta",
        "kanban",
        "architecture-beta",
        "radar-beta",
        "zenuml",
    )

    # Regex para identificação de formato e rótulo de nós
    # Ordem rigorosa: formatos com delimitadores mais específicos antes dos genéricos
    _NODE_SHAPE_PATTERNS = [
        # Double circle (((texto)))
        (re.compile(r"^([a-zA-Z0-9_\-]+)\(\(\((.*?)\)\)\)$"), NodeShape.DOUBLE_CIRCLE),
        # Circle ((texto))
        (re.compile(r"^([a-zA-Z0-9_\-]+)\(\((.*?)\)\)$"), NodeShape.CIRCLE),
        # Cylinder / Database [(texto)]
        (re.compile(r"^([a-zA-Z0-9_\-]+)\[\((.*?)\)\]$"), NodeShape.CYLINDER),
        # Stadium / Pill ([texto])
        (re.compile(r"^([a-zA-Z0-9_\-]+)\(\[(.*?)\]\)$"), NodeShape.STADIUM),
        # Subroutine [[texto]]
        (re.compile(r"^([a-zA-Z0-9_\-]+)\[\[(.*?)\]\]$"), NodeShape.SUBROUTINE),
        # Hexagon {{texto}}
        (re.compile(r"^([a-zA-Z0-9_\-]+)\{\{(.*?)\}\}$"), NodeShape.HEXAGON),
        # Trapezoid [/texto\]
        (re.compile(r"^([a-zA-Z0-9_\-]+)\[/(.*?)\\\]$"), NodeShape.TRAPEZOID),
        # Trapezoid alt [\texto/]
        (re.compile(r"^([a-zA-Z0-9_\-]+)\[\\(.*?)/\]$"), NodeShape.TRAPEZOID_ALT),
        # Parallelogram [/texto/]
        (re.compile(r"^([a-zA-Z0-9_\-]+)\[/(.*?)/\]$"), NodeShape.PARALLELOGRAM),
        # Parallelogram alt [\texto\]
        (re.compile(r"^([a-zA-Z0-9_\-]+)\[\\(.*?)\\\]$"), NodeShape.PARALLELOGRAM_ALT),
        # Asymmetric >texto]
        (re.compile(r"^([a-zA-Z0-9_\-]+)>(.*?)\]$"), NodeShape.ASYMMETRIC),
        # Decision {texto}
        (re.compile(r"^([a-zA-Z0-9_\-]+)\{(.*?)\}$"), NodeShape.DECISION),
        # Rounded (texto)
        (re.compile(r"^([a-zA-Z0-9_\-]+)\((.*?)\)$"), NodeShape.ROUNDED),
        # Rectangle [texto]
        (re.compile(r"^([a-zA-Z0-9_\-]+)\[(.*?)\]$"), NodeShape.RECTANGLE),
    ]

    # Regex para conectores de setas e rótulos entre nós
    # Padrões mais longos com |...| e delimitadores explícitos vêm primeiro
    _ARROW_REGEX = re.compile(
        r"(-->\|[^|\n]+\||--\s*\|[^|\n]+\|\s*-->|--\s+[^-\n|>]+\s+-->|-->"
        r"|==>\|[^|\n]+\||==\s*\|[^|\n]+\|\s*==>|==\s+[^=\n|>]*\s+==>|==>"
        r"|-\.->\|[^|\n]+\||-\.\s*\|[^|\n]+\|\s*\.->|-\.\s+[^.\n|>]*\s+\.->|-\.->"
        r"|---\|[^|\n]+\||--\s*\|[^|\n]+\|\s*---|--\s+[^-\n|>]*\s+---|---"
        r"|<-->\|[^|\n]+\||<--\s*\|[^|\n]+\|\s*-->|<--\s+[^-\n|>]*\s+-->|<-->)"
    )

    def parse(self, code: str) -> Optional[MermaidGraph]:
        """Converte texto Mermaid em uma estrutura de dados MermaidGraph.

        :param code: Código bruto do bloco Mermaid
        :return: Instância de MermaidGraph preenchida ou None se inválido
        """
        raw_lines = code.strip().splitlines()
        lines = [line.strip() for line in raw_lines if line.strip() and not line.strip().startswith("%%")]
        if not lines:
            return None

        first_line = lines[0]
        first_lower = first_line.lower().strip()

        # 1. Diagrama de Sequência (sequenceDiagram)
        if first_lower.startswith("sequencediagram"):
            return self._parse_sequence_diagram(lines[1:])

        # 2. Diagrama de Entidade-Relacionamento (erDiagram)
        if first_lower.startswith("erdiagram"):
            return self._parse_er_diagram(lines[1:])

        # 3. Tipos de diagrama NÃO suportados nativamente (ativam a ponte CLI)
        if any(first_lower.startswith(pfx) for pfx in self._UNSUPPORTED_PREFIXES):
            return None

        # 4. Fluxograma (flowchart / graph)
        header_match = re.match(r"^(flowchart|graph)(?:\s+(TD|TB|LR|RL|BT))?\s*$", first_line, re.IGNORECASE)
        direction = "TD"
        start_idx = 0

        if header_match:
            direction = (header_match.group(2) or "TD").upper()
            start_idx = 1
        elif any(self._ARROW_REGEX.search(l) for l in lines):
            # Se não houver declaração explícita de header mas tiver conexões
            direction = "TD"
            start_idx = 0
        else:
            return None

        graph = MermaidGraph(diagram_type="flowchart", direction=direction)

        current_subgraph: Optional[MermaidSubgraph] = None

        # 3. Processa cada linha de definição
        for line in lines[start_idx:]:
            # Ignora linhas vazias
            if not line:
                continue

            # Subgrafos: subgraph id [Título] ou subgraph Título
            if line.lower().startswith("subgraph"):
                sg_match = re.match(r"^subgraph\s+([a-zA-Z0-9_\-]+)?(?:\s*\[?(.*?)\]?)?$", line, re.IGNORECASE)
                if sg_match:
                    sg_id = (sg_match.group(1) or f"sg_{len(graph.subgraphs)}").strip()
                    sg_title = (sg_match.group(2) or sg_id).strip().strip('"\'')
                    current_subgraph = MermaidSubgraph(id=sg_id, title=sg_title)
                    graph.subgraphs.append(current_subgraph)
                continue

            if line.lower() == "end":
                current_subgraph = None
                continue

            # Ignora diretivas cosméticas por enquanto
            if line.startswith(("classDef", "class ", "style ", "click ", "linkStyle", "direction ")):
                continue

            # Remove sufixo de estilo CSS inline (:::nomeClasse) antes de processar
            line = re.sub(r":::([a-zA-Z0-9_\-]+)", "", line).strip()
            if not line:
                continue

            self._parse_flowchart_line(line, graph, current_subgraph)

        return graph if graph.nodes else None

    def _parse_sequence_diagram(self, lines: List[str]) -> Optional[MermaidGraph]:
        """Interpreta linhas de um diagrama de sequência."""
        graph = MermaidGraph(diagram_type="sequence", direction="TD")

        for line in lines:
            if not line:
                continue

            if line.lower() == "autonumber":
                graph.has_autonumber = True
                continue

            # Participante / Ator explícito: participant/actor Id [as Rótulo]
            part_match = re.match(r"^(actor|participant)\s+([a-zA-Z0-9_\-]+)(?:\s+as\s+(.*))?$", line, re.IGNORECASE)
            if part_match:
                is_actor = part_match.group(1).lower() == "actor"
                p_id = part_match.group(2).strip()
                label = (part_match.group(3) or p_id).strip().strip('"\'')
                graph.add_participant(p_id, label=label, is_actor=is_actor)
                continue

            # Mensagens entre participantes: A->>B: Mensagem ou A-->>B: Resposta
            msg_match = re.match(
                r"^([a-zA-Z0-9_]+)\s*(-->>|->>|-->|->)\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$",
                line,
            )
            if msg_match:
                sender, arrow, receiver, text = msg_match.groups()
                sender = sender.strip()
                receiver = receiver.strip()
                text = text.strip()

                graph.add_participant(sender)
                graph.add_participant(receiver)

                style = "dotted" if "--" in arrow else "solid"
                is_async = ">>" in arrow

                graph.messages.append(
                    SequenceMessage(
                        sender=sender,
                        receiver=receiver,
                        text=text,
                        style=style,
                        is_async=is_async,
                    )
                )

        return graph if graph.participants or graph.messages else None

    def _parse_er_diagram(self, lines: List[str]) -> Optional[MermaidGraph]:
        """Interpreta definições de diagramas de entidade-relacionamento (erDiagram)."""
        graph = MermaidGraph(diagram_type="erDiagram", direction="TD")
        current_entity: Optional[ErEntity] = None

        for line in lines:
            if not line:
                continue

            # Fechamento de entidade }
            if line == "}":
                current_entity = None
                continue

            # Se estiver dentro do bloco de atributos de uma entidade
            if current_entity is not None:
                # type name [PK|FK|UK] ["comment"]
                attr_match = re.match(
                    r"^([a-zA-Z0-9_<>,]+)\s+([a-zA-Z0-9_]+)(?:\s+(PK|FK|UK))?(?:\s+\"?(.*?)\"?)?$",
                    line,
                )
                if attr_match:
                    type_name, name, key_type, comment = attr_match.groups()
                    current_entity.attributes.append(
                        ErAttribute(
                            type_name=type_name.strip(),
                            name=name.strip(),
                            key_type=(key_type or "").strip(),
                            comment=(comment or "").strip().strip('"\''),
                        )
                    )
                else:
                    tokens = line.split()
                    if len(tokens) >= 2:
                        current_entity.attributes.append(
                            ErAttribute(
                                type_name=tokens[0],
                                name=tokens[1],
                                key_type=tokens[2] if len(tokens) > 2 and tokens[2] in ("PK", "FK", "UK") else "",
                            )
                        )
                continue

            # Abertura de entidade: ENTITY_NAME {
            entity_open = re.match(r"^([a-zA-Z0-9_\-]+)\s*\{$", line)
            if entity_open:
                entity_name = entity_open.group(1).strip()
                current_entity = graph.get_or_add_er_entity(entity_name)
                continue

            # Relacionamento: ENTITY1 ||--o{ ENTITY2 : "rótulo"
            rel_match = re.match(
                r"^([a-zA-Z0-9_\-]+)\s+([|o\}]+[\-\.]+[|o\{]+)\s+([a-zA-Z0-9_\-]+)(?:\s*:\s*\"?(.*?)\"?)?$",
                line,
            )
            if rel_match:
                e1, conn, e2, label = rel_match.groups()
                e1 = e1.strip()
                e2 = e2.strip()
                label = (label or "").strip().strip('"\'')

                graph.get_or_add_er_entity(e1)
                graph.get_or_add_er_entity(e2)

                is_dashed = ".." in conn
                parts = re.split(r"\-\-|\.\.", conn)
                card1 = parts[0].strip() if len(parts) > 0 else "||"
                card2 = parts[1].strip() if len(parts) > 1 else "o{"

                graph.er_relationships.append(
                    ErRelationship(
                        entity1=e1,
                        cardinality1=card1,
                        rel_type="dashed" if is_dashed else "solid",
                        cardinality2=card2,
                        entity2=e2,
                        label=label,
                    )
                )

        return graph if graph.er_entities or graph.er_relationships else None

    def _parse_flowchart_line(
        self,
        line: str,
        graph: MermaidGraph,
        current_subgraph: Optional[MermaidSubgraph] = None,
    ) -> None:
        """Processa uma linha de fluxograma contendo nós e possíveis conexões."""
        arrow_matches = list(self._ARROW_REGEX.finditer(line))

        if not arrow_matches:
            # Nós isolados (ex: A[Aplicação])
            node_info = self._parse_node_token(line)
            if node_info:
                n = graph.add_node(node_info[0], label=node_info[1], shape=node_info[2])
                if current_subgraph:
                    n.subgraph_id = current_subgraph.id
                    if n.id not in current_subgraph.node_ids:
                        current_subgraph.node_ids.append(n.id)
            return

        # Divide a linha pelos conectores: A & B -->|1| C & D --> E
        parts = []
        last_end = 0

        for match in arrow_matches:
            node_part = line[last_end:match.start()].strip()
            if node_part:
                parts.append(node_part)

            arrow_str = match.group(0)
            parts.append(arrow_str)
            last_end = match.end()

        final_part = line[last_end:].strip()
        if final_part:
            parts.append(final_part)

        idx = 0
        while idx + 2 < len(parts):
            left_token = parts[idx]
            arrow_token = parts[idx + 1]
            right_token = parts[idx + 2]

            left_nodes = self._parse_compound_node_token(left_token)
            right_nodes = self._parse_compound_node_token(right_token)

            edge_label, edge_style, arrow_start, arrow_end = self._parse_arrow_token(arrow_token)

            for l_id, l_label, l_shape in left_nodes:
                node_l = graph.add_node(l_id, label=l_label, shape=l_shape)
                if current_subgraph:
                    node_l.subgraph_id = current_subgraph.id
                    if node_l.id not in current_subgraph.node_ids:
                        current_subgraph.node_ids.append(node_l.id)

                for r_id, r_label, r_shape in right_nodes:
                    node_r = graph.add_node(r_id, label=r_label, shape=r_shape)
                    if current_subgraph:
                        node_r.subgraph_id = current_subgraph.id
                        if node_r.id not in current_subgraph.node_ids:
                            current_subgraph.node_ids.append(node_r.id)

                    graph.add_edge(
                        MermaidEdge(
                            source=l_id,
                            target=r_id,
                            label=edge_label,
                            style=edge_style,
                            has_arrow_start=arrow_start,
                            has_arrow_end=arrow_end,
                        )
                    )

            idx += 2

    def _parse_compound_node_token(self, token: str) -> List[Tuple[str, str, NodeShape]]:
        """Processa tokens com suporte a múltiplos nós concatenados com '&' (ex: A & B)."""
        clean = token.strip()
        if not clean:
            return []

        sub_tokens = self._split_compound_token(clean)
        results = []
        for st in sub_tokens:
            info = self._parse_node_token(st)
            if info:
                results.append(info)
        return results

    def _split_compound_token(self, text: str) -> List[str]:
        """Divide uma expressão de nós compostos por '&' respeitando delimitadores fechados."""
        parts: List[str] = []
        curr: List[str] = []
        depth = 0
        in_quote = False

        for ch in text:
            if ch in ('"', "'"):
                in_quote = not in_quote
                curr.append(ch)
            elif not in_quote and ch in ("[", "(", "{"):
                depth += 1
                curr.append(ch)
            elif not in_quote and ch in ("]", ")", "}"):
                depth = max(0, depth - 1)
                curr.append(ch)
            elif not in_quote and depth == 0 and ch == "&":
                part_str = "".join(curr).strip()
                if part_str:
                    parts.append(part_str)
                curr = []
            else:
                curr.append(ch)

        final_str = "".join(curr).strip()
        if final_str:
            parts.append(final_str)

        return parts

    def _parse_node_token(self, token: str) -> Optional[Tuple[str, str, NodeShape]]:
        """Extrai ID, rótulo higienizado e formato geométrico de um token de nó."""
        clean = token.strip()
        if not clean:
            return None

        for pattern, shape in self._NODE_SHAPE_PATTERNS:
            match = pattern.match(clean)
            if match:
                node_id, label = match.groups()
                clean_label = self._sanitize_label(label)
                return (node_id.strip(), clean_label, shape)

        # Se for apenas o identificador puro
        if re.match(r"^[a-zA-Z0-9_\-]+$", clean):
            return (clean, clean, NodeShape.RECTANGLE)

        return None

    def _sanitize_label(self, label: str) -> str:
        """Remove aspas externas e normaliza quebras de linha em rótulos."""
        clean = label.strip()
        if (clean.startswith('"') and clean.endswith('"')) or (clean.startswith("'") and clean.endswith("'")):
            clean = clean[1:-1].strip()
        return clean

    def _parse_arrow_token(self, token: str) -> Tuple[str, str, bool, bool]:
        """Extrai rótulo, estilo de linha e pontas de seta de um conector."""
        clean = token.strip()
        label = ""
        style = "solid"
        arrow_start = False
        arrow_end = True

        # 1. Rótulo entre pipes |texto|
        pipe_match = re.search(r"\|(.*?)\|", clean)
        if pipe_match:
            label = pipe_match.group(1).strip()
        else:
            # 2. Rótulo inline no formato -- texto --> ou == texto ==>
            inline_match = re.search(r"(?:--|==|-\.)\s+(.*?)\s+(?:-->|==>|\.->|---|===)", clean)
            if inline_match:
                label = inline_match.group(1).strip()

        if clean.startswith("-.") or "-.-" in clean or ".->" in clean:
            style = "dotted"
        elif clean.startswith("==") or "===" in clean or "==>" in clean:
            style = "thick"
        elif clean.startswith("---") and not clean.endswith(">"):
            style = "solid"
            arrow_end = False

        if clean.startswith("<"):
            arrow_start = True

        return (label, style, arrow_start, arrow_end)
