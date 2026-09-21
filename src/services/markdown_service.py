"""Serviço de parsing e renderização de Markdown para Pango Markup / GTK.

Fachada (Facade) que delega para sub-módulos especializados:
- BlockParser: headings, code blocks, tabelas, listas, etc.
- InlineParser: bold, italic, links, imagens, tags, emojis, etc.
- ThemeColors: paleta de cores centralizada por tema
- TokenManager / RichToken: tokens tipados para renderização rica

Suporta especificações completas de Basic Syntax e Extended Syntax do Markdown Guide:
- https://www.markdownguide.org/basic-syntax/
- https://www.markdownguide.org/extended-syntax/
"""

import logging
from typing import List

from src.services.markdown.block_parser import BlockParser
from src.services.markdown.inline_parser import InlineParser
from src.services.markdown.theme_colors import ThemeColors

logger = logging.getLogger(__name__)


class MarkdownService:
    """Conversor e renderizador nativo de Markdown para Pango Markup.

    Mantém a API pública inalterada para compatibilidade com código existente.
    Internamente delega para InlineParser (formatação de linha) e
    BlockParser (estrutura de blocos).
    """

    def __init__(self) -> None:
        self._inline_parser = InlineParser()
        self._block_parser = BlockParser(self._inline_parser)

    def render_to_pango(self, markdown_text: str, is_dark: bool = True) -> str:
        """Converte uma string Markdown em Pango Markup formatado.

        :param markdown_text: Texto original em Markdown
        :param is_dark: Flag indicando se o tema ativo é escuro
        :return: String compatível com Pango Markup do GTK
        """
        if not markdown_text:
            return ""

        # Remove frontmatter YAML se houver no início
        text = self._strip_frontmatter(markdown_text)

        # Obtém a paleta de cores para o tema ativo
        colors = ThemeColors.for_theme(is_dark)

        # Delega para o BlockParser que coordena blocos e inline
        return self._block_parser.render(text, colors)

    def extract_tags(self, text: str) -> List[str]:
        """Extrai todas as tags do formato #tag encontradas no texto.

        :param text: Texto Markdown bruto
        :return: Lista de tags únicas em lowercase
        """
        clean_text = self._strip_frontmatter(text)
        return self._inline_parser.extract_tags(clean_text)

    def _strip_frontmatter(self, text: str) -> str:
        """Remove o bloco Frontmatter YAML inicial se existir."""
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                return parts[2].lstrip("\r\n")
        return text
