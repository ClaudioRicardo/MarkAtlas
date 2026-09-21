# MarkAtlas - Visão Geral do Projeto (Overview)

> Este documento serve como referência estratégica e funcional para guiar a arquitetura, especificações OpenSpec (SDD) e a implementação do MarkAtlas.

---

## 1. Visão & Propósito

- **O que é o MarkAtlas:**
  <!-- Descreva em 1 ou 2 parágrafos o conceito central do MarkAtlas. -->
  MarkAtlas é uma ferramenta de gestão de conhecimento (PKM - Personal Knowledge Management) construída com Python e GTK4, projetada para transformar notas em Markdown em um "atlas" visual e interativo. Com foco em privacidade (offline-first), leveza e arquitetura limpa baseada em OpenSpec, ele oferece uma experiência fluida para captura, organização e exploração de conhecimento de forma não linear.

  Com o MarkAtlas poderá:
  * Escrever, ler e editar arquivos Markdown
  * Organizar em diretórios
  * Conectar documentos marcados com Tags
  * Visualizar seus documentos como um Atlas
  * Cosumir fontes de dados PDF,HTML, Markdown, EPub, etc. Convertendo-os para Markdown, e organizando em diretórios.
  * Visualizar cada documento em Markdown com interface própria.
  * Visualizar documentos como grafo.
  * Consultar documentos e termos presentes nos documentos
  Obs.: Eu pretendo usar o github para versionar essa base de conhecimento
  Obs.: Essa base de conhecimento poderá ser utilizada por sistemas e agentes de IA para responderem perguntas, consultas e realizar tarefas.

- **Qual problema/dor ele resolve:**
  <!-- Ex: Dificuldade de organizar conhecimento de forma visual e local, dependência de ferramentas em nuvem, lentidão de softwares baseados em Electron, etc. -->
  O MarkAtlas resolve a dificuldade de organizar conhecimento de forma visual e local, combatendo a fragmentação de informações e a dependência de ferramentas baseadas em nuvem. Ao oferecer uma alternativa leve (Python + GTK), ele proporciona uma experiência de uso mais rápida e focada, onde o usuário tem total controle e privacidade sobre seus dados, sem distrações ou performance comprometida.

- **Proposta de Valor:**
  <!-- O que torna o MarkAtlas único e especial? -->
  Uma ferramenta leve, rápida, flexível e personalizável para gerenciar conhecimento de forma visual e interativa. Com foco em privacidade, interoperabilidade e arquitetura limpa, ele
  se destaca pela combinação de experiência fluida, design moderno e visão estratégica de futuro, onde o conhecimento se torna um recurso valioso para agentes de IA.

---

## 2. Público-Alvo & Casos de Uso Principais

- **Público-Alvo / Perfil de Usuário:**
  <!-- Quem usará o MarkAtlas? (Ex: desenvolvedores, pesquisadores, estudantes, escritores) -->
  Desenvolvedores, pesquisadores, estudantes, escritores, qualquer pessoa que precise organizar conhecimento de forma visual e interativa.

- **Cenários do Dia a Dia (User Stories / Jornadas):**
  <!-- 
  1. Criação rápida de notas diárias ou de reuniões.
  2. Conexão de ideias e conceitos através de links bidirecionais.
  3. Navegação espacial/visual por tópicos de um projeto.
  -->
  Com o MarkAtlas poderá:
  * Escrever, ler e editar arquivos Markdown
  * Organizar em diretórios
  * Conectar documentos marcados com Tags
  * Visualizar seus documentos como um Atlas
  * Cosumir fontes de dados PDF,HTML, Markdown, EPub, etc. Convertendo-os para Markdown, e organizando em diretórios.
  * Visualizar cada documento em Markdown com interface própria.
  * Visualizar documentos como grafo.
  * Consultar documentos e termos presentes nos documentos
  Obs.: Eu pretendo usar o github para versionar essa base de conhecimento
  Obs.: Essa base de conhecimento poderá ser utilizada por sistemas e agentes de IA para responderem perguntas, consultas e realizar tarefas. 

