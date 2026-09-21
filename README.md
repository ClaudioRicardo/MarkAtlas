# MarkAtlas 🗺️📝

**MarkAtlas** é um leitor e editor desktop para arquivos Markdown (`.md`), focado em **Gestão de Conhecimento Pessoal (PKM - *Personal Knowledge Management*)**. 

Desenvolvido em **Python e GTK** com estilização modular em **CSS**, o MarkAtlas foi projetado para transformar notas locais em um atlas de conhecimento visual, organizado e interativo. É uma alternativa leve, rápida e com baixo consumo de memória aos softwares pesados baseados em Electron.

---

## 🌟 Principais Recursos

- **📝 Leitor e Editor de Markdown Rico**:
  - Escrita e leitura fluida com suporte completo à sintaxe Markdown.
  - Suporte a metadados e cabeçalho **YAML Frontmatter** (título, tags, data).
  - Destaque de sintaxe (*Syntax Highlighting*) para diversas linguagens de programação (Python, JavaScript, TypeScript, SQL, JSON, XML, etc.).
  - Renderização integrada de diagramas e fluxogramas **Mermaid**.
  - Suporte a listas de tarefas interativas (*checkboxes*), tabelas, citações, emojis e tags (`#tag`).
  - *Lightbox* interativo de imagens integrado com suporte a zoom in/out.

- **📁 Gestão de Cofres (Vaults) sem Lock-in**:
  - Seus dados pertencem a você: arquivos salvos diretamente como pastas e arquivos `.md` locais no seu disco.
  - **100% Offline-First e Privado**: sem dependência de nuvem, contas ou telemetria.
  - **Interoperabilidade Total**: compatível nativamente com Obsidian, VS Code, Logseq, Typora ou qualquer editor de texto.
  - Navegação visual em árvore do diretório do workspace com operações de criar, renomear e excluir arquivos e pastas.

- **🎨 Design Moderno & Temas**:
  - Interface moderna com suporte nativo a temas **Dark** e **Light**.
  - Tokens visuais e estilização via `Gtk.CssProvider`.
  - Controle de acessibilidade com ajuste dinâmico do tamanho da fonte para leitura confortável.

- **🤖 Preparado para IA e Versionamento**:
  - Projetado para fácil versionamento de conhecimento com Git e GitHub.
  - Estrutura de dados limpa e semântica ideal para ser consumida e consultada por agentes de IA e sistemas RAG.

---

## 🏛️ Arquitetura do Projeto

O MarkAtlas segue o padrão **MVC (Model-View-Controller) + Repository**, combinando tipagem estrita no Python e separação de responsabilidades guiada por **Spec-Driven Development (SDD)**:

```
markatlas/
├── assets/
│   ├── icons/                 # Ícones da interface
│   └── styles/                # Folhas de estilo CSS (main, tokens, editor, sidebar)
├── src/
│   ├── core/                  # Configurações, EventBus, StyleManager e exceções
│   ├── models/                # Entidades de domínio puras (Note, Vault, Tag, Backlink)
│   ├── repositories/          # Repositórios de persistência em disco (NoteRepository, VaultRepository)
│   ├── services/              # Casos de uso e serviços de Markdown, Mermaid e realce de sintaxe
│   ├── controllers/           # Orquestração entre Views e Serviços (WorkspaceController)
│   ├── views/                 # Widgets e componentes GTK (MainWindow, MarkdownEditor, WorkspaceTree, Lightbox)
│   └── main.py                # Ponto de entrada interno da aplicação
├── tests/
│   └── unit/                  # Cobertura abrangente de testes unitários
├── .agents/                   # Diretrizes arquiteturais, visão de produto e design system
├── main.py                    # Ponto de entrada raiz
├── pyproject.toml             # Configuração do projeto e dependências (PEP 621)
├── requirements.txt           # Lista de dependências Python
├── run.bat / run.ps1          # Scripts de inicialização rápida
└── LICENSE                    # Licença MIT
```

---

## 🚀 Como Executar

### Pré-requisitos

- **Python 3.11+**
- **GTK 3 ou GTK 4** com suporte a **PyGObject**

### 1. Clonar o Repositório

```bash
git clone https://github.com/ClaudioRicardo/MarkAtlas.git
cd MarkAtlas
```

### 2. Instalar Dependências Python

Recomenda-se o uso de um ambiente virtual:

```bash
python -m venv .venv

# No Linux/macOS:
source .venv/bin/activate

# No Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

> **Nota sobre o PyGObject no Windows**: No Windows, o GTK e PyGObject são recomendados via ambiente **MSYS2 (UCRT64)** (`pacman -S mingw-w64-ucrt-x86_64-python-gobject mingw-w64-ucrt-x86_64-gtk3`).

### 3. Iniciar a Aplicação

- **Diretamente via Python**:
  ```bash
  python main.py
  ```

- **No Windows (com MSYS2 configurado)**:
  ```cmd
  run.bat
  ```
  *ou no PowerShell:*
  ```powershell
  .\run.ps1
  ```

---

## 🧪 Executando os Testes

A suíte de testes unitários é executada com `pytest`:

```bash
pytest tests/
```

---

## 🗺️ Roadmap & Visão de Futuro

- [x] Criação, visualização, edição e exclusão de notas Markdown
- [x] Organização em árvore de diretórios e cofres locais
- [x] Suporte a metadados Frontmatter e tags
- [x] Syntax Highlighting e renderização de diagramas Mermaid
- [ ] Visualização de notas em Grafo de conexões
- [ ] Importação e conversão de múltiplos formatos (PDF, HTML, ePub) para Markdown
- [ ] Sistema de busca em texto completo e links bidirecionais (`[[Nota]]`)

---

## 📄 Licença

Este projeto está licenciado sob os termos da **Licença MIT**. Consulte o arquivo [LICENSE](LICENSE) para obter mais informações.

---

## 🤝 Contribuindo

Contribuições são bem-vindas!
1. Faça um Fork do projeto
2. Crie uma branch para a sua funcionalidade (`git checkout -b feat/minha-feature`)
3. Faça o commit das alterações (`git commit -m 'feat: adiciona nova funcionalidade'`)
4. Envie para o branch (`git push origin feat/minha-feature`)
5. Abra um Pull Request
