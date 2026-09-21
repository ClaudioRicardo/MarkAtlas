r"""Testes de diagnóstico para identificar problemas nos parsers Mermaid.

Execute com:
    .venv/Scripts/python.exe tests/unit/test_mermaid_diagnostics.py
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.markdown.mermaid_parser import MermaidParser
from src.services.markdown.mermaid_renderer import MermaidSvgGenerator
from src.services.markdown.theme_colors import ThemeColors


parser = MermaidParser()
gen = MermaidSvgGenerator()
dark = ThemeColors.for_theme(is_dark=True)
ok = 0
fail = 0


def check(name: str, code: str, expect_type: str | None, assertions: list[tuple[str, callable]] = []) -> None:
    global ok, fail
    graph = parser.parse(code)
    if expect_type is None:
        if graph is None:
            print(f"  ✅ {name}")
            ok += 1
        else:
            print(f"  ❌ {name} — esperava None, got {graph.diagram_type}")
            fail += 1
        return

    if graph is None:
        print(f"  ❌ {name} — parser retornou None (esperava {expect_type})")
        fail += 1
        return

    if graph.diagram_type != expect_type:
        print(f"  ❌ {name} — tipo errado: {graph.diagram_type} (esperava {expect_type})")
        fail += 1
        return

    # Gera SVG e verifica que não levanta exceção
    try:
        svg = gen.generate_svg(graph, dark)
    except Exception as e:
        print(f"  ❌ {name} — SVG crash: {e}")
        fail += 1
        return

    errors = []
    for label, fn in assertions:
        try:
            result = fn(graph, svg)
            if result is False:
                errors.append(label)
        except Exception as e:
            errors.append(f"{label} (exception: {e})")

    if errors:
        print(f"  ❌ {name}")
        for e in errors:
            print(f"       • {e}")
        fail += 1
    else:
        print(f"  ✅ {name}")
        ok += 1


# ─── FLOWCHART ───────────────────────────────────────────────────────────────
print("\n── Flowchart básico ──")
check("TD básico", """
flowchart TD
    A[Start] --> B[End]
""", "flowchart",
    [("2 nós", lambda g, _: len(g.nodes) == 2),
     ("1 aresta", lambda g, _: len(g.edges) == 1)])

check("LR com rótulo pipe", """
flowchart LR
    A[Input] -->|process| B[Output]
""", "flowchart",
    [("direção LR", lambda g, _: g.direction == "LR"),
     ("rótulo 'process'", lambda g, _: g.edges[0].label == "process")])

check("Múltiplos nós &", """
flowchart TD
    A & B --> C & D
""", "flowchart",
    [("4 nós", lambda g, _: len(g.nodes) == 4),
     ("4 arestas (produto cartesiano)", lambda g, _: len(g.edges) == 4)])

check("Formas especiais: {}, {{}}, [()], (())", """
flowchart TD
    A{Decision} --> B{{Hex}} --> C[(DB)] --> D((Circle))
""", "flowchart",
    [("4 nós", lambda g, _: len(g.nodes) == 4),
     ("A é DECISION", lambda g, _: g.nodes["A"].shape.value == "decision"),
     ("B é HEXAGON", lambda g, _: g.nodes["B"].shape.value == "hexagon"),
     ("C é CYLINDER", lambda g, _: g.nodes["C"].shape.value == "cylinder"),
     ("D é CIRCLE", lambda g, _: g.nodes["D"].shape.value == "circle")])

check("Seta -- Texto --> (inline label)", """
flowchart TD
    A -- Passo importante --> B
""", "flowchart",
    [("rótulo 'Passo importante'", lambda g, _: g.edges[0].label == "Passo importante")])

check("Seta pontilhada -.->", """
flowchart TD
    A -.-> B
""", "flowchart",
    [("estilo dotted", lambda g, _: g.edges[0].style == "dotted")])

check("Seta espessa ==>", """
flowchart TD
    A ==> B
