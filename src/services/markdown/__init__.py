"""Sub-pacote de parsing e renderização de Markdown para Pango Markup.

Exporta os módulos principais para uso direto:
- ThemeColors: Paleta de cores por tema
- RichToken / TokenManager: Tokens tipados para renderização rica
- InlineParser: Parser de formatação inline
- BlockParser: Parser de blocos de documento
"""

from src.services.markdown.theme_colors import ThemeColors
from src.services.markdown.rich_token import RichToken, TokenManager
from src.services.markdown.inline_parser import InlineParser
from src.services.markdown.block_parser import BlockParser
from src.services.markdown.emoji_map import EMOJI_MAP, replace_emojis
from src.services.markdown.mermaid_models import MermaidEdge, MermaidGraph, MermaidNode, NodeShape
from src.services.markdown.mermaid_parser import MermaidParser
from src.services.markdown.mermaid_renderer import MermaidSvgGenerator
from src.services.markdown.mermaid_cli_bridge import MermaidCliBridge
from src.services.markdown.syntax_highlighter import SyntaxHighlighter

__all__ = [
    "ThemeColors",
    "RichToken",
    "TokenManager",
    "InlineParser",
    "BlockParser",
    "EMOJI_MAP",
    "replace_emojis",
    "MermaidNode",
    "MermaidEdge",
    "MermaidGraph",
    "NodeShape",
    "MermaidParser",
    "MermaidSvgGenerator",
    "MermaidCliBridge",
    "SyntaxHighlighter",
]
