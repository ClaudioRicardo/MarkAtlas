"""Modelo de domínio para Ligações entre Notas (Backlinks / Wikilinks)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Backlink:
    """Entidade que expressa uma ligação direcionada entre duas notas no grafo de conhecimento."""

    source_path: str
    target_path: str
    anchor_text: str = ""
    line_number: Optional[int] = None

    @property
    def is_wikilink(self) -> bool:
        """Indica se o link tem formato padrão wikilink ([[nota]])." """
        return bool(self.anchor_text and not self.anchor_text.startswith("http"))
