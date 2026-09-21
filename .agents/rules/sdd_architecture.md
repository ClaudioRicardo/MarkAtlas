# Regra de Desenvolvimento: SDD, Arquitetura MVC + Repository e Stack Desktop (MarkAtlas)

Esta regra define os padrões arquiteturais, a stack tecnológica, a organização modular e o fluxo de **Spec-Driven Development (SDD)** para o desenvolvimento da aplicação desktop **MarkAtlas**.

---

## 1. Visão Geral e Princípios do SDD (Spec-Driven Development)

1. **Especificação em Primeiro Lugar (Spec-First)**:
   - Nenhuma funcionalidade ou alteração estrutural deve ser codificada sem antes definir ou atualizar a especificação em `openspec/`.
   - Cada especificação deve descrever o domínio, requisitos funcionais (RF), requisitos não-funcionais (RNF), cenários e contratos de interface.
2. **Orientação a Objetos (OOP) e SOLID**:
   - Todo o código deve ser modular, orientado a objetos, com responsabilidade única e baixo acoplamento.
   - O uso de interfaces abstratas (`abc.ABC`) é obrigatório para desacoplar a camada de persistência e serviços.
3. **Inversão e Injeção de Dependências**:
   - Controllers e Services recebem suas dependências (Repositórios e Serviços) via construtor (`__init__`), facilitando testes unitários e mocks.
4. **Separação Rígida de Camadas (MVC + Repository)**:
   - A camada visual (GTK) nunca deve ler/escrever arquivos ou manipular markdown diretamente.
   - A camada de domínio/modelo não deve importar componentes do GTK.

---

## 2. Stack Tecnológica

| Componente | Tecnologia / Biblioteca | Finalidade |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.11+ | Linguagem base com tipagem estrita (`typing`, `dataclasses`) |
| **Interface Gráfica (GUI)** | PyGObject (`gi.repository.Gtk`) | Framework de UI nativo e performático |
| **Estilização** | CSS Modular (`Gtk.CssProvider`) | Customização visual moderna, dark mode, temas e componentes |
| **Markdown Parsing** | `python-frontmatter` + `mistune` / `markdown-it-py` | Extração de metadados (YAML frontmatter) e renderização/AST |
| **Indexação & Busca** | SQLite (FTS5) ou Repositório em Memória | Busca textual rápida, rastreamento de links internos e tags |
| **Testes Unitários** | `pytest`, `pytest-mock` | Testes de modelos, repositórios, serviços e controllers |

---

## 3. Estrutura Modular de Pastas

```text
MarkAtlas/
├── .agents/
│   └── rules/
│       └── sdd_architecture.md     # Esta regra arquitetural
├── openspec/
│   ├── config.yaml                 # Configuração do OpenSpec
│   ├── specs/                      # Especificações principais (Main Specs)
│   └── changes/                    # Mudanças ativas (Proposals, Deltas, Tasks)
├── assets/
│   ├── icons/                      # Ícones da aplicação (SVG / PNG)
│   └── styles/                     # Folhas de estilo CSS modulares
│       ├── main.css                # CSS global e variáveis de cores/tipografia
│       ├── sidebar.css             # Estilos da árvore de notas e navegação
│       ├── editor.css              # Estilos da área de edição/visualização
│       └── components.css          # Botões, inputs, tags, badges, diálogos
├── src/
│   ├── __init__.py
│   ├── main.py                     # Entry point da aplicação (Gtk.Application)
│   │
│   ├── core/                       # Núcleo da aplicação
│   │   ├── __init__.py
│   │   ├── config.py               # Configurações globais e preferências
│   │   ├── style_manager.py        # Carregador e gerenciador de CSS (Gtk.CssProvider)
│   │   └── events.py               # Sistema de eventos / barramento (Event Bus ou Signals)
│   │
│   ├── models/                     # Entidades puras de domínio (OOP, Dataclasses)
│   │   ├── __init__.py
│   │   ├── note.py                 # Modelo da Nota (caminho, título, frontmatter, corpo)
│   │   ├── tag.py                  # Modelo de Tags/Categorias
│   │   ├── backlink.py             # Modelo de ligações entre notas [[link]]
│   │   └── vault.py                # Modelo do diretório raiz / cofre de notas
│   │
│   ├── repositories/               # Camada de Acesso a Dados (Repository Pattern)
│   │   ├── __init__.py
│   │   ├── base.py                 # Interfaces abstratas (NoteRepositoryInterface, etc.)
│   │   ├── markdown_repository.py  # Implementação que lê/escreve arquivos .md em disco
│   │   ├── frontmatter_parser.py   # Parser e serializer de metadados YAML
│   │   └── search_repository.py    # Repositório de busca e indexação
│   │
│   ├── services/                   # Camada de Negócio / Casos de Uso (Use Cases)
│   │   ├── __init__.py
│   │   ├── note_service.py         # Criação, edição, exclusão, renomeação de notas
│   │   ├── vault_service.py        # Abertura e varredura do diretório de notas
│   │   ├── search_service.py       # Lógica de consulta por texto, tags e backlinks
│   │   └── graph_service.py        # Construção da rede de conexões entre arquivos
│   │
│   ├── controllers/                # Camada Controladora (MVC)
│   │   ├── __init__.py
│   │   ├── main_controller.py      # Orquestrador da janela principal e ciclo de vida
│   │   ├── sidebar_controller.py   # Controle da navegação, árvore de arquivos e tags
│   │   ├── editor_controller.py    # Controle do editor/preview de Markdown
│   │   └── search_controller.py    # Controle da barra de pesquisa e filtros
│   │
│   └── views/                      # Camada de Visualização (GTK Widgets)
│       ├── __init__.py
│       ├── main_window.py          # Janela principal da aplicação (Gtk.ApplicationWindow)
│       ├── components/             # Componentes visuais reutilizáveis
│       │   ├── __init__.py
│       │   ├── note_tree.py        # Widget de árvore de diretórios/notas
│       │   ├── tag_list.py         # Widget com lista de tags clicáveis
│       │   ├── search_bar.py       # Widget de busca rápida
│       │   └── status_bar.py       # Barra de status no rodapé
│       ├── editor_view.py          # Visualizador / Editor de texto GTK com suporte a CSS
│       └── dialogs/                # Janelas de diálogo modais (Configurações, Sobre, etc.)
│
├── tests/                          # Testes automatizados (Pytest)
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_repositories.py
│   │   └── test_services.py
│   └── integration/
│       └── test_controllers.py
├── pyproject.toml / requirements.txt
└── README.md
```

