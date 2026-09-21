"""Repositório de Cofres (Vaults) baseado no sistema de arquivos local."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from src.models.note import Note
from src.models.vault import Vault
from src.repositories.base import VaultRepositoryInterface
from src.repositories.note_repository import MarkdownNoteRepository
from src.core.exceptions import VaultNotFoundError

logger = logging.getLogger(__name__)


class FileSystemVaultRepository(VaultRepositoryInterface):
    """Gerencia a varredura e estrutura hierárquica de um cofre de notas em disco."""

    IGNORED_DIRECTORIES: Set[str] = {
        ".git",
        ".gemini",
        ".agent",
        ".agents",
        ".opencode",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "node_modules",
        ".obsidian",
        ".trash",
    }

    def __init__(self, note_repository: Optional[MarkdownNoteRepository] = None) -> None:
        self.note_repo = note_repository or MarkdownNoteRepository()

    def scan(self, vault: Vault) -> List[Note]:
        """Varre o diretório do cofre e carrega todas as notas Markdown encontradas."""
        root = Path(vault.path).resolve()
        if not root.exists() or not root.is_dir():
            raise VaultNotFoundError(f"Diretório do cofre não encontrado: {root}")

        vault.notes.clear()
        found_notes: List[Note] = []

        for file_path in root.rglob("*.md"):
            # Verifica se algum segmento do caminho está na lista de ignorados
            relative_parts = file_path.relative_to(root).parts
            if any(part.startswith(".") or part in self.IGNORED_DIRECTORIES for part in relative_parts):
                continue

            note = self.note_repo.get_by_path(str(file_path))
            if note:
                vault.add_note(note)
                found_notes.append(note)

        vault.is_loaded = True
        logger.info(f"Cofre '{vault.name}' escaneado com sucesso. Total de notas: {len(found_notes)}")
        return found_notes

    def get_vault_structure(self, vault: Vault) -> Dict[str, Any]:
        """
        Retorna a árvore hierárquica de pastas e arquivos Markdown do Vault.
        Formato de cada nó:
        {
            "name": str,
            "path": str,
            "type": "folder" | "file",
            "children": [...] (apenas para pastas)
        }
        """
        root = Path(vault.path).resolve()
        if not root.exists() or not root.is_dir():
            return {"name": vault.name, "path": vault.path, "type": "folder", "children": []}

        return self._build_tree(root, root)

    def _build_tree(self, current_dir: Path, root: Path) -> Dict[str, Any]:
        """Constrói recursivamente o dicionário da árvore a partir de um diretório."""
        node: Dict[str, Any] = {
            "name": current_dir.name if current_dir != root else root.name,
            "path": str(current_dir),
            "type": "folder",
            "children": [],
        }

        try:
            entries = sorted(list(current_dir.iterdir()), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.name.startswith(".") or entry.name in self.IGNORED_DIRECTORIES:
                    continue

                if entry.is_dir():
                    child_tree = self._build_tree(entry, root)
                    # Só adiciona a pasta se tiver conteúdo ou mantiver a estrutura
                    node["children"].append(child_tree)
                elif entry.is_file() and entry.suffix.lower() == ".md":
                    node["children"].append({
                        "name": entry.name,
                        "path": str(entry),
                        "type": "file",
                    })
        except PermissionError as err:
            logger.warning(f"Permissão negada ao acessar {current_dir}: {err}")

        return node