""", "flowchart",
    [("estilo thick", lambda g, _: g.edges[0].style == "thick")])

check("Sem cabeçalho com setas", """
A --> B --> C
""", "flowchart",
    [("3 nós", lambda g, _: len(g.nodes) == 3)])

check("Subgraph", """
flowchart TD
    subgraph sg1 [Grupo]
        A --> B
    end
    B --> C
""", "flowchart",
    [("3 nós", lambda g, _: len(g.nodes) == 3),
     ("1 subgrafo", lambda g, _: len(g.subgraphs) == 1)])

check("Rótulo com & interno", """
flowchart TD
    A[Auth & RBAC] --> B[API]
""", "flowchart",
    [("rótulo preservado", lambda g, _: "Auth & RBAC" in g.nodes["A"].label)])

check("Nó em aspas com caracteres especiais", r"""
flowchart LR
    A["Cliente [Web]"] --> B["API (v2)"]
""", "flowchart",
    [("rótulo sem aspas externas A", lambda g, _: g.nodes["A"].label == "Cliente [Web]"),
     ("rótulo sem aspas externas B", lambda g, _: g.nodes["B"].label == "API (v2)")])

# ─── SEQUENCE DIAGRAM ─────────────────────────────────────────────────────────
print("\n── sequenceDiagram ──")
check("Básico", """
sequenceDiagram
    Alice->>Bob: Olá
    Bob-->>Alice: Resposta
""", "sequence",
    [("2 participantes", lambda g, _: len(g.participants) == 2),
     ("2 mensagens", lambda g, _: len(g.messages) == 2)])

check("Com autonumber e actor", """
sequenceDiagram
    autonumber
    actor U as Usuário
    participant S as Servidor
    U->>S: Login
    S-->>U: Token
