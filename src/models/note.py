"""Modelo de domínio para Nota Markdown (Note)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Note:
    """Entidade de domínio pura que representa um arquivo Markdown com metadados."""

    path: str
    title: str
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_dirty: bool = False

    def add_tag(self, tag: str) -> None:
        """Adiciona uma tag à nota se não existir."""
        clean_tag = tag.strip().lstrip("#")
        if clean_tag and clean_tag not in self.tags:
            self.tags.append(clean_tag)

    def remove_tag(self, tag: str) -> None:
        """Remove uma tag da nota."""
        clean_tag = tag.strip().lstrip("#")
        if clean_tag in self.tags:
            self.tags.remove(clean_tag)

    def has_tag(self, tag: str) -> bool:
        """Verifica se a nota possui a tag especificada."""
        clean_tag = tag.strip().lstrip("#")
        return clean_tag in self.tags

    @property
    def word_count(self) -> int:
        """Retorna a contagem de palavras do conteúdo textual."""
        return len(self.content.split()) if self.content else 0

    @property
    def line_count(self) -> int:
        """Retorna o número de linhas da nota."""
        return len(self.content.splitlines()) if self.content else 0