---

## 3. Pilares & Funcionalidades Chave

- **Gestão de Cofres (Vaults):**
  <!-- Como devem funcionar os cofres (ex: pastas locais no disco, arquivos Markdown puros (.md), sem lock-in). -->
  O MarkAtlas funcionará com cofres (vaults), que são pastas locais no disco, arquivos Markdown puros (.md), sem lock-in.

- **Estrutura de Conteúdo & Metadados:**
  <!-- Frontmatter YAML, tags (#tag), links bidirecionais ([[Nota]]), anexos/imagens. -->
  O MarkAtlas funcionará com estrutura de conteúdo baseada em frontmatter YAML, tags (#tag), links bidirecionais ([[Nota]]), anexos/imagens.

- **Editor & Renderização:**
  <!-- Modos de edição (Markdown puro, live preview, preview lado a lado, syntax highlighting). -->
  O MarkAtlas funcionará com modos de edição (Markdown puro, live preview, preview lado a lado, syntax highlighting).

- **Organização & Visualização (Atlas / Grafo / Árvore):**
  <!-- Como o conhecimento será explorado visualmente (árvore de arquivos, grafo de conexões, mapas mentais, etc.). -->
  O MarkAtlas funcionará com organização e visualização baseada em árvore de arquivos, grafo de conexões, mapas mentais, etc.

- **Busca & Indexação:**
  <!-- Busca por texto completo, filtros por tags e metadados. -->
  O MarkAtlas funcionará com busca por texto completo, filtros por tags e metadados.

---

## 4. Decisões Técnicas & Princípios Inegociáveis

- **Privacidade & Offline-First:**
  <!-- Ex: 100% offline, dados pertencem ao usuário, sem telemetria. -->
  O MarkAtlas será 100% offline, com dados pertencentes ao usuário, sem telemetria.

- **Performance & Consumo de Recursos:**
  <!-- Ex: Aplicação desktop nativa e leve (Python + GTK), inicialização instantânea. -->
  O MarkAtlas será uma aplicação desktop nativa e leve (Python + GTK), com inicialização instantânea.

- **Interoperabilidade:**
  <!-- Ex: Total compatibilidade com outros editores de Markdown (Obsidian, VS Code, Logseq, Typora). -->
  O MarkAtlas funcionará com total compatibilidade com outros editores de Markdown (Obsidian, VS Code, Logseq, Typora).

- **Arquitetura de Código:**
  <!-- MVC + Repository, Spec-Driven Development (OpenSpec), Design System com Dark-First. -->
  O MarkAtlas funcionará com arquitetura MVC + Repository, Spec-Driven Development (OpenSpec), Design System com Dark-First.
  * O sistema deve reutilizar componentes para evitar duplicação de código
  * O sistema deve ser modular para facilitar a manutenção
  * As views devem ser responsaveis pela visualizaçãoe deve ser construida com o máximo de componentes reutilizaveis


---

## 5. Roadmap & Fases do Projeto

### Fase 1: MVP (Produto Mínimo Viável)
- [ ] Criação, visualização, edição e exclusão de notas
- [ ] Organização de notas em diretórios
- [ ] Sistema de tags
- [ ] Sistema de visualização de notas em grafo.
- [ ] Importação e conversão de fontes PDF,HTML, Markdown, EPub. convertendo-os para Markdown, e organizando em diretórios.
- [ ] Cada documento deve ter interface própria de visualização. Esta interface será responsável por exibir o conteúdo do documento e permitir a interação com ele.


### Fase 2: Expansão & Recursos Avançados
- [ ] Sistema de busca
- [ ] Sistema de links bidirecionais
- [ ] Sistema de anexos/imagens

### Fase 3: Visão de Longo Prazo / Futuro
- [ ] Sistema de visualização de notas em mapa
- [ ] Sistema de visualização de notas em árvore
- [ ] Sistema de visualização de notas em grafo
 

