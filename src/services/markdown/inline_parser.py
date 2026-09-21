"""Parser de formatação inline de Markdown para Pango Markup.

Processa elementos dentro de uma linha: bold, italic, code, links,
imagens, footnotes, tags, emojis, highlight, sub/superscript, kbd.
"""

import re
from typing import List

from src.services.markdown.emoji_map import replace_emojis
from src.services.markdown.rich_token import RichToken, TokenManager
from src.services.markdown.theme_colors import ThemeColors


class InlineParser:
    """Processador de marcações inline de Markdown com proteção de tokens."""

    def __init__(self) -> None:
        # Regex para inline markdown
        self._re_tag = re.compile(r"(?<![a-zA-Z0-9_&/])#([a-zA-Z\u00C0-\u017F][a-zA-Z0-9_\-/\u00C0-\u017F]*)")
        self._re_bold_italic = re.compile(r"(\*\*\*|___)(.*?)\1")
        self._re_bold = re.compile(r"(\*\*|__)(.*?)\1")
        self._re_italic = re.compile(r"(\*|_)(.*?)\1")
        self._re_strike = re.compile(r"~~(.*?)~~")
        self._re_highlight = re.compile(r"==(.*?)==\b|==(.*?)==\B")
        self._re_subscript = re.compile(r"~([a-zA-Z0-9_\-\+]+)~")
        self._re_superscript = re.compile(r"\^([a-zA-Z0-9_\-\+]+)\^")
        self._re_code_inline = re.compile(r"`([^`]+)`")
        self._re_image = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
        self._re_link = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        self._re_wikilink = re.compile(r"\[\[([^\]]+)\]\]")
        self._re_footnote_ref = re.compile(r"\[\^([^\]]+)\]")
        self._re_autolink = re.compile(r"<(https?://[^>]+|mailto:[^>]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>")
        self._re_raw_url = re.compile(r"(?<![\"\'>=])\b(https?://[^\s<>]+)")
        self._re_kbd = re.compile(r"<kbd>(.*?)</kbd>", re.IGNORECASE)

    @property
    def tag_regex(self) -> re.Pattern:
        """Retorna o regex de tags para uso externo (extração de tags)."""
        return self._re_tag

    def render(self, text: str, colors: ThemeColors, token_manager: TokenManager) -> str:
        """Processa marcações inline escapando entidades e aplicando todas as tags Pango.

        :param text: Texto bruto de uma linha
        :param colors: Paleta de cores do tema ativo
        :param token_manager: Gerenciador de tokens para elementos ricos
        :return: String Pango Markup formatada
        """
        # 1. Substitui emojis de texto :emoji:
        text = replace_emojis(text)

        # 2. Escapa entidades XML (&, <, >) mantendo aspas e apóstrofos limpos
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # 3. Código inline `codigo`
        escaped = self._re_code_inline.sub(
            lambda m: token_manager.save_raw(
                f"<span font_desc='JetBrains Mono, monospace' background='{colors.code_bg}' foreground='{colors.code_fg}'> {m.group(1)} </span>"
            ),
            escaped,
        )

        # 4. Tags de teclado <kbd>Ctrl</kbd>
        escaped = re.sub(
            r"(?:&lt;kbd&gt;|<kbd>)(.*?)(?:&lt;/kbd&gt;|</kbd>)",
            lambda m: token_manager.save_raw(
                f"<span font_desc='JetBrains Mono, monospace' background='{colors.code_bg}' foreground='{colors.code_fg}'>[ {m.group(1)} ]</span>"
            ),
            escaped,
            flags=re.IGNORECASE,
        )

        # 5. Imagens ![alt](url)
        escaped = self._re_image.sub(
            lambda m: token_manager.save(
                RichToken(kind="image", url=m.group(2), alt=m.group(1))
            ),
            escaped,
        )

        # 6. Links padrão [Texto](url)
        escaped = self._re_link.sub(
            lambda m: token_manager.save(
                RichToken(kind="link", url=m.group(2), label=m.group(1))
            ),
            escaped,
        )

        # 7. Wikilinks [[Nota]]
        escaped = self._re_wikilink.sub(
            lambda m: token_manager.save_raw(
                f"<span foreground='{colors.link_color}' weight='bold' underline='single'>[[{m.group(1)}]]</span>"
            ),
            escaped,
        )

        # 8. Autolinks <https://...> ou <email@...>
        escaped = self._re_autolink.sub(
            lambda m: token_manager.save(
                RichToken(kind="link", url=m.group(1), label=m.group(1))
            ),
            escaped,
        )

        # 9. URLs puras https://...
        escaped = self._re_raw_url.sub(
            lambda m: token_manager.save(
                RichToken(kind="link", url=m.group(1), label=m.group(1))
            ),
            escaped,
        )

        # 10. Referência a Footnote [^1]
        escaped = self._re_footnote_ref.sub(
            lambda m: token_manager.save(
                RichToken(kind="footnote_ref", fn_id=m.group(1))
            ),
            escaped,
        )

        # 11. Tags Markdown #tag ou #tag/subtag
        escaped = self._re_tag.sub(
            lambda m: token_manager.save_raw(
                f"<span foreground='{colors.tag_color}' weight='bold'>#{m.group(1)}</span>"
            ),
            escaped,
        )

        # 12. Destaque / Highlight ==texto==
        escaped = self._re_highlight.sub(
            lambda m: token_manager.save_raw(
                f"<span background='{colors.hl_bg}' foreground='{colors.hl_fg}' weight='bold'> {m.group(1) or m.group(2)} </span>"
            ),
            escaped,
        )

        # 13. Negrito + Itálico ***texto*** ou ___texto___
        escaped = self._re_bold_italic.sub(r"<b><i>\2</i></b>", escaped)

        # 14. Negrito **texto** ou __texto__
        escaped = self._re_bold.sub(r"<b>\2</b>", escaped)

        # 15. Itálico *texto* ou _texto_
        escaped = self._re_italic.sub(r"<i>\2</i>", escaped)

        # 16. Tachado ~~texto~~
        escaped = self._re_strike.sub(r"<s>\1</s>", escaped)

        # 17. Subscrito ~sub~ (ex: H~2~O)
        escaped = self._re_subscript.sub(
            r"<span rise='-4000' size='small'>\1</span>",
            escaped,
        )

        # 18. Sobrescrito ^super^ (ex: X^2^)
        escaped = self._re_superscript.sub(
            r"<span rise='5000' size='small'>\1</span>",
            escaped,
        )

        # 19. Restaura tokens com renderização padrão
        escaped = token_manager.restore_all(escaped, colors.link_color, colors.tag_color)

        return escaped

    def extract_tags(self, text: str) -> List[str]:
        """Extrai todas as tags do formato #tag encontradas no texto.

        :param text: Texto Markdown bruto
        :return: Lista de tags únicas em lowercase
        """
        matches = self._re_tag.findall(text)
        seen: set = set()
        result: List[str] = []
        for tag in matches:
            t = tag.lower()
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result
