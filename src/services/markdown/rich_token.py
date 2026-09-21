"""Tokens tipados para renderização rica de Markdown (links, imagens, footnotes).

Substitui o protocolo ad-hoc de strings @@@TOKEN@@@ por dataclasses type-safe.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RichToken:
    """Representa um elemento rico que requer tratamento especial na renderização.

    Em vez de codificar informações como strings @@@LINKTOKEN@@@url@@@label@@@,
    cada token carrega seus dados de forma tipada e segura.
    """

    kind: str  # "link", "image", "footnote_ref"
    url: str = ""
    label: str = ""
    alt: str = ""
    fn_id: str = ""

    def to_pango(self, link_color: str, tag_color: str) -> str:
        """Renderiza o token como Pango Markup inline (fallback para texto puro).

        :param link_color: Cor do link no tema ativo
        :param tag_color: Cor de tags/footnotes no tema ativo
        :return: String Pango Markup para exibição textual
        """
        if self.kind == "link":
            return f"<span foreground='{link_color}' underline='single'>{self.label}</span>"
        elif self.kind == "image":
            return f"🖼️ <span foreground='{link_color}' style='italic'>[Imagem: {self.alt}]</span>"
        elif self.kind == "footnote_ref":
            return f"<span rise='4000' size='small' foreground='{tag_color}' weight='bold'>[{self.fn_id}]</span>"
        return self.label or self.url


# Prefixo de placeholder para identificar tokens no texto renderizado
_TOKEN_PREFIX = "@@@MARKATLASTOKEN"
_TOKEN_SUFFIX = "@@@"


class TokenManager:
    """Gerencia a substituição e restauração de tokens durante a renderização inline.

    O fluxo é:
    1. Durante o parsing inline, elementos ricos (links, imagens, footnotes) são
       substituídos por placeholders numéricos (@@@MARKATLASTOKEN0@@@).
    2. Após toda a formatação inline (bold, italic, etc.), os placeholders são
       restaurados com o Pango Markup final ou mantidos como tokens para
       renderização rica no preview.
    """

    def __init__(self) -> None:
        self._tokens: Dict[str, RichToken] = {}
        self._counter: int = 0

    @property
    def tokens(self) -> Dict[str, RichToken]:
        """Retorna o dicionário de placeholder → RichToken."""
        return self._tokens

    def save(self, token: RichToken) -> str:
        """Registra um RichToken e retorna o placeholder de substituição.

        :param token: O token rico a ser armazenado
        :return: String placeholder para inserir no texto
        """
        placeholder = f"{_TOKEN_PREFIX}{self._counter}{_TOKEN_SUFFIX}"
        self._tokens[placeholder] = token
        self._counter += 1
        return placeholder

    def save_raw(self, rendered_markup: str) -> str:
        """Registra um trecho de markup renderizado bruto (para tags que não
        precisam de tratamento especial no preview, como <kbd>, wikilinks, etc).

        :param rendered_markup: String Pango Markup já pronta
        :return: String placeholder para inserir no texto
        """
        placeholder = f"{_TOKEN_PREFIX}{self._counter}{_TOKEN_SUFFIX}"
        # Armazena como um token especial "raw" com o markup no campo label
        self._tokens[placeholder] = RichToken(kind="raw", label=rendered_markup)
        self._counter += 1
        return placeholder

    def restore_all(self, text: str, link_color: str, tag_color: str) -> str:
        """Substitui todos os placeholders pelo markup Pango final.

        :param text: Texto contendo placeholders
        :param link_color: Cor do link no tema ativo
        :param tag_color: Cor de tags/footnotes no tema ativo
        :return: Texto com todos os tokens restaurados
        """
        for placeholder, token in self._tokens.items():
            if token.kind == "raw":
                text = text.replace(placeholder, token.label)
            else:
                text = text.replace(placeholder, token.to_pango(link_color, tag_color))
        return text

    def get_rich_tokens(self) -> List[RichToken]:
        """Retorna apenas os tokens que requerem renderização rica (link, image, footnote_ref).

        :return: Lista de RichTokens não-raw
        """
        return [t for t in self._tokens.values() if t.kind != "raw"]

    def clear(self) -> None:
        """Limpa todos os tokens registrados."""
        self._tokens.clear()
        self._counter = 0
