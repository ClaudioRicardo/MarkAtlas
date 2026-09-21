"""Camada de repositórios e interfaces de persistência do MarkAtlas."""

from src.repositories.base import (
    NoteRepositoryInterface,
    VaultRepositoryInterface,
)
from src.repositories.note_repository import MarkdownNoteRepository
from src.repositories.vault_repository import FileSystemVaultRepository

__all__ = [
    "NoteRepositoryInterface",
    "VaultRepositoryInterface",
    "MarkdownNoteRepository",
    "FileSystemVaultRepository",
]
