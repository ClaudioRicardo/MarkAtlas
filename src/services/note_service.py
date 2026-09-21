"""Serviço de gerenciamento e manipulação de Notas Markdown."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.exceptions import NoteNotFoundError
from src.models.note import Note
from src.repositories.base import NoteRepositoryInterface
from src.repositories.note_repository import MarkdownNoteRepository

logger = logging.getLogger(__name__)


class NoteService:
    """Regras de negócio para criação, edição, renomeação, exclusão e parsing de tags em notas."""

    def __init__(self, note_repository: Optional[NoteRepositoryInterface] = None) -> None:
        self.note_repo = note_repository or MarkdownNoteRepository()

    def get_note(self, path: str) -> Optional[Note]:
        """Recupera uma nota pelo caminho do arquivo."""
        return self.note_repo.get_by_path(path)

    def create_note(
        self,
        folder_path: str,
        filename: str,
        title: Optional[str] = None,
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Note:
        """
        Cria uma nova nota Markdown em um diretório específico.
        
        :param folder_path: Pasta onde a nota será salva
        :param filename: Nome do arquivo (adiciona .md automaticamente se necessário)
        :param title: Título da nota
        :param content: Conteúdo inicial da nota
        :param metadata: Dicionário opcional de frontmatter
        :return: Instância de Note recém-criada
        """
        clean_name = filename.strip()
        if not clean_name.lower().endswith(".md"):
            clean_name = f"{clean_name}.md"

        target_dir = Path(folder_path).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / clean_name

        note_title = title or Path(clean_name).stem
        note_metadata = metadata or {}
        if "title" not in note_metadata:
            note_metadata["title"] = note_title

        note = Note(
            path=str(file_path),
            title=note_title,
            content=content,
            metadata=note_metadata,
        )

        self.note_repo.save(note)
        logger.info(f"Nova nota criada: {file_path}")
        return note

    def rename_note(self, old_path: str, new_name: str) -> Optional[Note]:
        """
        Renomeia um arquivo Markdown no disco e atualiza a entidade Note.
        
        :param old_path: Caminho atual da nota
        :param new_name: Novo nome do arquivo (com ou sem .md)
        :return: Instância de Note atualizada ou None em caso de falha
        """
        clean_name = new_name.strip()
        if not clean_name:
            raise ValueError("O novo nome da nota não pode ser vazio.")

        if not clean_name.lower().endswith(".md"):
            clean_name = f"{clean_name}.md"

        old_file = Path(old_path).resolve()
        if not old_file.exists() or not old_file.is_file():
            logger.warning(f"Nota não encontrada para renomear: {old_path}")
            return None

        new_file = old_file.parent / clean_name
        if new_file.exists() and new_file != old_file:
            raise FileExistsError(f"Já existe uma nota com o nome '{clean_name}'.")

        try:
            old_file.rename(new_file)
            logger.info(f"Nota renomeada de {old_file.name} para {new_file.name}")
            return self.get_note(str(new_file))
        except Exception as e:
            logger.error(f"Falha ao renomear nota {old_path} para {new_name}: {e}")
            return None

    def save_note(self, note: Note) -> bool:
        """Persiste as alterações de uma nota no disco."""
        return self.note_repo.save(note)

    def delete_note(self, path: str) -> bool:
        """Remove a nota do disco."""
        return self.note_repo.delete(path)

    def extract_tags(self, note: Note) -> List[str]:
        """Retorna todas as tags atualizadas da nota."""
        return self.note_repo.extract_tags(note.metadata, note.content)
