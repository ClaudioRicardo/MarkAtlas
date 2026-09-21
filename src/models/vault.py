"""Modelo de domínio para o Cofre de Notas (Vault)."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from src.models.note import Note


@dataclass
class Vault:
    """Entidade que representa o diretório raiz de um repositório/cofre de notas."""

    path: str
    name: str = ""
    notes: Dict[str, Note] = field(default_factory=dict)
    is_loaded: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            self.name = Path(self.path).name

    @property
    def root_path(self) -> Path:
        """Retorna o caminho do vault como um objeto Path."""
        return Path(self.path).resolve()

    @property
    def total_notes(self) -> int:
        """Número total de notas carregadas no vault."""
        return len(self.notes)

    def add_note(self, note: Note) -> None:
        """Adiciona ou atualiza uma nota no vault."""
        self.notes[note.path] = note

    def remove_note(self, path: str) -> Optional[Note]:
        """Remove uma nota do vault pelo caminho."""
        return self.notes.pop(path, None)

    def get_note(self, path: str) -> Optional[Note]:
        """Recupera uma nota pelo caminho relativo ou absoluto."""
        return self.notes.get(path)

    def list_notes(self) -> List[Note]:
        """Retorna a lista de todas as notas do vault."""
        return list(self.notes.values())
