"""Modelo de domínio para Tag/Categoria."""

from dataclasses import dataclass, field
from typing import Set


@dataclass
class Tag:
    """Entidade que representa uma Tag de categorização de notas."""

    name: str
    note_paths: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.name = self.name.strip().lstrip("#")

    @property
    def formatted_name(self) -> str:
        """Retorna o nome formatado com prefixo hashtag."""
        return f"#{self.name}"

    @property
    def note_count(self) -> int:
        """Quantidade de notas associadas a esta tag."""
        return len(self.note_paths)

    def add_note_path(self, path: str) -> None:
        """Associa uma nota a esta tag."""
        self.note_paths.add(path)

    def remove_note_path(self, path: str) -> None:
        """Remove a associação de uma nota com esta tag."""
        self.note_paths.discard(path)
