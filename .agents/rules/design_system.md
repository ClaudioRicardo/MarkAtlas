# MarkAtlas Design System & Estilização GTK

Este documento define os padrões visuais, tokens semânticos, tipografia e boas práticas de estilização CSS para o projeto MarkAtlas (PyGObject / GTK 3+).

---

## 1. Princípios de Design

1. **Dark-First Elegante**: O tema escuro (`dark`) é a experiência primária e padrão da aplicação, oferecendo alto contraste sem cansar a visão.
2. **Semântica e Consistência**: Todos os componentes devem utilizar variáveis/tokens CSS padronizados (`@define-color`), evitando cores hexadecimais hardcoded nos componentes.
3. **Compatibilidade GTK 3 / Windows**: O GTK 3 no Windows possui particularidades de renderização (gradientes padrão de botões e cabeçalhos). Resets como `background-image: none;`, `box-shadow: none;` e tratamento explícito de estados `:backdrop` (quando a janela perde o foco) são obrigatórios em componentes estruturais e botões.
4. **Responsividade e Espaçamento**: Layouts consistentes com grids de 4px / 8px e cantos arredondados de 6px a 8px.

---

## 2. Paletas de Cores & Tokens

### 2.1 Tema Escuro (Padrão)

| Token | Valor Hex | Descrição |
| :--- | :--- | :--- |
| `@bg_darker` | `#12121a` | Fundo mais profundo (Sidebar, HeaderBar, Barra de Status) |
| `@bg_dark` | `#181824` | Fundo principal da janela e tela do editor |
| `@bg_card` | `#202030` | Fundo de cartões, caixas de diálogo, inputs |
| `@bg_hover` | `#2b2b40` | Estado hover de linhas de árvore, itens e botões secundários |
| `@bg_active` | `#383854` | Estado selecionado ou ativo |
| `@fg_primary` | `#f0f0f5` | Texto principal de alto contraste |
| `@fg_secondary` | `#9c9cb3` | Texto secundário, subtítulos, ícones neutros |
| `@fg_muted` | `#6e6e88` | Texto atenuado, placeholders, metadados |
| `@accent_blue` | `#3b82f6` | Cor de destaque primária (botões principais, foco) |
| `@accent_blue_hover`| `#60a5fa` | Hover do destaque primário |
| `@accent_purple` | `#8b5cf6` | Destaque secundário / tags |
| `@accent_green` | `#10b981` | Sucesso / status ativo |
| `@accent_rose` | `#f43f5e` | Alerta / perigo / erro |
| `@accent_amber` | `#f59e0b` | Aviso / tags temporárias |
| `@border_subtle` | `#2c2c3e` | Linhas divisórias e bordas sutis |
| `@border_focus` | `#3b82f6` | Bordas de foco em inputs |

---

### 2.2 Tema Claro

| Token | Valor Hex | Descrição |
| :--- | :--- | :--- |
| `@bg_darker` | `#f1f5f9` | Fundo neutro (Sidebar, HeaderBar, Barra de Status) |
| `@bg_dark` | `#ffffff` | Fundo principal e tela do editor |
| `@bg_card` | `#f8fafc` | Fundo de cartões, caixas de diálogo, inputs |
| `@bg_hover` | `#e2e8f0` | Hover de itens e botões |
| `@bg_active` | `#cbd5e1` | Estado selecionado ou ativo |
| `@fg_primary` | `#0f172a` | Texto principal escuro |
| `@fg_secondary` | `#475569` | Texto secundário |
| `@fg_muted` | `#94a3b8` | Texto atenuado e placeholders |
| `@accent_blue` | `#2563eb` | Cor de destaque primária |
| `@accent_blue_hover`| `#1d4ed8` | Hover do destaque primário |
| `@accent_purple` | `#7c3aed` | Destaque secundário |
| `@accent_green` | `#059669` | Sucesso |
| `@accent_rose` | `#e11d48` | Alerta / erro |
| `@accent_amber` | `#d97706` | Aviso |
| `@border_subtle` | `#e2e8f0` | Linhas divisórias claras |
| `@border_focus` | `#2563eb` | Bordas de foco |

---

## 3. Tipografia

- **Família da Interface (UI)**: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;`
- **Família do Editor / Código**: `"JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, monospace;`
- **Escala Tipográfica**:
  - `Document Title`: 26px, peso 700 (Bold)
  - `HeaderBar Title`: 15px, peso 700
  - `HeaderBar Subtitle`: 13px, peso 400
  - `Vault Title / Seção`: 16px, peso 700
  - `Body / Editor`: 16px, altura de linha 1.6
  - `Tree / Navegação`: 15px
  - `Menu Items / UI Buttons`: 14px
  - `Status Bar / Hints`: 13px, peso 400
  - `Tag Badges`: 12px, peso 600

---

## 4. Regras Obrigatórias para CSS no GTK 3

1. **Reset de Background Image**: No GTK 3, elementos nativos como `button` e `headerbar` possuem gradientes nativos embutidos. Sempre declare:
   ```css
   background-image: none;
   box-shadow: none;
   ```
2. **Tratamento do Estado `:backdrop`**: Quando uma janela GTK perde o foco no Windows, ela entra no estado `:backdrop`. Declare seletores como:
   ```css
   headerbar, headerbar:backdrop {
       background-color: @bg_darker;
       color: @fg_primary;
   }
   ```
3. **Nomes de Classes e Componentes**:
   - Botões principais: `.btn-primary`
   - Botões secundários/neutros: `.btn-secondary`
   - Botões de alternância/ícones: `.btn-icon`
   - Caixas de busca: `.search-input`
   - Títulos de seção: `.section-title`, `.tag-section-title`
   - Árvores de visualização: `.file-tree`
