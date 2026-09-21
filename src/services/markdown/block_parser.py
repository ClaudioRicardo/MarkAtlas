"""Parser de blocos de Markdown para Pango Markup.

Processa elementos de bloco: headings, code blocks, blockquotes, listas,
tabelas, footnotes, separadores e parágrafos.
"""

import hashlib
import logging
import re
import tempfile
import textwrap
from pathlib import Path
from typing import List

from src.services.markdown.inline_parser import InlineParser
from src.services.markdown.mermaid_cli_bridge import MermaidCliBridge
from src.services.markdown.mermaid_parser import MermaidParser
from src.services.markdown.mermaid_renderer import MermaidSvgGenerator
from src.services.markdown.rich_token import TokenManager
from src.services.markdown.syntax_highlighter import SyntaxHighlighter
from src.services.markdown.theme_colors import ThemeColors

logger = logging.getLogger(__name__)


class BlockParser:
    """Processador de elementos de bloco de Markdown."""

    def __init__(self, inline_parser: InlineParser) -> None:
        self._inline = inline_parser
        self._mermaid_parser = MermaidParser()
        self._mermaid_svg_gen = MermaidSvgGenerator()
        self._mermaid_cli_bridge = MermaidCliBridge()
        self._syntax_highlighter = SyntaxHighlighter()

    def render(self, text: str, colors: ThemeColors) -> str:
        """Converte texto Markdown em Pango Markup processando blocos e inline.

        :param text: Texto Markdown sem frontmatter
        :param colors: Paleta de cores do tema ativo
        :return: String Pango Markup formatada
        """
        lines = text.split("\n")
        output_lines: List[str] = []
        in_code_block = False
        code_block_lines: List[str] = []
        code_block_lang = ""

        idx = 0
        total_lines = len(lines)

        while idx < total_lines:
            line = lines[idx]
            stripped = line.strip()

            # 1. Blocos de Código Cercados (```lang ... ```)
            if stripped.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    code_content = "\n".join(code_block_lines)
                    if code_block_lang.lower() == "mermaid":
                        output_lines.append(self._render_mermaid_block(code_content, colors))
                    else:
                        output_lines.append(
                            self._syntax_highlighter.render_code_block(code_content, code_block_lang, colors)
                        )
                    code_block_lines = []
                    code_block_lang = ""
                else:
                    in_code_block = True
                    code_block_lang = stripped[3:].strip()
                    code_block_lines = []
                idx += 1
                continue

            if in_code_block:
                code_block_lines.append(line)
                idx += 1
                continue

            # 2. Linhas Vazias
            if not stripped:
                output_lines.append("")
                idx += 1
                continue

            # 3. Separador Horizontal (--- ou *** ou ___)
            if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
                output_lines.append(f"<span foreground='{colors.sep_color}'>────────────────────────────────────────────</span>")
                idx += 1
                continue

            # 4. Setext Headings (Linha de texto seguida por === ou ---)
            if idx + 1 < total_lines:
                next_line = lines[idx + 1].strip()
                if re.match(r"^={2,}$", next_line):
                    token_mgr = TokenManager()
                    escaped_title = self._inline.render(line, colors, token_mgr)
                    output_lines.append(f"\n<span font_weight='bold' size='xx-large' foreground='{colors.h_color}'>{escaped_title}</span>")
                    idx += 2
                    continue
                elif re.match(r"^-{2,}$", next_line) and not stripped.startswith(("-", "*", ">", "|", "+")):
                    token_mgr = TokenManager()
                    escaped_title = self._inline.render(line, colors, token_mgr)
                    output_lines.append(f"\n<span font_weight='bold' size='x-large' foreground='{colors.h_color}'>{escaped_title}</span>")
                    idx += 2
                    continue

            # 5. ATX Headings (# H1 a ###### H6) com suporte a Heading IDs {#custom-id}
            if line.startswith("#"):
                h_match = re.match(r"^(#{1,6})\s+(.*?)(?:\s+\{#.*?\})?$", line)
                if h_match:
                    hashes, title_text = h_match.groups()
                    level = len(hashes)
                    token_mgr = TokenManager()
                    escaped_title = self._inline.render(title_text, colors, token_mgr)

                    sizes = {
                        1: "xx-large",
                        2: "x-large",
                        3: "large",
                        4: "medium",
                        5: "small",
                        6: "x-small",
                    }
                    size = sizes.get(level, "medium")
                    output_lines.append(
                        f"\n<span font_weight='bold' size='{size}' foreground='{colors.h_color}'>{escaped_title}</span>"
                    )
                    idx += 1
                    continue

            # 6. Tabelas Markdown (| Col1 | Col2 | ...)
            if stripped.startswith("|") and stripped.endswith("|"):
                table_lines = []
                while idx < total_lines and lines[idx].strip().startswith("|") and lines[idx].strip().endswith("|"):
                    table_lines.append(lines[idx].strip())
                    idx += 1

                rendered_table = self._render_table(table_lines, colors)
                output_lines.append(rendered_table)
                continue

            # 7. Citações (Blockquotes > e Aninhadas >>)
            if stripped.startswith(">"):
                quote_depth = 0
                temp = stripped
                while temp.startswith(">"):
                    quote_depth += 1
                    temp = temp[1:].strip()

                token_mgr = TokenManager()
                escaped_quote = self._inline.render(temp, colors, token_mgr)
                bars = "┃ " * quote_depth
                output_lines.append(
                    f"<span foreground='{colors.bar_color}' weight='bold'>{bars}</span><span style='italic' foreground='{colors.quote_color}'>{escaped_quote}</span>"
                )
                idx += 1
                continue

            # 8. Checklists / Task Lists (- [ ] e - [x] ou * [ ] / + [x])
            chk_match = re.match(r"^(\s*)[-+*]\s+\[([ xX])\]\s+(.*)$", line)
            if chk_match:
                indent, state, chk_text = chk_match.groups()
                token_mgr = TokenManager()
                escaped_chk = self._inline.render(chk_text, colors, token_mgr)
                if state.lower() == "x":
                    output_lines.append(f"{indent}<span foreground='{colors.tag_color}'>☑ </span><s>{escaped_chk}</s>")
                else:
                    output_lines.append(f"{indent}<span foreground='{colors.quote_color}'>☐ </span>{escaped_chk}")
                idx += 1
                continue

            # 9. Listas Não-Ordenadas (-, *, +)
            list_match = re.match(r"^(\s*)[-+*]\s+(.*)$", line)
            if list_match:
                indent, item_text = list_match.groups()
                token_mgr = TokenManager()
                escaped_item = self._inline.render(item_text, colors, token_mgr)
                output_lines.append(f"{indent}<span foreground='{colors.bullet_color}'> • </span>{escaped_item}")
                idx += 1
                continue

            # 10. Listas Ordenadas (1. 2. etc)
            num_match = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
            if num_match:
                indent, num, item_text = num_match.groups()
                token_mgr = TokenManager()
                escaped_item = self._inline.render(item_text, colors, token_mgr)
                output_lines.append(f"{indent}<span foreground='{colors.num_color}' weight='bold'>{num}.</span> {escaped_item}")
                idx += 1
                continue

            # 11. Notas de Rodapé de Definição ([^1]: Detalhe)
            fn_def_match = re.match(r"^\[\^([^\]]+)\]:\s+(.*)$", stripped)
            if fn_def_match:
                fn_id, fn_content = fn_def_match.groups()
                token_mgr = TokenManager()
                escaped_fn = self._inline.render(fn_content, colors, token_mgr)
                output_lines.append(
                    f"\n<span size='small' foreground='{colors.tag_color}' weight='bold'>[^{fn_id}]:</span> <span size='small' style='italic'>{escaped_fn}</span>"
                )
                idx += 1
                continue

            # 12. Listas de Definição (Termo seguido por : Definição)
            if stripped.startswith(":") and len(stripped) > 1:
                def_text = stripped[1:].strip()
                token_mgr = TokenManager()
                escaped_def = self._inline.render(def_text, colors, token_mgr)
                output_lines.append(f"    <span foreground='{colors.quote_color}'>↳ </span>{escaped_def}")
                idx += 1
                continue

            # 13. Parágrafo Padrão
            token_mgr = TokenManager()
            escaped_paragraph = self._inline.render(line, colors, token_mgr)
            output_lines.append(escaped_paragraph)
            idx += 1

        # Bloco de código residual não finalizado
        if in_code_block and code_block_lines:
            code_content = "\n".join(code_block_lines)
            if code_block_lang.lower() == "mermaid":
                output_lines.append(self._render_mermaid_block(code_content, colors))
            else:
                output_lines.append(
                    self._syntax_highlighter.render_code_block(code_content, code_block_lang, colors)
                )

        return "\n".join(output_lines)

    def _render_mermaid_block(self, code: str, colors: ThemeColors) -> str:
        """Processa um bloco de código Mermaid gerando o diagrama SVG correspondente ou fallback."""
        # 1. Tenta o motor nativo em Python (instantâneo e offline)
        graph = self._mermaid_parser.parse(code)
        if graph:
            try:
                svg_content = self._mermaid_svg_gen.generate_svg(graph, colors)
                if svg_content:
                    diag_hash = hashlib.md5((code + colors.code_bg + colors.tag_color).encode("utf-8")).hexdigest()[:12]
                    cache_dir = Path(tempfile.gettempdir()) / "markatlas_diagrams"
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    svg_path = cache_dir / f"mermaid_{diag_hash}.svg"
                    svg_path.write_text(svg_content, encoding="utf-8")

                    banner = f"<span size='small' foreground='{colors.tag_color}'>[ MERMAID DIAGRAM ]</span>"
                    return f"\n{banner}\n🖼️ [Mermaid: {svg_path.as_posix()}]\n"
            except Exception as e:
                logger.warning(f"Falha no motor nativo Mermaid: {e}")

        # 2. Tenta a ponte Mermaid CLI (para os 30 tipos oficiais incluindo C4, Sankey, Packet, Architecture, etc.)
        if self._mermaid_cli_bridge.is_available:
            try:
                cli_svg_path = self._mermaid_cli_bridge.render_to_svg_file(code, colors)
                if cli_svg_path:
                    banner = f"<span size='small' foreground='{colors.tag_color}'>[ MERMAID DIAGRAM ]</span>"
                    return f"\n{banner}\n🖼️ [Mermaid: {cli_svg_path.as_posix()}]\n"
            except Exception as e:
                logger.warning(f"Falha na ponte Mermaid CLI: {e}")

        # 3. Fallback gracioso para bloco de código Pango formatado
        escaped_code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        banner = f"<span size='small' foreground='{colors.quote_color}'>[ MERMAID ]</span>\n"
        return f"\n{banner}<span font_desc='JetBrains Mono, Consolas, monospace' background='{colors.code_bg}' foreground='{colors.code_fg}'>  {escaped_code}  </span>\n"

    def _render_table(
        self,
        table_lines: List[str],
        colors: ThemeColors,
        max_table_width: int = 80,
    ) -> str:
        """Renderiza tabelas Markdown formatadas com quebra de linha interna automática.

        :param table_lines: Linhas brutas da tabela (incluindo separadores)
        :param colors: Paleta de cores do tema ativo
        :param max_table_width: Largura máxima em caracteres
        :return: String Pango Markup da tabela formatada
        """
        if len(table_lines) < 2:
            return "\n".join(table_lines)

        rows = []
        for line in table_lines:
            raw_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # Pula linha separadora de traços (ex: | --- | --- |)
            if all(re.match(r"^:?-+:?$", cell) for cell in raw_cells if cell):
                continue
            rows.append(raw_cells)

        if not rows:
            return "\n".join(table_lines)

        header = rows[0]
        data_rows = rows[1:] if len(rows) > 1 else []
        col_count = len(header)

        # 1. Calcula a largura ideal baseada no maior conteúdo de cada coluna
        col_widths = [max(len(header[i]), 4) if i < len(header) else 4 for i in range(col_count)]
        for row in data_rows:
            for i in range(col_count):
                cell = row[i] if i < len(row) else ""
                col_widths[i] = max(col_widths[i], len(cell))

        # 2. Ajusta larguras caso a tabela ultrapasse o limite horizontal
        total_w = sum(col_widths) + (col_count - 1) * 3 + 4
        if total_w > max_table_width:
            target_per_col = max(14, (max_table_width - (col_count * 3 + 4)) // col_count)
            col_widths = [max(target_per_col, min(w, target_per_col * 2)) for w in col_widths]

        def format_row_lines(cells: List[str], is_header: bool = False) -> str:
            wrapped_cells: List[List[str]] = []
            max_lines = 1
            for i in range(col_count):
                cell_raw = cells[i] if i < len(cells) else ""
                w = max(col_widths[i], 6)
                cell_lines = textwrap.wrap(cell_raw, width=w) or [""]
                wrapped_cells.append(cell_lines)
                max_lines = max(max_lines, len(cell_lines))

            rendered_lines: List[str] = []
            for line_idx in range(max_lines):
                line_parts: List[str] = []
                for i in range(col_count):
                    w = col_widths[i]
                    cell_line_list = wrapped_cells[i]
                    text_piece = cell_line_list[line_idx] if line_idx < len(cell_line_list) else ""
                    token_mgr = TokenManager()
                    rendered_piece = self._inline.render(text_piece, colors, token_mgr)
                    if is_header:
                        rendered_piece = f"<b>{rendered_piece}</b>"

                    padding_len = max(0, w - len(text_piece))
                    line_parts.append(rendered_piece + (" " * padding_len))

                row_str = " │ ".join(line_parts)
                if is_header:
                    rendered_lines.append(f"<span font_desc='JetBrains Mono, monospace' background='{colors.table_header_bg}'>│ {row_str} │</span>")
                else:
                    rendered_lines.append(f"<span font_desc='JetBrains Mono, monospace'>│ {row_str} │</span>")

            return "\n".join(rendered_lines)

        top_border = f"<span foreground='{colors.table_border}' font_desc='JetBrains Mono, monospace'>┌─" + "─┬─".join(["─" * w for w in col_widths]) + "─┐</span>"
        mid_border = f"<span foreground='{colors.table_border}' font_desc='JetBrains Mono, monospace'>├─" + "─┼─".join(["─" * w for w in col_widths]) + "─┤</span>"
        bot_border = f"<span foreground='{colors.table_border}' font_desc='JetBrains Mono, monospace'>└─" + "─┴─".join(["─" * w for w in col_widths]) + "─┘</span>"

        result_lines = [f"\n{top_border}", format_row_lines(header, is_header=True), mid_border]
        for r in data_rows:
            result_lines.append(format_row_lines(r))
        result_lines.append(bot_border + "\n")

        return "\n".join(result_lines)