""", "sequence",
    [("autonumber ativo", lambda g, _: g.has_autonumber is True),
     ("Usuário é actor", lambda g, _: g.participants["U"].is_actor is True),
     ("label Usuário", lambda g, _: g.participants["U"].label == "Usuário"),
     ("SVG contém Usuário", lambda g, s: "Usuário" in s)])

# ─── ER DIAGRAM ───────────────────────────────────────────────────────────────
print("\n── erDiagram ──")
check("Básico com entidades e relacionamentos", """
erDiagram
    USERS ||--o{ ORDERS : "faz"
    USERS {
        uuid id PK
        string name
        string email
    }
    ORDERS {
        uuid id PK
        uuid user_id FK
        string item
    }
""", "erDiagram",
    [("2 entidades", lambda g, _: len(g.er_entities) == 2),
     ("1 relacionamento", lambda g, _: len(g.er_relationships) == 1),
     ("USERS tem 3 atributos", lambda g, _: len(g.er_entities["USERS"].attributes) == 3),
     ("id é PK", lambda g, _: g.er_entities["USERS"].attributes[0].key_type == "PK"),
     ("SVG contém USERS", lambda g, s: "USERS" in s),
     ("SVG contém PK badge", lambda g, s: "PK" in s)])

check("Relacionamento com comentário em atributo", """
erDiagram
    ROLES {
        uuid id PK
        string name UK "ex: admin"
        string description
    }
""", "erDiagram",
    [("name tem chave UK", lambda g, _: g.er_entities["ROLES"].attributes[1].key_type == "UK"),
     ("comentário capturado", lambda g, _: "admin" in g.er_entities["ROLES"].attributes[1].comment)])

# ─── CASOS DE BORDA / EDGE CASES ─────────────────────────────────────────────
print("\n── Edge cases: sintaxes que costumam falhar ──")

# classDiagram (não suportado nativamente) - deve retornar None e não crashar
check("classDiagram retorna None (sem suporte nativo)", """
classDiagram
    class Animal {
        +String name
        +speak() void
    }
    Animal <|-- Dog
""", None)

# stateDiagram-v2 (não suportado nativamente) - deve retornar None
check("stateDiagram-v2 retorna None (sem suporte nativo)", """
stateDiagram-v2
    [*] --> Idle
    Idle --> Running : start
    Running --> [*] : stop
""", None)

# pie (não suportado nativamente) - deve retornar None
check("pie retorna None (sem suporte nativo)", """
pie title Exemplo
    "Fatia A" : 40
    "Fatia B" : 60
""", None)

# gitGraph (não suportado nativamente) - deve retornar None
check("gitGraph retorna None (sem suporte nativo)", """
gitGraph
    commit
    branch feature
    checkout feature
    commit
    checkout main
    merge feature
""", None)

# Flowchart com nó de ID numérico (ex: 1 como ID)
check("Nos com IDs alfanumericos tipo ID1", """
flowchart LR
    id1[Login Page] --> id2{Valid?}
    id2 -->|Yes| id3[Dashboard]
    id2 -->|No| id1
""", "flowchart",
    [("3 nos", lambda g, _: len(g.nodes) == 3),
     ("3 arestas (inclui ciclo id2->id1)", lambda g, _: len(g.edges) == 3)])

# Flowchart com direção BT
check("Flowchart BT", """
flowchart BT
    A --> B --> C
""", "flowchart",
    [("direção BT", lambda g, _: g.direction == "BT"),
     ("3 nós", lambda g, _: len(g.nodes) == 3)])

# Flowchart com direção RL
check("Flowchart RL", """
flowchart RL
    A --> B --> C
""", "flowchart",
    [("direção RL", lambda g, _: g.direction == "RL")])

# Sequência com +/- (não implementado ainda, não deve crashar)
check("sequenceDiagram com activate/deactivate (não deve crashar)", """
sequenceDiagram
    Alice->>Bob: Request
    activate Bob
    Bob-->>Alice: Response
    deactivate Bob
""", "sequence",
    [("2 participantes", lambda g, _: len(g.participants) == 2),
     ("2 mensagens", lambda g, _: len(g.messages) == 2)])

# Flowchart com classDef/class/style (devem ser ignorados sem crash)
check("Flowchart com classDef é ignorado sem crash", """
flowchart TD
    A[Start]:::redStyle --> B[End]
    classDef redStyle fill:#f00
    class A redStyle
""", "flowchart",
    [("nós presentes", lambda g, _: len(g.nodes) >= 2)])

# Sequence com múltiplos tipos de seta
check("sequenceDiagram com ->> e --> e -->>", """
sequenceDiagram
    A->>B: Sync request
    B-->A: Old style
    B-->>A: Async reply
""", "sequence",
    [("3 mensagens", lambda g, _: len(g.messages) == 3),
     ("1a seta é solid", lambda g, _: g.messages[0].style == "solid"),
     ("2a seta é dotted", lambda g, _: g.messages[1].style == "dotted")])

# Flowchart com nó reutilizado em múltiplas conexões
check("Nó reutilizado não perde rótulo rico", """
flowchart TD
    Auth[Autenticação & Autorização] --> API[REST API]
    API --> DB[(PostgreSQL)]
    API --> Cache[(Redis)]
""", "flowchart",
    [("4 nós", lambda g, _: len(g.nodes) == 4),
     ("rótulo Auth preservado", lambda g, _: "Autenticação & Autorização" in g.nodes["Auth"].label),
     ("DB é CYLINDER", lambda g, _: g.nodes["DB"].shape.value == "cylinder")])

# ─── FALLBACK ─────────────────────────────────────────────────────────────────
print("\n── Fallbacks ──")
check("Tipo desconhecido retorna None", """
pie title Distribuição
    "A" : 40
    "B" : 60
""", None)

check("Código vazio retorna None", "", None)

check("Apenas comentários retorna None", """
%% apenas comentário
%% outra linha
""", None)

# ─── RESULTADO FINAL ──────────────────────────────────────────────────────────
total = ok + fail
print(f"\n{'='*50}")
print(f"  Resultado: {ok}/{total} testes passando")
if fail:
    print(f"  FALHAS: {fail} precisam de correcao")
else:
    print("  Todos passando!")
print('='*50)

