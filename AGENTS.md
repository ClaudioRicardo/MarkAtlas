# Diretrizes do Projeto MarkAtlas

Este projeto segue a metodologia **Spec-Driven Development (SDD)** com **OpenSpec** e adota o padrão de arquitetura **MVC + Repository** em **Python (PyGObject/GTK)** com estilização em **CSS**.

Para a regra arquitetural completa e detalhada, consulte [.agents/rules/sdd_architecture.md](file:///c:/Users/claud/Projetos/MSV/MarkAtlas/.agents/rules/sdd_architecture.md).
Para as diretrizes de estilos, tokens e compatibilidade de UI/GTK, consulte [.agents/rules/design_system.md](file:///c:/Users/claud/Projetos/MSV/MarkAtlas/.agents/rules/design_system.md).
Para as regras de qualidade, encapsulamento e boas práticas, consulte [.agents/rules/code_quality_guidelines.md](file:///c:/Users/claud/Projetos/MSV/MarkAtlas/.agents/rules/code_quality_guidelines.md).
Para a visão funcional e estratégica do produto, consulte [.agents/overview_projeto.md](file:///c:/Users/claud/Projetos/MSV/MarkAtlas/.agents/overview_projeto.md).

---

## Resumo Rápido

1. **Stack**:
   - Python 3.11+ (POO, Dataclasses, tipagem estrita com `typing`).
   - PyGObject / GTK (GTK 3 ou GTK 4).
   - Estilização via `Gtk.CssProvider` e `Gtk.StyleContext` com arquivos CSS em `assets/styles/`.
   - Parsing de Markdown e metadados via `python-frontmatter` e `mistune` / `markdown-it-py`.
2. **Camadas**:
   - `src/models/`: Entidades de domínio puras.
   - `src/repositories/`: Contratos abstratos (`base.py`) e implementações de I/O em disco/SQLite.
   - `src/services/`: Casos de uso e regras de negócio orquestrando repositórios.
   - `src/controllers/`: Manipuladores de eventos de UI e comunicação entre Views e Services.
   - `src/views/`: Widgets GTK e layouts, decorados com classes CSS.
   - `src/core/`: Configurações, gerenciador de estilos (`StyleManager`) e eventos.
3. **Fluxo SDD**:
   - Planejar via OpenSpec (`openspec/`): Proposta -> Especificação com contratos -> Tarefas -> Implementação -> Testes.
