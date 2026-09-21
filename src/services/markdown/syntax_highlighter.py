"""Módulo de destaque de sintaxe (Syntax Highlighting) e renderização de caixas de código para Pango Markup.

Oferece suporte a mais de 20 linguagens de programação populares com paletas de cores
otimizadas para os temas Dark e Light, utilizando Pygments (quando disponível) e um
motor regex nativo resiliente como fallback offline de alto desempenho.
"""

from __future__ import annotations

import html
import re
import textwrap
import unicodedata
from typing import Dict, List, Optional, Tuple

from src.services.markdown.theme_colors import ThemeColors

try:
    import pygments
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class SyntaxHighlighter:
    """Motor de realce de sintaxe e estilização de caixas de código para Pango Markup."""

    # Mapeamento de identificadores de linguagem para (Nome de Exibição, Ícone)
    _LANG_METADATA: Dict[str, Tuple[str, str]] = {
        "python": ("Python", "🐍"),
        "py": ("Python", "🐍"),
        "javascript": ("JavaScript", "🟨"),
        "js": ("JavaScript", "🟨"),
        "typescript": ("TypeScript", "🔷"),
        "ts": ("TypeScript", "🔷"),
        "jsx": ("React JSX", "⚛️"),
        "tsx": ("React TSX", "⚛️"),
        "html": ("HTML", "🌐"),
        "htm": ("HTML", "🌐"),
        "xml": ("XML", "📰"),
        "svg": ("SVG XML", "📐"),
        "css": ("CSS", "🎨"),
        "scss": ("SCSS", "🎨"),
        "sass": ("SASS", "🎨"),
        "json": ("JSON", "📄"),
        "sql": ("SQL", "🗄️"),
        "pgsql": ("PostgreSQL", "🐘"),
        "mysql": ("MySQL", "🐬"),
        "sqlite": ("SQLite", "🗃️"),
        "bash": ("Bash", "🐚"),
        "sh": ("Shell", "🐚"),
        "zsh": ("Zsh", "🐚"),
        "shell": ("Shell", "🐚"),
        "powershell": ("PowerShell", "💻"),
        "ps1": ("PowerShell", "💻"),
        "c": ("C", "⚙️"),
        "cpp": ("C++", "⚙️"),
        "c++": ("C++", "⚙️"),
        "h": ("C Header", "📑"),
        "hpp": ("C++ Header", "📑"),
        "csharp": ("C#", "💠"),
        "cs": ("C#", "💠"),
        "rust": ("Rust", "🦀"),
        "rs": ("Rust", "🦀"),
        "go": ("Go", "🐹"),
        "golang": ("Go", "🐹"),
        "java": ("Java", "☕"),
        "kotlin": ("Kotlin", "🟣"),
        "kt": ("Kotlin", "🟣"),
        "yaml": ("YAML", "📋"),
        "yml": ("YAML", "📋"),
        "toml": ("TOML", "⚙️"),
        "ini": ("Config INI", "⚙️"),
        "env": ("Environment", "🔒"),
        "markdown": ("Markdown", "📝"),
        "md": ("Markdown", "📝"),
        "php": ("PHP", "🐘"),
        "ruby": ("Ruby", "💎"),
        "rb": ("Ruby", "💎"),
        "swift": ("Swift", "🧡"),
        "dockerfile": ("Dockerfile", "🐳"),
        "docker": ("Docker", "🐳"),
        "diff": ("Diff Patch", "📊"),
    }

    # Paletas de cores para realce de sintaxe
    _DARK_PALETTE = {
        "keyword": "#38bdf8",     # Azul claro vibrante
        "type": "#c084fc",        # Roxo / Lilás
        "function": "#facc15",    # Amarelo dourado
        "string": "#4ade80",      # Verde claro
        "number": "#fb923c",      # Laranja
        "comment": "#94a3b8",     # Cinza suave itálico
        "decorator": "#f472b6",   # Rosa
        "operator": "#e2e8f0",    # Branco suave
        "builtin": "#38bdf8",     # Ciano
    }

    _LIGHT_PALETTE = {
        "keyword": "#0284c7",     # Azul forte
        "type": "#7c3aed",        # Roxo profundo
        "function": "#b45309",    # Âmbar escuro
        "string": "#15803d",      # Verde escuro
        "number": "#c2410c",      # Laranja forte
        "comment": "#64748b",     # Cinza médio itálico
        "decorator": "#be185d",   # Magenta
        "operator": "#1e293b",    # Escuro
        "builtin": "#0369a1",     # Azul petróleo
    }

    def render_code_block(
        self,
        code: str,
        language: str,
        colors: ThemeColors,
        max_code_width: int = 76,
    ) -> str:
        """Renderiza um bloco de código cercado como uma caixa fechada com borda perimetral,

        cabeçalho de linguagem, numeração de linhas e quebra de linha inteligente.

        :param code: Código bruto do bloco
        :param language: Identificador da linguagem (ex: 'python', 'sql', 'js')
        :param colors: Cores do tema ativo (Dark / Light)
        :param max_code_width: Largura máxima do conteúdo em colunas antes de quebrar linha
        :return: String formatada em Pango Markup
        """
        raw_lines = code.splitlines()
        if not raw_lines:
            raw_lines = [""]

        clean_lang = (language or "").strip().lower()
        display_name, icon = self._get_lang_info(clean_lang)

        # Determina a paleta baseada no tema
        is_dark = colors.code_bg.lower() not in ("#ffffff", "#f8f9fa", "#f1f5f9", "#e2e8f0", "#eff6ff")
        palette = self._DARK_PALETTE if is_dark else self._LIGHT_PALETTE

        # Destaca o código linha por linha
        highlighted_lines = self._highlight_to_lines(code, clean_lang, palette)

        if len(highlighted_lines) < len(raw_lines):
            highlighted_lines.extend([""] * (len(raw_lines) - len(highlighted_lines)))

        # 1. Calcula a largura ideal da coluna de código baseada na maior instrução
        max_visible_len = max((self._str_display_width(line) for line in highlighted_lines), default=20)
        title_text = f" {icon} {display_name.upper()} " if clean_lang else " 📄 CÓDIGO "
        title_w = self._str_display_width(title_text)

        # Largura da área de código (respeitando o limite max_code_width)
        code_col_width = max(40, min(max(max_visible_len, title_w + 4), max_code_width))

        # Numeração de linhas
        num_lines = len(highlighted_lines)
        num_width = max(2, len(str(num_lines)))

        border_col = colors.table_border
        num_col = colors.quote_color
        header_fg = colors.tag_color

        # 2. Borda Superior: ┌── 🐍 PYTHON ──────────────────────────────────────────────┐
        rem_top = max(2, code_col_width + num_width + 4 - title_w - 3)
        top_bar = (
            f"<span foreground='{border_col}'>┌──</span>"
            f"<span foreground='{header_fg}' weight='bold'>{html.escape(title_text)}</span>"
            f"<span foreground='{border_col}'>{'─' * rem_top}┐</span>"
        )

        box_rows: List[str] = [top_bar]

        # 3. Linhas de Código Numeradas com Borda Lateral Fechada: │  1 │ def hello():  │
        for idx, h_line in enumerate(highlighted_lines, 1):
            num_str = str(idx).rjust(num_width)
            vis_w = self._str_display_width(h_line)

            # Se a linha couber na largura da caixa:
            if vis_w <= code_col_width:
                pad = " " * (code_col_width - vis_w)
                row = (
                    f"<span foreground='{border_col}'>│</span> "
                    f"<span foreground='{num_col}'>{num_str}</span> "
                    f"<span foreground='{border_col}'>│</span> "
                    f"{h_line}{pad} "
                    f"<span foreground='{border_col}'>│</span>"
                )
                box_rows.append(row)
            else:
                # Quebra de linha inteligente para instruções muito longas
                raw_text = html.unescape(re.sub(r"<[^>]+>", "", h_line))
                wrapped_pieces = textwrap.wrap(raw_text, width=code_col_width) or [raw_text]
                for sub_idx, piece in enumerate(wrapped_pieces):
                    esc_piece = html.escape(piece)
                    # Aplica cor baseada no tipo se for linha única
                    piece_w = self._str_display_width(esc_piece)
                    pad = " " * max(0, code_col_width - piece_w)
                    gutter_num = num_str if sub_idx == 0 else " " * num_width

                    row = (
                        f"<span foreground='{border_col}'>│</span> "
                        f"<span foreground='{num_col}'>{gutter_num}</span> "
                        f"<span foreground='{border_col}'>│</span> "
                        f"{esc_piece}{pad} "
                        f"<span foreground='{border_col}'>│</span>"
                    )
                    box_rows.append(row)

        # 4. Borda Inferior Fechada: └──────────────────────────────────────────────────┘
        bottom_len = code_col_width + num_width + 4
        bottom_bar = f"<span foreground='{border_col}'>└{'─' * bottom_len}┘</span>"
        box_rows.append(bottom_bar)

        # Junta todas as linhas dentro do container com background e fonte monoespaçada
        content_block = "\n".join(box_rows)
        return (
            f"\n<span font_desc='JetBrains Mono, Consolas, monospace' "
            f"background='{colors.code_bg}' foreground='{colors.code_fg}'>\n{content_block}\n</span>\n"
        )

    def _str_display_width(self, pango_line: str) -> int:
        """Calcula o tamanho visual exato em colunas de uma string formatada em Pango.

        Trata remoção de tags XML, desfaz entidades HTML (&lt;, &gt;, &amp;) e
        calcula a largura de emojis e caracteres unicode corretamente.
        """
        clean = html.unescape(re.sub(r"<[^>]+>", "", pango_line))
        width = 0
        for ch in clean:
            if ch in ("\ufe0f", "\u200d"):
                continue
            eaw = unicodedata.east_asian_width(ch)
            if eaw in ("F", "W") or ord(ch) > 0x1F000:
                width += 2
            else:
                width += 1
        return width

    def _get_lang_info(self, lang: str) -> Tuple[str, str]:
        """Retorna o nome amigável e ícone da linguagem."""
        if not lang:
            return ("Código", "📄")
        return self._LANG_METADATA.get(lang, (lang.capitalize(), "💻"))

    def _highlight_to_lines(self, code: str, lang: str, palette: Dict[str, str]) -> List[str]:
        """Aplica o realce de sintaxe retornando uma lista de linhas com tags Pango Markup seguras."""
        if not code.strip():
            return [html.escape(l) for l in code.splitlines()] or [""]

        # 1. Tenta usar Pygments se disponível
        if PYGMENTS_AVAILABLE:
            try:
                lexer = None
                if lang:
                    try:
                        lexer = get_lexer_by_name(lang)
                    except Exception:
                        pass
                if lexer:
                    return self._highlight_pygments_lines(code, lexer, palette)
            except Exception:
                pass

        # 2. Fallback para motor regex nativo em Python puro
        return self._highlight_regex_lines(code, lang, palette)

    def _highlight_pygments_lines(self, code: str, lexer: object, palette: Dict[str, str]) -> List[str]:
        """Converte tokens do Pygments em linhas de tags Pango Markup."""
        tokens = lex(code, lexer)
        lines: List[str] = []
        current_line_parts: List[str] = []

        for ttype, value in tokens:
            escaped_val = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if not escaped_val:
                continue

            color = None
            is_bold = False
            is_italic = False

            if ttype in Token.Keyword or ttype in Token.Keyword.Constant or ttype in Token.Keyword.Declaration:
                color = palette["keyword"]
                is_bold = True
            elif ttype in Token.Keyword.Type or ttype in Token.Name.Class or ttype in Token.Name.Exception:
                color = palette["type"]
                is_bold = True
            elif ttype in Token.Name.Function or ttype in Token.Name.Builtin.Pseudo:
                color = palette["function"]
            elif ttype in Token.Name.Builtin:
                color = palette["builtin"]
            elif ttype in Token.String or ttype in Token.String.Doc or ttype in Token.String.Char:
                color = palette["string"]
            elif ttype in Token.Number or ttype in Token.Number.Integer or ttype in Token.Number.Float:
                color = palette["number"]
            elif ttype in Token.Comment or ttype in Token.Comment.Single or ttype in Token.Comment.Multiline:
                color = palette["comment"]
                is_italic = True
            elif ttype in Token.Name.Decorator or ttype in Token.Name.Tag:
                color = palette["decorator"]

            def format_piece(piece: str) -> str:
                if not color or not piece:
                    return piece
                attrs = f"foreground='{color}'"
                if is_bold:
                    attrs += " weight='bold'"
                if is_italic:
                    attrs += " style='italic'"
                return f"<span {attrs}>{piece}</span>"

            if "\n" in escaped_val:
                sub_parts = escaped_val.split("\n")
                for i, sub in enumerate(sub_parts):
                    if sub:
                        current_line_parts.append(format_piece(sub))
                    if i < len(sub_parts) - 1:
                        lines.append("".join(current_line_parts))
                        current_line_parts = []
            else:
                current_line_parts.append(format_piece(escaped_val))

        if current_line_parts or not lines:
            lines.append("".join(current_line_parts))

        return lines

    def _highlight_regex_lines(self, code: str, lang: str, palette: Dict[str, str]) -> List[str]:
        """Motor de realce regex nativo em Python puro quando Pygments não está disponível."""
        # Palavras-chave por família de linguagem
        keywords_common = {
            "python": r"\b(def|class|if|elif|else|for|while|try|except|finally|with|as|return|yield|import|from|in|is|not|and|or|lambda|global|nonlocal|pass|break|continue|raise|async|await|assert)\b",
            "js": r"\b(function|class|const|let|var|if|else|for|while|do|switch|case|break|continue|return|try|catch|finally|throw|new|typeof|instanceof|import|export|from|default|async|await|yield|this|super|extends|implements|interface|type)\b",
            "sql": r"\b(SELECT|FROM|WHERE|INSERT|INTO|UPDATE|DELETE|JOIN|LEFT|RIGHT|INNER|OUTER|GROUP|BY|ORDER|HAVING|LIMIT|OFFSET|CREATE|TABLE|DROP|ALTER|ADD|INDEX|VIEW|PRIMARY|KEY|FOREIGN|REFERENCES|NOT|NULL|UNIQUE|DEFAULT|CHECK|AND|OR|AS|IN|EXISTS|BETWEEN|LIKE|IS|CASE|WHEN|THEN|END|UNION|ALL|DISTINCT|COUNT|SUM|AVG|MIN|MAX)\b",
            "html": r"</?([a-zA-Z0-9_\-]+)",
            "sh": r"\b(if|then|else|elif|fi|case|esac|for|while|until|do|done|in|function|select|return|exit|export|local|echo|read|source|alias)\b",
        }

        escaped_lines: List[str] = []

        for line in code.split("\n"):
            # Linhas de comentário completas
            if lang in ("python", "py", "sh", "bash", "yaml", "yml") and line.strip().startswith("#"):
                esc_line = html.escape(line)
                escaped_lines.append(f"<span foreground='{palette['comment']}' style='italic'>{esc_line}</span>")
                continue
            elif lang in ("js", "javascript", "ts", "typescript", "c", "cpp", "java", "rust", "go") and line.strip().startswith("//"):
                esc_line = html.escape(line)
                escaped_lines.append(f"<span foreground='{palette['comment']}' style='italic'>{esc_line}</span>")
                continue
            elif lang == "sql" and line.strip().startswith("--"):
                esc_line = html.escape(line)
                escaped_lines.append(f"<span foreground='{palette['comment']}' style='italic'>{esc_line}</span>")
                continue

            # Escapa a linha para XML Pango
            esc = html.escape(line)

            # Destaca Strings ("..." e '...')
            esc = re.sub(
                r'(&quot;.*?&quot;|&#x27;.*?&#x27;|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')',
                f"<span foreground='{palette['string']}'>\\1</span>",
                esc,
            )

            # Destaca Números isolados
            esc = re.sub(
                r'\b([0-9]+(?:\.[0-9]+)?)\b',
                f"<span foreground='{palette['number']}'>\\1</span>",
                esc,
            )

            # Destaca Booleanos e Nulos
            esc = re.sub(
                r'\b(True|False|None|true|false|null|nil|undefined)\b',
                f"<span foreground='{palette['number']}' weight='bold'>\\1</span>",
                esc,
            )

            # Destaca Decorators em Python (@dataclass, @property)
            if lang in ("python", "py"):
                esc = re.sub(
                    r'(@[a-zA-Z0-9_]+)',
                    f"<span foreground='{palette['decorator']}'>\\1</span>",
                    esc,
                )

            # Destaca Keywords conforme linguagem
            kw_pattern = None
            if lang in ("python", "py"):
                kw_pattern = keywords_common["python"]
            elif lang in ("javascript", "js", "typescript", "ts", "jsx", "tsx"):
                kw_pattern = keywords_common["js"]
            elif lang in ("sql", "pgsql", "mysql", "sqlite"):
                kw_pattern = keywords_common["sql"]
            elif lang in ("bash", "sh", "zsh", "shell", "powershell", "ps1"):
                kw_pattern = keywords_common["sh"]
            else:
                kw_pattern = r"\b(def|function|class|if|else|return|for|while|import|export|const|var|let|public|private|protected|static|void|int|str|bool)\b"

            if kw_pattern:
                esc = re.sub(
                    kw_pattern,
                    f"<span foreground='{palette['keyword']}' weight='bold'>\\1</span>",
                    esc,
                    flags=re.IGNORECASE if lang == "sql" else 0,
                )

            # Destaca chamadas de função (ex: func_name(...) )
            esc = re.sub(
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*\()',
                f"<span foreground='{palette['function']}'>\\1</span>",
                esc,
            )

            escaped_lines.append(esc)

        return escaped_lines
