# Diretrizes de Qualidade, Arquitetura e Boas Práticas — MarkAtlas

Este documento estabelece regras obrigatórias de desenvolvimento para garantir manutenibilidade, isolamento de camadas, robustez e consistência no código do MarkAtlas, prevenindo a reintrodução de antipadrões identificados nas análises de qualidade.

---

## 1. Princípio de Responsabilidade Única (SRP) e Tamanho de Módulos

- **Limite de Responsabilidades por Módulo**: Nenhum arquivo deve concentrar múltiplas responsabilidades (ex.: parsing de blocos, parsing inline, paleta de cores, renderização de tabelas e mapa de emojis no mesmo arquivo).
- **Limite Recomendado de LOC**: Mantenha os arquivos focados e coesos (idealmente abaixo de 250–300 linhas). Se um componente começar a crescer excessivamente, fatie-o em sub-módulos especializados ou crie um sub-pacote com uma fachada (Facade).
- **Fachadas (Facades)**: Quando um subsistema for decomposto em vários submódulos (como o `src/services/markdown/`), o ponto de entrada principal (`MarkdownService`) deve atuar como uma fachada fina, coordenando os submódulos sem acumular lógica interna.

---

## 2. Separação Rigorosa de Camadas (MVC + Repository)

O projeto MarkAtlas segue estritamente o padrão **MVC + Repository**:

```
[ View ]  <--->  [ Controller ]  <--->  [ Service ]  <--->  [ Repository ]
   |                                                              |
[ CSS / UI ]                                                [ FileSystem / SQLite ]
```

### Regras por Camada:

1. **Views (`src/views/`)**:
   - Responsabilidade exclusiva: construção de widgets GTK, layout, exibição de dados e captura de eventos do usuário.
   - **PROIBIDO**: Fazer I/O em disco, leitura direta de arquivos, manipulação direta de repositórios ou regras de negócio complexas.
   - **PROIBIDO**: Chamar métodos de services internos pulando o Controller.

2. **Controllers (`src/controllers/`)**:
   - Responsabilidade: orquestrar o fluxo entre a interface e os serviços de domínio, tratando eventos de UI e gerenciando o estado ativo da sessão.
   - Deve expor métodos delegados claros para a View.

3. **Services (`src/services/`)**:
   - Responsabilidade: regras de negócio puras, casos de uso, transformações de dados e orquestração de persistência.
   - Não devem depender de widgets ou tipos de UI (`Gtk`, `Gdk`).

4. **Repositories (`src/repositories/`)**:
   - Responsabilidade: acesso a dados e persistência física (arquivos locais, metadados frontmatter, SQLite).
   - Devem implementar rigorosamente as interfaces abstratas definidas em `src/repositories/base.py`.

---

## 3. Lei de Demeter e Respeito a Encapsulamento

- **Não encadear acessos profundos**: As Views devem interagir apenas com o Controller imediato.
  - ❌ **Incorreto**: `self.controller.vault_service.get_active_vault()`
  - ✅ **Correto**: `self.controller.get_active_vault()` (método delegado no Controller)
- **Respeito a Métodos Privados**:
  - ❌ **Incorreto**: Chamar `obj._metodo_privado()` de outra camada ou usar `isinstance` para acessar membros internos de uma implementação concreta.
  - ✅ **Correto**: Declarar o método como público no contrato abstrato da interface (`base.py`) e implementá-lo formalmente.
- **Interfaces Públicas no Editor**: Se a `MainWindow` ou outro componente precisa atualizar um widget, a View deve expor um método público formal (ex.: `refresh_preview()`), nunca acessar `_update_preview()`.

---

## 4. Manipulação Segura de Pango Markup e TextBuffer (GTK)

Ao renderizar e manipular texto formatado no `Gtk.TextView` / `Gtk.TextBuffer`:

1. **Inserção Atômica de Markup**:
   - **NUNCA** fatiar uma string de Pango Markup por regex e passar pedaços fragmentados para `insert_markup()`. Pedaços isolados contêm tags XML não balanceadas (como `<b>` sem `</b>`), o que causa erros `Gtk-WARNING: Invalid markup string`.
   - Sempre chame `insert_markup(end_iter, raw_pango, -1)` com a string completa e balanceada de uma só vez.
2. **Enriquecimento Pós-Renderização**:
   - Para adicionar comportamentos interativos (links clicáveis, âncoras de footnotes, substituição de imagens locais por `GdkPixbuf`), faça uma varredura pós-renderização no `TextBuffer` já populado utilizando `get_iter_at_offset` e `apply_tag()`.

---

## 5. Tipagem Estrita e Proibição de Protocolos de String Ad-hoc

- **Dataclasses vs Strings Mágicas**:
  - ❌ **Incorreto**: Criar protocolos de comunicação baseados em delimitadores de string (ex.: `@@@LINKTOKEN@@@url@@@label@@@` parseados com `split("@@@")`). Strings arbitrárias que contenham o delimitador quebram silenciosamente.
  - ✅ **Correto**: Utilizar `@dataclass` tipadas (ex.: `RichToken`, `ThemeColors`) com campos explícitos e métodos de conversão seguros.
- **Tipagem Obrigatória**:
  - Todas as funções, métodos e atributos de classes devem ter anotações de tipo completas (`typing`: `Optional`, `List`, `Dict`, `Tuple`, `Callable`, etc.).

---

## 6. Design System e Centralização de Cores (DRY)

- **Cores Centralizadas**: Não disperse códigos de cores hexadecimais hardcoded dentro de métodos de serviço ou componentes de visualização.
- Utilize a classe centralizada `ThemeColors` (`src/services/markdown/theme_colors.py`) integrada aos tokens definidos em `assets/styles/tokens_dark.css` e `assets/styles/tokens_light.css`.
- Assegure que qualquer nova feature visual suporte tanto o modo **Dark** quanto o modo **Light**.

---

## 7. Higiene de Código e Manutenibilidade

- **Zero Código Morto**:
  - Não deixe imports não utilizados (ex.: `import html` não referenciado).
  - Remova classes, métodos e variáveis que foram substituídos ou não são utilizados.
- **Resiliência a Falhas (Graceful Degradation)**:
  - Componentes gráficos devem checar a disponibilidade do GTK (`GTK_AVAILABLE`) para permitir execução de suítes de teste em ambientes headless.
- **Testabilidade**:
  - Toda nova funcionalidade de negócio ou refatoração deve ser acompanhada de testes unitários em `tests/unit/` ou testes de integração em `tests/integration/`.
