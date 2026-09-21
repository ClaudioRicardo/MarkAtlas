"""Gerador vetorial de SVG para diagramas Mermaid (Flowchart e Sequence) estilizados com ThemeColors."""

from __future__ import annotations

import html
import math
import re
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

from src.services.markdown.mermaid_models import (
    ErAttribute,
    ErEntity,
    ErRelationship,
    MermaidEdge,
    MermaidGraph,
    MermaidNode,
    NodeShape,
    SequenceMessage,
    SequenceParticipant,
)
from src.services.markdown.theme_colors import ThemeColors


class MermaidSvgGenerator:
    """Calcula o layout geométrico e gera código SVG vetorial a partir da AST Mermaid."""

    def __init__(self) -> None:
        self._layer_gap_td = 70.0
        self._layer_gap_lr = 90.0
        self._node_gap = 30.0

    def generate_svg(self, graph: MermaidGraph, colors: ThemeColors) -> str:
        """Calcula o posicionamento e retorna uma string XML de SVG completo.

        :param graph: Grafo contendo nós, arestas, sequência ou entidades ER
        :param colors: Paleta de cores do tema ativo
        :return: String SVG vetorial pronta para renderização
        """
        if graph.diagram_type == "sequence":
            return self._render_sequence_diagram(graph, colors)
        elif graph.diagram_type == "erDiagram":
            return self._render_er_diagram(graph, colors)

        if not graph.nodes:
            return ""

        # 1. Calcula as dimensões de cada nó baseado no texto do rótulo
        self._calculate_node_dimensions(graph)

        # 2. Distribui os nós em camadas hierárquicas
        layers = self._assign_layers(graph)

        # 3. Calcula coordenadas (X, Y) para cada nó
        is_lr = graph.direction in ("LR", "RL")
        width, height = self._calculate_positions(graph, layers, is_lr)

        # 4. Renderiza os elementos SVG
        return self._render_flowchart_svg(graph, colors, width, height, is_lr)

    def _calculate_node_dimensions(self, graph: MermaidGraph) -> None:
        """Estima a largura e altura de cada nó conforme o formato e comprimento do texto."""
        for node in graph.nodes.values():
            lines = [l.strip() for l in re.split(r"<br\s*/?>|\n", node.label) if l.strip()]
            if not lines:
                lines = [node.id]

            max_chars = max(len(l) for l in lines)
            text_width = max(60.0, max_chars * 8.2)
            num_lines = len(lines)
            base_height = max(46.0, num_lines * 18.0 + 20.0)

            if node.shape == NodeShape.DECISION:
                node.width = max(140.0, text_width + 60.0)
                node.height = max(68.0, base_height + 20.0)
            elif node.shape in (NodeShape.CIRCLE, NodeShape.DOUBLE_CIRCLE):
                diam = max(70.0, max(text_width, base_height) + 20.0)
                node.width = diam
                node.height = diam
            elif node.shape == NodeShape.HEXAGON:
                node.width = max(130.0, text_width + 50.0)
                node.height = base_height
            elif node.shape == NodeShape.CYLINDER:
                node.width = max(110.0, text_width + 36.0)
                node.height = max(58.0, base_height + 12.0)
            elif node.shape == NodeShape.STADIUM:
                node.width = max(120.0, text_width + 44.0)
                node.height = base_height
            else:
                node.width = max(110.0, text_width + 36.0)
                node.height = base_height

    def _assign_layers(self, graph: MermaidGraph) -> List[List[str]]:
        """Organiza os nós em camadas topológicas (ranks)."""
        in_degree: Dict[str, int] = {node_id: 0 for node_id in graph.nodes}
        adj_list: Dict[str, List[str]] = defaultdict(list)

        for edge in graph.edges:
            if edge.target in in_degree:
                in_degree[edge.target] += 1
            adj_list[edge.source].append(edge.target)

        # Nós sem arestas de entrada começam na camada 0
        node_layer: Dict[str, int] = {}
        queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])

        for node_id in queue:
            node_layer[node_id] = 0

        # Se houver ciclos ou nós isolados
        if not queue:
            first_node = next(iter(graph.nodes))
            queue.append(first_node)
            node_layer[first_node] = 0

        visited: Set[str] = set()

        while queue:
            curr = queue.popleft()
            visited.add(curr)
            curr_layer = node_layer.get(curr, 0)

            for neighbor in adj_list[curr]:
                node_layer[neighbor] = max(node_layer.get(neighbor, 0), curr_layer + 1)
                if neighbor not in visited and neighbor not in queue:
                    queue.append(neighbor)

        # Garante que todos os nós tenham uma camada atribuída
        for node_id in graph.nodes:
            if node_id not in node_layer:
                node_layer[node_id] = 0

        max_layer = max(node_layer.values()) if node_layer else 0
        layers: List[List[str]] = [[] for _ in range(max_layer + 1)]
        for node_id, layer_idx in node_layer.items():
            layers[layer_idx].append(node_id)
            graph.nodes[node_id].level = layer_idx

        return layers

    def _calculate_positions(self, graph: MermaidGraph, layers: List[List[str]], is_lr: bool) -> Tuple[float, float]:
        """Calcula coordenadas (x, y) absolutas para cada nó e retorna (largura_total, altura_total)."""
        padding = 40.0

        if not is_lr:
            # Layout Top-Down (TD / TB)
            max_row_width = 0.0
            layer_heights: List[float] = []

            for layer in layers:
                row_width = sum(graph.nodes[nid].width for nid in layer) + max(0, len(layer) - 1) * self._node_gap
                max_row_width = max(max_row_width, row_width)
                max_h = max((graph.nodes[nid].height for nid in layer), default=46.0)
                layer_heights.append(max_h)

            total_width = max_row_width + (padding * 2)
            curr_y = padding

            for layer_idx, layer in enumerate(layers):
                row_width = sum(graph.nodes[nid].width for nid in layer) + max(0, len(layer) - 1) * self._node_gap
                curr_x = (total_width - row_width) / 2.0
                layer_h = layer_heights[layer_idx]

                for nid in layer:
                    node = graph.nodes[nid]
                    node.x = curr_x + node.width / 2.0
                    node.y = curr_y + layer_h / 2.0
                    curr_x += node.width + self._node_gap

                curr_y += layer_h + self._layer_gap_td

            total_height = curr_y - self._layer_gap_td + padding
            return (total_width, total_height)
        else:
            # Layout Left-to-Right (LR)
            max_col_height = 0.0
            layer_widths: List[float] = []

            for layer in layers:
                col_h = sum(graph.nodes[nid].height for nid in layer) + max(0, len(layer) - 1) * self._node_gap
                max_col_height = max(max_col_height, col_h)
                max_w = max((graph.nodes[nid].width for nid in layer), default=120.0)
                layer_widths.append(max_w)

            total_height = max_col_height + (padding * 2)
            curr_x = padding

            for layer_idx, layer in enumerate(layers):
                col_h = sum(graph.nodes[nid].height for nid in layer) + max(0, len(layer) - 1) * self._node_gap
                curr_y = (total_height - col_h) / 2.0
                layer_w = layer_widths[layer_idx]

                for nid in layer:
                    node = graph.nodes[nid]
                    node.x = curr_x + layer_w / 2.0
                    node.y = curr_y + node.height / 2.0
                    curr_y += node.height + self._node_gap

                curr_x += layer_w + self._layer_gap_lr

            total_width = curr_x - self._layer_gap_lr + padding
            return (total_width, total_height)

    def _render_flowchart_svg(
        self,
        graph: MermaidGraph,
        colors: ThemeColors,
        width: float,
        height: float,
        is_lr: bool,
    ) -> str:
        """Gera a árvore XML do SVG formatada com elementos de nós, subgrafos e arestas."""
        svg_parts: List[str] = []

        svg_parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
            f'width="{width:.1f}" height="{height:.1f}" style="background-color: transparent;">'
        )

        svg_parts.append(
            f'<defs>'
            f'  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'    <path d="M 0 1 L 10 5 L 0 9 z" fill="{colors.tag_color}" />'
            f'  </marker>'
            f'  <filter id="shadow" x="-8%" y="-8%" width="120%" height="120%">'
            f'    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.25"/>'
            f'  </filter>'
            f'</defs>'
        )

        # 1. Desenha os Subgrafos (plano de fundo agrupador)
        for sg in graph.subgraphs:
            member_nodes = [graph.nodes[nid] for nid in sg.node_ids if nid in graph.nodes]
            if not member_nodes:
                continue

            sg_min_x = min(n.x - n.width / 2.0 for n in member_nodes) - 16.0
            sg_min_y = min(n.y - n.height / 2.0 for n in member_nodes) - 28.0
            sg_max_x = max(n.x + n.width / 2.0 for n in member_nodes) + 16.0
            sg_max_y = max(n.y + n.height / 2.0 for n in member_nodes) + 16.0
            sg_w = sg_max_x - sg_min_x
            sg_h = sg_max_y - sg_min_y

            svg_parts.append(
                f'<rect x="{sg_min_x:.1f}" y="{sg_min_y:.1f}" width="{sg_w:.1f}" height="{sg_h:.1f}" '
                f'rx="8" ry="8" fill="rgba(128, 128, 128, 0.07)" stroke="{colors.quote_color}" '
                f'stroke-width="1.2" stroke-dasharray="4,4"/>'
            )
            svg_parts.append(
                f'<text x="{(sg_min_x + 12.0):.1f}" y="{(sg_min_y + 18.0):.1f}" fill="{colors.tag_color}" '
                f'font-family="Inter, system-ui, sans-serif" font-size="11" font-weight="700" '
                f'text-anchor="start">{html.escape(sg.title)}</text>'
            )

        # 2. Desenha as Arestas / Conexões
        for edge in graph.edges:
            src = graph.nodes.get(edge.source)
            tgt = graph.nodes.get(edge.target)
            if not src or not tgt:
                continue

            if not is_lr:
                x1, y1 = src.x, src.y + src.height / 2.0
                x2, y2 = tgt.x, tgt.y - tgt.height / 2.0
                mid_y = (y1 + y2) / 2.0
                path_d = f"M {x1:.1f} {y1:.1f} C {x1:.1f} {mid_y:.1f}, {x2:.1f} {mid_y:.1f}, {x2:.1f} {y2:.1f}"
                label_x = (x1 + x2) / 2.0
                label_y = mid_y
            else:
                x1, y1 = src.x + src.width / 2.0, src.y
                x2, y2 = tgt.x - tgt.width / 2.0, tgt.y
                mid_x = (x1 + x2) / 2.0
                path_d = f"M {x1:.1f} {y1:.1f} C {mid_x:.1f} {y1:.1f}, {mid_x:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"
                label_x = mid_x
                label_y = (y1 + y2) / 2.0

            dash_attr = 'stroke-dasharray="4,4"' if edge.style == "dotted" else ""
            width_attr = 'stroke-width="2.5"' if edge.style == "thick" else 'stroke-width="1.8"'
            marker_end = 'marker-end="url(#arrow)"' if edge.has_arrow_end else ""
            marker_start = 'marker-start="url(#arrow)"' if edge.has_arrow_start else ""

            svg_parts.append(
                f'<path d="{path_d}" fill="none" stroke="{colors.tag_color}" {width_attr} {dash_attr} {marker_start} {marker_end} />'
            )

            # Rótulo de aresta
            if edge.label:
                escaped_label = html.escape(edge.label)
                label_w = len(edge.label) * 7.5 + 16.0
                svg_parts.append(
                    f'<rect x="{(label_x - label_w / 2.0):.1f}" y="{(label_y - 10.0):.1f}" '
                    f'width="{label_w:.1f}" height="20" rx="4" ry="4" '
                    f'fill="{colors.table_header_bg}" stroke="{colors.table_border}" stroke-width="1"/>'
                )
                svg_parts.append(
                    f'<text x="{label_x:.1f}" y="{(label_y + 4.0):.1f}" '
                    f'fill="{colors.h_color}" font-family="Inter, system-ui, sans-serif" '
                    f'font-size="11" font-weight="500" text-anchor="middle">{escaped_label}</text>'
                )

        # 3. Desenha os Nós em todas as 14 formas suportadas
        for node in graph.nodes.values():
            x = node.x - node.width / 2.0
            y = node.y - node.height / 2.0
            cx, cy = node.x, node.y
            w, h = node.width, node.height
            w2, h2 = w / 2.0, h / 2.0

            if node.shape == NodeShape.DECISION:
                pts = f"{cx:.1f},{(cy - h2):.1f} {(cx + w2):.1f},{cy:.1f} {cx:.1f},{(cy + h2):.1f} {(cx - w2):.1f},{cy:.1f}"
                svg_parts.append(f'<polygon points="{pts}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape == NodeShape.HEXAGON:
                cut = min(18.0, w / 4.0)
                pts = f"{(x + cut):.1f},{y:.1f} {(x + w - cut):.1f},{y:.1f} {(x + w):.1f},{cy:.1f} {(x + w - cut):.1f},{(y + h):.1f} {(x + cut):.1f},{(y + h):.1f} {x:.1f},{cy:.1f}"
                svg_parts.append(f'<polygon points="{pts}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape in (NodeShape.PARALLELOGRAM, NodeShape.TRAPEZOID):
                cut = min(16.0, w / 4.0)
                if node.shape == NodeShape.PARALLELOGRAM:
                    pts = f"{(x + cut):.1f},{y:.1f} {(x + w):.1f},{y:.1f} {(x + w - cut):.1f},{(y + h):.1f} {x:.1f},{(y + h):.1f}"
                else:
                    pts = f"{(x + cut):.1f},{y:.1f} {(x + w - cut):.1f},{y:.1f} {(x + w):.1f},{(y + h):.1f} {x:.1f},{(y + h):.1f}"
                svg_parts.append(f'<polygon points="{pts}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape in (NodeShape.PARALLELOGRAM_ALT, NodeShape.TRAPEZOID_ALT):
                cut = min(16.0, w / 4.0)
                if node.shape == NodeShape.PARALLELOGRAM_ALT:
                    pts = f"{x:.1f},{y:.1f} {(x + w - cut):.1f},{y:.1f} {(x + w):.1f},{(y + h):.1f} {(x + cut):.1f},{(y + h):.1f}"
                else:
                    pts = f"{x:.1f},{y:.1f} {(x + w):.1f},{y:.1f} {(x + w - cut):.1f},{(y + h):.1f} {(x + cut):.1f},{(y + h):.1f}"
                svg_parts.append(f'<polygon points="{pts}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape == NodeShape.ASYMMETRIC:
                cut = 14.0
                pts = f"{x:.1f},{y:.1f} {(x + w):.1f},{y:.1f} {(x + w):.1f},{(y + h):.1f} {x:.1f},{(y + h):.1f} {(x + cut):.1f},{cy:.1f}"
                svg_parts.append(f'<polygon points="{pts}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape == NodeShape.CIRCLE:
                r = w / 2.0
                svg_parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape == NodeShape.DOUBLE_CIRCLE:
                r = w / 2.0
                svg_parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')
                svg_parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{(r - 4.0):.1f}" fill="none" stroke="{colors.tag_color}" stroke-width="1.2"/>')

            elif node.shape == NodeShape.CYLINDER:
                ry_el = 8.0
                svg_parts.append(
                    f'<path d="M {x:.1f} {(y + ry_el):.1f} A {w2:.1f} {ry_el:.1f} 0 0 1 {(x + w):.1f} {(y + ry_el):.1f} '
                    f'V {(y + h - ry_el):.1f} A {w2:.1f} {ry_el:.1f} 0 0 1 {x:.1f} {(y + h - ry_el):.1f} Z" '
                    f'fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>'
                )
                svg_parts.append(f'<ellipse cx="{cx:.1f}" cy="{(y + ry_el):.1f}" rx="{w2:.1f}" ry="{ry_el:.1f}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8"/>')

            elif node.shape == NodeShape.STADIUM:
                rx_st = h / 2.0
                svg_parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx_st:.1f}" ry="{rx_st:.1f}" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape == NodeShape.ROUNDED:
                svg_parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="20" ry="20" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            elif node.shape == NodeShape.SUBROUTINE:
                svg_parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" ry="4" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')
                svg_parts.append(f'<line x1="{(x + 8.0):.1f}" y1="{y:.1f}" x2="{(x + 8.0):.1f}" y2="{(y + h):.1f}" stroke="{colors.tag_color}" stroke-width="1.5"/>')
                svg_parts.append(f'<line x1="{(x + w - 8.0):.1f}" y1="{y:.1f}" x2="{(x + w - 8.0):.1f}" y2="{(y + h):.1f}" stroke="{colors.tag_color}" stroke-width="1.5"/>')

            else:
                # Retângulo Padrão
                svg_parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" ry="6" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>')

            # Renderiza texto com suporte a múltiplas linhas (<br> ou \n)
            self._render_node_text(svg_parts, node, colors)

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def _render_node_text(self, svg_parts: List[str], node: MermaidNode, colors: ThemeColors) -> None:
        """Renderiza texto do nó com suporte a quebra em múltiplas linhas."""
        raw_lines = [l.strip() for l in re.split(r"<br\s*/?>|\n", node.label) if l.strip()]
        if not raw_lines:
            raw_lines = [node.id]

        if len(raw_lines) == 1:
            svg_parts.append(
                f'<text x="{node.x:.1f}" y="{(node.y + 4.5):.1f}" fill="{colors.h_color}" '
                f'font-family="Inter, system-ui, sans-serif" font-size="12" font-weight="600" '
                f'text-anchor="middle">{html.escape(raw_lines[0])}</text>'
            )
        else:
            line_height = 16.0
            start_y = node.y - ((len(raw_lines) - 1) * line_height) / 2.0 + 4.0
            svg_parts.append(
                f'<text x="{node.x:.1f}" y="{start_y:.1f}" fill="{colors.h_color}" '
                f'font-family="Inter, system-ui, sans-serif" font-size="11.5" font-weight="600" '
                f'text-anchor="middle">'
            )
            for i, line_text in enumerate(raw_lines):
                dy = "0" if i == 0 else f"{line_height:.1f}"
                svg_parts.append(f'<tspan x="{node.x:.1f}" dy="{dy}">{html.escape(line_text)}</tspan>')
            svg_parts.append('</text>')

    def _render_sequence_diagram(self, graph: MermaidGraph, colors: ThemeColors) -> str:
        """Gera SVG para diagramas de sequência (sequenceDiagram)."""
        participants = list(graph.participants.values())
        if not participants:
            return ""

        part_width = 140.0
        part_height = 40.0
        gap_x = 80.0
        padding = 40.0
        msg_gap_y = 50.0

        num_parts = len(participants)
        width = padding * 2 + (num_parts * part_width) + ((num_parts - 1) * gap_x)
        num_msgs = max(1, len(graph.messages))
        height = padding * 2 + (part_height * 2) + (num_msgs * msg_gap_y) + 40.0

        part_x: Dict[str, float] = {}
        curr_x = padding

        for p in participants:
            part_x[p.id] = curr_x + part_width / 2.0
            curr_x += part_width + gap_x

        svg_parts: List[str] = []
        svg_parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
            f'width="{width:.1f}" height="{height:.1f}" style="background-color: transparent;">'
        )

        svg_parts.append(
            f'<defs>'
            f'  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'    <path d="M 0 1 L 10 5 L 0 9 z" fill="{colors.tag_color}" />'
            f'  </marker>'
            f'  <filter id="shadow" x="-8%" y="-8%" width="120%" height="120%">'
            f'    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.25"/>'
            f'  </filter>'
            f'</defs>'
        )

        top_y = padding + part_height
        bot_y = height - padding - part_height

        # 1. Linhas de vida (Lifelines)
        for p in participants:
            px = part_x[p.id]
            svg_parts.append(
                f'<line x1="{px:.1f}" y1="{top_y:.1f}" x2="{px:.1f}" y2="{bot_y:.1f}" '
                f'stroke="{colors.quote_color}" stroke-width="1.5" stroke-dasharray="4,4"/>'
            )

        # 2. Mensagens
        msg_y = top_y + 35.0
        for idx, msg in enumerate(graph.messages, start=1):
            x1 = part_x.get(msg.sender, padding)
            x2 = part_x.get(msg.receiver, padding + part_width)

            dash_attr = 'stroke-dasharray="4,4"' if msg.style == "dotted" else ""
            svg_parts.append(
                f'<line x1="{x1:.1f}" y1="{msg_y:.1f}" x2="{x2:.1f}" y2="{msg_y:.1f}" '
                f'stroke="{colors.tag_color}" stroke-width="1.8" {dash_attr} marker-end="url(#arrow)"/>'
            )

            msg_label = f"[{idx}] {msg.text}" if graph.has_autonumber else msg.text
            mid_x = (x1 + x2) / 2.0
            svg_parts.append(
                f'<text x="{mid_x:.1f}" y="{(msg_y - 8.0):.1f}" fill="{colors.h_color}" '
                f'font-family="Inter, system-ui, sans-serif" font-size="11.5" font-weight="500" '
                f'text-anchor="middle">{html.escape(msg_label)}</text>'
            )

            msg_y += msg_gap_y

        # 3. Caixas de participantes (Topo e Rodapé)
        for p in participants:
            px = part_x[p.id]
            bx = px - part_width / 2.0

            # Top box
            svg_parts.append(
                f'<rect x="{bx:.1f}" y="{padding:.1f}" width="{part_width:.1f}" height="{part_height:.1f}" '
                f'rx="6" ry="6" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>'
            )
            svg_parts.append(
                f'<text x="{px:.1f}" y="{(padding + part_height / 2.0 + 4.5):.1f}" fill="{colors.h_color}" '
                f'font-family="Inter, system-ui, sans-serif" font-size="12" font-weight="600" '
                f'text-anchor="middle">{html.escape(p.label)}</text>'
            )

            # Bottom box
            svg_parts.append(
                f'<rect x="{bx:.1f}" y="{bot_y:.1f}" width="{part_width:.1f}" height="{part_height:.1f}" '
                f'rx="6" ry="6" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>'
            )
            svg_parts.append(
                f'<text x="{px:.1f}" y="{(bot_y + part_height / 2.0 + 4.5):.1f}" fill="{colors.h_color}" '
                f'font-family="Inter, system-ui, sans-serif" font-size="12" font-weight="600" '
                f'text-anchor="middle">{html.escape(p.label)}</text>'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def _render_er_diagram(self, graph: MermaidGraph, colors: ThemeColors) -> str:
        """Gera código SVG vetorial para diagramas de entidade-relacionamento (erDiagram)."""
        entities = graph.er_entities
        if not entities:
            return ""

        # 1. Calcula dimensões de cada tabela de entidade
        for entity in entities.values():
            header_chars = len(entity.name)
            max_attr_chars = 14
            for attr in entity.attributes:
                row_len = len(attr.type_name) + len(attr.name) + len(attr.key_type) + (len(attr.comment) if attr.comment else 0)
                max_attr_chars = max(max_attr_chars, row_len)

            entity.width = max(220.0, max(header_chars * 10.0 + 40.0, max_attr_chars * 7.5 + 48.0))
            row_count = max(1, len(entity.attributes))
            entity.height = 36.0 + (row_count * 24.0) + 12.0

        # 2. Distribuição em camadas (Ranks)
        in_degree: Dict[str, int] = {name: 0 for name in entities}
        adj_list: Dict[str, List[str]] = defaultdict(list)

        for rel in graph.er_relationships:
            if rel.entity2 in in_degree:
                in_degree[rel.entity2] += 1
            adj_list[rel.entity1].append(rel.entity2)

        node_layer: Dict[str, int] = {}
        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        for name in queue:
            node_layer[name] = 0

        if not queue:
            first_name = next(iter(entities))
            queue.append(first_name)
            node_layer[first_name] = 0

        visited: Set[str] = set()
        while queue:
            curr = queue.popleft()
            visited.add(curr)
            curr_layer = node_layer.get(curr, 0)
            for neighbor in adj_list[curr]:
                node_layer[neighbor] = max(node_layer.get(neighbor, 0), curr_layer + 1)
                if neighbor not in visited and neighbor not in queue:
                    queue.append(neighbor)

        for name in entities:
            if name not in node_layer:
                node_layer[name] = 0

        max_layer = max(node_layer.values()) if node_layer else 0
        layers: List[List[str]] = [[] for _ in range(max_layer + 1)]
        for name, layer_idx in node_layer.items():
            layers[layer_idx].append(name)
            entities[name].level = layer_idx

        # 3. Posicionamento 2D
        padding = 40.0
        gap_x = 50.0
        gap_y = 80.0

        max_row_w = 0.0
        layer_heights: List[float] = []

        for layer in layers:
            row_w = sum(entities[ename].width for ename in layer) + max(0, len(layer) - 1) * gap_x
            max_row_w = max(max_row_w, row_w)
            max_h = max((entities[ename].height for ename in layer), default=60.0)
            layer_heights.append(max_h)

        total_width = max_row_w + padding * 2.0
        curr_y = padding

        for layer_idx, layer in enumerate(layers):
            row_w = sum(entities[ename].width for ename in layer) + max(0, len(layer) - 1) * gap_x
            curr_x = (total_width - row_w) / 2.0
            layer_h = layer_heights[layer_idx]

            for ename in layer:
                ent = entities[ename]
                ent.x = curr_x + ent.width / 2.0
                ent.y = curr_y + ent.height / 2.0
                curr_x += ent.width + gap_x

            curr_y += layer_h + gap_y

        total_height = curr_y - gap_y + padding

        # 4. Renderização do SVG
        svg_parts: List[str] = []
        svg_parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width:.1f} {total_height:.1f}" '
            f'width="{total_width:.1f}" height="{total_height:.1f}" style="background-color: transparent;">'
        )

        svg_parts.append(
            f'<defs>'
            f'  <filter id="shadow" x="-8%" y="-8%" width="120%" height="120%">'
            f'    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.25"/>'
            f'  </filter>'
            f'</defs>'
        )

        # Relacionamentos entre entidades (Linhas e rótulos)
        for rel in graph.er_relationships:
            e1 = entities.get(rel.entity1)
            e2 = entities.get(rel.entity2)
            if not e1 or not e2:
                continue

            x1, y1 = e1.x, e1.y + e1.height / 2.0
            x2, y2 = e2.x, e2.y - e2.height / 2.0
            mid_y = (y1 + y2) / 2.0

            path_d = f"M {x1:.1f} {y1:.1f} C {x1:.1f} {mid_y:.1f}, {x2:.1f} {mid_y:.1f}, {x2:.1f} {y2:.1f}"
            dash_attr = 'stroke-dasharray="4,4"' if rel.rel_type == "dashed" else ""

            svg_parts.append(
                f'<path d="{path_d}" fill="none" stroke="{colors.tag_color}" stroke-width="1.8" {dash_attr} />'
            )

            # Rótulo de relacionamento
            label_text = rel.label or f"{rel.cardinality1} ── {rel.cardinality2}"
            label_x = (x1 + x2) / 2.0
            label_y = mid_y
            label_w = len(label_text) * 7.5 + 16.0

            svg_parts.append(
                f'<rect x="{(label_x - label_w / 2.0):.1f}" y="{(label_y - 10.0):.1f}" '
                f'width="{label_w:.1f}" height="20" rx="4" ry="4" '
                f'fill="{colors.table_header_bg}" stroke="{colors.table_border}" stroke-width="1"/>'
            )
            svg_parts.append(
                f'<text x="{label_x:.1f}" y="{(label_y + 4.0):.1f}" '
                f'fill="{colors.h_color}" font-family="Inter, system-ui, sans-serif" '
                f'font-size="11" font-weight="500" text-anchor="middle">{html.escape(label_text)}</text>'
            )

        # Desenha as tabelas de entidades
        for entity in entities.values():
            x = entity.x - entity.width / 2.0
            y = entity.y - entity.height / 2.0
            w = entity.width
            h = entity.height

            # Card de fundo
            svg_parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                f'rx="8" ry="8" fill="{colors.code_bg}" stroke="{colors.tag_color}" stroke-width="1.8" filter="url(#shadow)"/>'
            )

            # Cabeçalho da tabela
            svg_parts.append(
                f'<path d="M {x:.1f} {(y + 8.0):.1f} A 8 8 0 0 1 {(x + 8.0):.1f} {y:.1f} H {(x + w - 8.0):.1f} A 8 8 0 0 1 {(x + w):.1f} {(y + 8.0):.1f} V {(y + 32.0):.1f} H {x:.1f} Z" '
                f'fill="{colors.table_header_bg}" stroke="{colors.table_border}" stroke-width="1"/>'
            )
            svg_parts.append(
                f'<text x="{entity.x:.1f}" y="{(y + 21.0):.1f}" fill="{colors.h_color}" '
                f'font-family="Inter, system-ui, sans-serif" font-size="13" font-weight="700" '
                f'text-anchor="middle">{html.escape(entity.name)}</text>'
            )

            # Linha divisória
            svg_parts.append(
                f'<line x1="{x:.1f}" y1="{(y + 32.0):.1f}" x2="{(x + w):.1f}" y2="{(y + 32.0):.1f}" '
                f'stroke="{colors.table_border}" stroke-width="1"/>'
            )

            # Linhas de atributos
            curr_row_y = y + 50.0
            for attr in entity.attributes:
                # Tipo do atributo (cinza/muted)
                svg_parts.append(
                    f'<text x="{(x + 14.0):.1f}" y="{curr_row_y:.1f}" fill="{colors.quote_color}" '
                    f'font-family="JetBrains Mono, monospace" font-size="11">{html.escape(attr.type_name)}</text>'
                )

                # Nome do atributo (destacado)
                col_name_x = x + max(60.0, len(attr.type_name) * 7.5 + 24.0)
                svg_parts.append(
                    f'<text x="{col_name_x:.1f}" y="{curr_row_y:.1f}" fill="{colors.code_fg}" '
                    f'font-family="Inter, system-ui, sans-serif" font-size="11.5" font-weight="600">{html.escape(attr.name)}</text>'
                )

                # Badge PK / FK / UK
                if attr.key_type:
                    badge_x = x + w - 44.0
                    badge_bg = "rgba(56, 189, 248, 0.18)" if attr.key_type == "PK" else "rgba(168, 85, 247, 0.18)"
                    badge_fg = colors.tag_color if attr.key_type == "PK" else "#c084fc"

                    svg_parts.append(
                        f'<rect x="{badge_x:.1f}" y="{(curr_row_y - 12.0):.1f}" width="28" height="15" rx="3" ry="3" '
                        f'fill="{badge_bg}" stroke="{badge_fg}" stroke-width="0.8"/>'
                    )
                    svg_parts.append(
                        f'<text x="{(badge_x + 14.0):.1f}" y="{(curr_row_y - 1.0):.1f}" fill="{badge_fg}" '
                        f'font-family="JetBrains Mono, monospace" font-size="9" font-weight="700" text-anchor="middle">{attr.key_type}</text>'
                    )

                curr_row_y += 24.0

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)