---

## 4. Padrão Arquitetural Detalhado: MVC + Repository

### 4.1. Models (`src/models/`)
- Representam as entidades e regras de negócio essenciais.
- Devem usar `dataclass` ou classes com propriedades tipadas (`@property`).
- Totalmente agnósticos a UI e banco/arquivos físicos.

```python
# Exemplo conceitual: src/models/note.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

@dataclass
class Note:
    path: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### 4.2. Repositories (`src/repositories/`)
- Abstraem o armazenamento (disco, SQLite, cache).
- Definem contratos via `ABC` (Interface Segregation).

```python
# Exemplo conceitual: src/repositories/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.note import Note

class NoteRepositoryInterface(ABC):
    @abstractmethod
    def get_by_path(self, path: str) -> Optional[Note]:
        pass

    @abstractmethod
    def save(self, note: Note) -> bool:
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        pass

    @abstractmethod
    def list_all(self) -> List[Note]:
        pass
```

### 4.3. Services (`src/services/`)
- Implementam os Casos de Uso da aplicação.
- Orquestram repositórios, validações e transformações de dados.

```python
# Exemplo conceitual: src/services/note_service.py
from src.repositories.base import NoteRepositoryInterface
from src.models.note import Note

class NoteService:
    def __init__(self, repository: NoteRepositoryInterface):
        self._repository = repository

    def create_note(self, title: str, folder_path: str, content: str = "") -> Note:
        # Regras de negócio, sanitização de nome de arquivo, criação de frontmatter
        ...
```

### 4.4. Controllers (`src/controllers/`)
- Intermediam a comunicação entre a View (eventos de usuário/sinais GTK) e os Services.
- Mantêm o estado da interface se necessário e disparam atualizações visuais.

```python
# Exemplo conceitual: src/controllers/editor_controller.py
class EditorController:
    def __init__(self, note_service: NoteService, editor_view):
        self._note_service = note_service
        self._view = editor_view
        self._current_note = None

    def on_note_selected(self, note_path: str):
        note = self._note_service.get_note(note_path)
        self._current_note = note
        self._view.display_note(note)

    def on_save_requested(self, content: str):
        if self._current_note:
            self._note_service.update_content(self._current_note.path, content)
```

### 4.5. Views (`src/views/`) e Estilização com CSS
- Componentes visuais baseados em PyGObject (`Gtk.Box`, `Gtk.Window`, `Gtk.TextView`, `Gtk.TreeView` / `Gtk.ListView`).
- Os widgets devem receber classes CSS (`get_style_context().add_class(...)`) ou nomes/IDs (`set_name(...)`) para estilização declarativa.
- O `StyleManager` injeta os arquivos CSS na tela usando `Gtk.CssProvider`.

```python
# Exemplo conceitual: src/core/style_manager.py
import gi
gi.require_version("Gtk", "3.0")  # ou "4.0" conforme versão adotada
from gi.repository import Gtk, Gdk

class StyleManager:
    @staticmethod
    def load_styles(css_paths: list[str]) -> None:
        screen = Gdk.Screen.get_default()
        for path in css_paths:
            provider = Gtk.CssProvider()
            provider.load_from_path(path)
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
```

---

## 5. Diretrizes de Qualidade e Boas Práticas

1. **Tipagem Estrita**: Usar `typing` (`Optional`, `List`, `Dict`, `Callable`, `Protocol`) em todas as assinaturas de métodos e funções.
2. **Tratamento de Exceções**: Criar exceções de domínio customizadas em `src/core/exceptions.py` (ex: `NoteNotFoundError`, `InvalidFrontmatterError`).
3. **Modularidade no CSS**: Evitar arquivos CSS monolíticos. Separar por componente/área (`sidebar.css`, `editor.css`, etc.) com variáveis de cor para suportar temas claro e escuro.
4. **Isolamento de Testes**: Testes de Services e Controllers devem rodar sem abrir janelas GTK reais (usando mocks para Views e Repositórios).
