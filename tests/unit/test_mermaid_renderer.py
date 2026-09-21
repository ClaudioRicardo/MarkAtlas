"""Testes unitários completos para parsing, geração de SVG e renderização de diagramas Mermaid."""

import unittest
from pathlib import Path
from unittest.mock import patch

from src.services.markdown.mermaid_models import NodeShape
from src.services.markdown.mermaid_parser import MermaidParser
from src.services.markdown.mermaid_renderer import MermaidSvgGenerator
from src.services.markdown.theme_colors import ThemeColors
from src.services.markdown_service import MarkdownService


class TestMermaidRenderer(unittest.TestCase):
    """Suíte de testes para o motor de diagramas Mermaid."""

    def setUp(self):
        self.parser = MermaidParser()
        self.svg_gen = MermaidSvgGenerator()
        self.markdown_service = MarkdownService()
        self.colors_dark = ThemeColors.for_theme(is_dark=True)
        self.colors_light = ThemeColors.for_theme(is_dark=False)

    def test_parser_basic_flowchart(self):
        """Valida parsing de fluxograma simples com direção e rótulos."""
        code = """
        flowchart LR
            A[Início] -->|Avançar| B(Processamento)
            B --> C{Decisão}
            C -->|Sim| D((Fim))
            C -->|Não| E[[Sub-rotina]]
        """
        graph = self.parser.parse(code)
        self.assertIsNotNone(graph)
        self.assertEqual(graph.direction, "LR")
        self.assertEqual(len(graph.nodes), 5)
        self.assertEqual(len(graph.edges), 4)

        # Formatos dos nós
        self.assertEqual(graph.nodes["A"].shape, NodeShape.RECTANGLE)
        self.assertEqual(graph.nodes["A"].label, "Início")
        self.assertEqual(graph.nodes["B"].shape, NodeShape.ROUNDED)
        self.assertEqual(graph.nodes["C"].shape, NodeShape.DECISION)
        self.assertEqual(graph.nodes["D"].shape, NodeShape.CIRCLE)
        self.assertEqual(graph.nodes["E"].shape, NodeShape.SUBROUTINE)

        # Rótulo de aresta
        self.assertEqual(graph.edges[0].label, "Avançar")

    def test_extended_flowchart_shapes_and_quotes(self):
        """Valida formatos estendidos da especificação Mermaid e sanitização de aspas/quebras de linha."""
        code = """
        flowchart TD
            A(["Estádio / Pill"]) --> B{{Hexágono de Decisão}}
            B --> C[(Base de Dados SQL)]
            C --> D(((Círculo Duplo)))
            D --> E[/Paralelogramo/]
            E --> F[/Trapézio\\]
            F --> G["Texto com [Colchetes]<br/>Segunda Linha"]
        """
        graph = self.parser.parse(code)
        self.assertIsNotNone(graph)
        self.assertEqual(graph.nodes["A"].shape, NodeShape.STADIUM)
        self.assertEqual(graph.nodes["B"].shape, NodeShape.HEXAGON)
        self.assertEqual(graph.nodes["C"].shape, NodeShape.CYLINDER)
        self.assertEqual(graph.nodes["D"].shape, NodeShape.DOUBLE_CIRCLE)
        self.assertEqual(graph.nodes["E"].shape, NodeShape.PARALLELOGRAM)
        self.assertEqual(graph.nodes["F"].shape, NodeShape.TRAPEZOID)
        self.assertEqual(graph.nodes["G"].shape, NodeShape.RECTANGLE)
        self.assertIn("Segunda Linha", graph.nodes["G"].label)

        # Gera SVG e valida tags vetoriais
        svg = self.svg_gen.generate_svg(graph, self.colors_dark)
        self.assertIn("<ellipse", svg)
        self.assertIn("<tspan", svg)
        self.assertIn("Hexágono de Decisão", svg)

    def test_multi_node_and_inline_arrows(self):
        """Valida sintaxe de nós múltiplos 'A & B --> C & D' e conectores inline '-- texto --> '."""
        code = """
        flowchart TD
            A & B -->|Paralelo| C & D
            C -- Conexão Inline --> E
            D == Espessa ==> E
            E -. Pontilhada .-> F
        """
        graph = self.parser.parse(code)
        self.assertIsNotNone(graph)
        self.assertEqual(len(graph.nodes), 6)
        # 4 arestas cruzadas de A&B -> C&D + 3 arestas subsequentes = 7
        self.assertEqual(len(graph.edges), 7)

        # Valida estilos de aresta
        edge_labels = [e.label for e in graph.edges]
        self.assertIn("Conexão Inline", edge_labels)
        self.assertIn("Espessa", edge_labels)
        self.assertIn("Pontilhada", edge_labels)

    def test_subgraph_parsing_and_rendering(self):
        """Valida agrupamento por subgrafos (subgraph ... end)."""
        code = """
        flowchart TD
            subgraph Frontend [Camada Web / Mobile]
                A[React App] --> B[API Gateway]
            end
            subgraph Backend [Serviços Centrais]
                B --> C[Auth Service]
                C --> D[(PostgreSQL)]
            end
        """
        graph = self.parser.parse(code)
        self.assertIsNotNone(graph)
        self.assertEqual(len(graph.subgraphs), 2)
        self.assertEqual(graph.subgraphs[0].title, "Camada Web / Mobile")
        self.assertEqual(graph.subgraphs[1].title, "Serviços Centrais")

        svg = self.svg_gen.generate_svg(graph, self.colors_dark)
        self.assertIn("Camada Web / Mobile", svg)
        self.assertIn("Serviços Centrais", svg)

    def test_sequence_diagram_parsing_and_rendering(self):
        """Valida diagramas de sequência completos (sequenceDiagram)."""
        code = """
        sequenceDiagram
            autonumber
            actor User as Usuário Final
            participant App as Web App
            participant API as Gateway API
            participant DB as Base de Dados

            User->>App: 1. Acessa Sistema
            App->>API: 2. Solicita Token JWT
            API->>DB: 3. Consulta Usuário
            DB-->>API: 4. Retorna Registro
            API-->>App: 5. Emite Token
            App-->>User: 6. Login Concluído com Sucesso
        """
        graph = self.parser.parse(code)
        self.assertIsNotNone(graph)
        self.assertEqual(graph.diagram_type, "sequence")
        self.assertTrue(graph.has_autonumber)
        self.assertEqual(len(graph.participants), 4)
        self.assertEqual(len(graph.messages), 6)

        svg = self.svg_gen.generate_svg(graph, self.colors_dark)
        self.assertIn("<svg", svg)
        self.assertIn("Usuário Final", svg)
        self.assertIn("Gateway API", svg)
        self.assertIn("Solicita Token JWT", svg)

    def test_user_authentication_flowchart(self):
        """Valida o diagrama completo de autenticação fornecido pelo usuário."""
        code = """
        flowchart TD
            ClientApp[Aplicação Cliente - React / Mobile / B2B] -->|1. Envia X-API-Key| Gatekeeper[Camada 1: Client Authorization]
            Gatekeeper -->|Chave Inválida / Ausente| DenyClient[401 Unauthorized - Cliente não autorizado]
            Gatekeeper -->|Chave Válida| UserGate[Camada 2: User Authorization & RBAC]
            
            UserGate -->|Rota Pública / Login| PublicExec[Execução da Rota Pública]
            UserGate -->|Rota Protegida + JWT / Cookie| CheckRoles[Validação de Papéis e Permissões]
            CheckRoles -->|Permissão OK| PrivateExec[Execução do Endpoint]
            CheckRoles -->|Sem Permissão| DenyUser[403 Forbidden - Acesso Negado]
        """
        graph = self.parser.parse(code)
        self.assertIsNotNone(graph)
        self.assertEqual(graph.direction, "TD")
        self.assertEqual(len(graph.nodes), 8)
        self.assertEqual(len(graph.edges), 7)

        # Valida que todos os nós e arestas chave foram identificados
        self.assertIn("ClientApp", graph.nodes)
        self.assertIn("Gatekeeper", graph.nodes)
        self.assertIn("DenyClient", graph.nodes)
        self.assertIn("UserGate", graph.nodes)
        self.assertIn("CheckRoles", graph.nodes)
        self.assertIn("DenyUser", graph.nodes)

        # Gera SVG para os temas Dark e Light
        svg_dark = self.svg_gen.generate_svg(graph, self.colors_dark)
        self.assertIn("<svg", svg_dark)
        self.assertIn("</svg>", svg_dark)
        self.assertIn("Aplicação Cliente", svg_dark)
        self.assertIn("401 Unauthorized", svg_dark)
        self.assertIn("403 Forbidden", svg_dark)
        self.assertIn(self.colors_dark.tag_color, svg_dark)

        svg_light = self.svg_gen.generate_svg(graph, self.colors_light)
        self.assertIn("<svg", svg_light)
        self.assertIn(self.colors_light.tag_color, svg_light)

    def test_markdown_service_mermaid_block_integration(self):
        """Valida que o MarkdownService renderiza blocos de código mermaid gerando SVG em cache."""
        md = "## Fluxo de Autorização\n\n```mermaid\nflowchart TD\n    A[Start] --> B[End]\n```\n\nTexto final."
        pango = self.markdown_service.render_to_pango(md, is_dark=True)

        self.assertIn("[ MERMAID DIAGRAM ]", pango)
        self.assertIn("🖼️ [Mermaid:", pango)
        self.assertIn(".svg", pango)
        self.assertIn("Texto final.", pango)

    def test_user_er_diagram_rbac(self):
        """Valida o diagrama de Entidade-Relacionamento (erDiagram) fornecido pelo usuário."""
        code = """
        erDiagram
            USERS ||--o{ USER_ROLES : "possui"
            ROLES ||--o{ USER_ROLES : "pertence a"
            ROLES ||--o{ ROLE_PERMISSIONS : "contém"
            PERMISSIONS ||--o{ ROLE_PERMISSIONS : "atribuída a"

            USERS {
                uuid id PK
                string name
                string email
                string password_hash
            }

            ROLES {
                uuid id PK
                string name UK "ex: admin, manager, user"
                string description
            }

            PERMISSIONS {
                uuid id PK
                string name UK "ex: users:read, users:delete"
                string resource "ex: users, roles, reports"
                string action "ex: read, write, delete"
                string description
            }

            USER_ROLES {
                uuid user_id FK
                uuid role_id FK
            }

            ROLE_PERMISSIONS {
                uuid role_id FK
                uuid permission_id FK
            }
        """
        graph = self.parser.parse(code)
        self.assertIsNotNone(graph)
        self.assertEqual(graph.diagram_type, "erDiagram")
        self.assertEqual(len(graph.er_entities), 5)
        self.assertEqual(len(graph.er_relationships), 4)

        # Valida entidades e atributos
        self.assertIn("USERS", graph.er_entities)
        self.assertEqual(len(graph.er_entities["USERS"].attributes), 4)
        self.assertEqual(graph.er_entities["USERS"].attributes[0].key_type, "PK")

        self.assertIn("PERMISSIONS", graph.er_entities)
        self.assertEqual(len(graph.er_entities["PERMISSIONS"].attributes), 5)
        self.assertEqual(graph.er_entities["PERMISSIONS"].attributes[1].key_type, "UK")

        # Gera SVG para Dark e Light
        svg_dark = self.svg_gen.generate_svg(graph, self.colors_dark)
        self.assertIn("<svg", svg_dark)
        self.assertIn("USERS", svg_dark)
        self.assertIn("ROLE_PERMISSIONS", svg_dark)
        self.assertIn("password_hash", svg_dark)
        self.assertIn("possui", svg_dark)
        self.assertIn("PK", svg_dark)

        # Valida integração no MarkdownService
        md = f"```mermaid\n{code}\n```"
        pango = self.markdown_service.render_to_pango(md, is_dark=True)
        self.assertIn("[ MERMAID DIAGRAM ]", pango)
        self.assertIn("🖼️ [Mermaid:", pango)

    def test_mermaid_cli_bridge_availability_and_fallback(self):
        """Valida que a ponte CLI detecta Node.js/npx no PATH (sem invocar a CLI de verdade)."""
        from src.services.markdown.mermaid_cli_bridge import MermaidCliBridge
        bridge = MermaidCliBridge()
        # Valida apenas a detecção do executável, sem chamar o processo
        self.assertTrue(bridge.is_available)

    def test_mermaid_syntax_fallback(self):
        """Valida que código mermaid inválido exibe fallback formatado sem lançar erro."""
        # Mocka a ponte CLI para não invocar npx durante testes unitários
        with patch(
            "src.services.markdown.block_parser.MermaidCliBridge.render_to_svg_file",
            return_value=None,
        ):
            md = "```mermaid\nSintaxe Totalmente Inválida Sem Nós\n```"
            pango = self.markdown_service.render_to_pango(md, is_dark=True)

        self.assertIn("[ MERMAID ]", pango)
        self.assertIn("Sintaxe Totalmente Inválida", pango)


if __name__ == "__main__":
    unittest.main()
