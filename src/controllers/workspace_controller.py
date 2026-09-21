"""Controlador para orquestração de eventos de Workspace, Navegação e Notas."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.config import AppConfig, default_config
from src.core.events import EventBus
from src.models.note import Note
from src.models.vault import Vault
from src.services.note_service import NoteService
from src.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class WorkspaceController:
    """Controlador que faz a ponte entre a interface gráfica (Views) e a lógica de negócio (Services)."""

    def __init__(
        self,
        vault_service: Optional[VaultService] = None,
        note_service: Optional[NoteService] = None,
        event_bus: Optional[EventBus] = None,
        config: Optional[AppConfig] = None,
    ) -> None:
        self.vault_service = vault_service or VaultService()
        self.note_service = note_service or NoteService()
        self.event_bus = event_bus or EventBus()
        self.config = config or default_config
        self.current_note: Optional[Note] = None

    def get_active_vault(self) -> Optional[Vault]:
        """Retorna o cofre ativo na sessão (delegado do VaultService)."""
        return self.vault_service.get_active_vault()

    def open_workspace(self, folder_path: str) -> Vault:
        """Abre uma pasta como workspace/cofre e notifica ouvintes."""
        vault = self.vault_service.open_vault(folder_path)
        self.current_note = None
        self.event_bus.publish("workspace_opened", {"path": folder_path, "name": vault.name})
        return vault

    def get_workspace_tree(self) -> Dict[str, Any]:
        """Retorna a estrutura em árvore de arquivos do workspace ativo."""
        return self.vault_service.get_vault_tree()

    def load_note(self, file_path: str) -> Optional[Note]:
        """Carrega uma nota a partir do caminho e atualiza a nota ativa."""
        note = self.note_service.get_note(file_path)
        if note:
            self.current_note = note
            self.event_bus.publish("note_loaded", {"path": note.path, "title": note.title, "tags": note.tags})
        return note

    def save_current_note(self, title: str, content: str) -> bool:
        """Salva a nota atualmente aberta no editor."""
        if not self.current_note:
            logger.warning("Nenhuma nota ativa para salvar.")
            return False

        self.current_note.title = title
        self.current_note.content = content
        if self.current_note.metadata is None:
            self.current_note.metadata = {}
        self.current_note.metadata["title"] = title

        # Atualiza tags dinamicamente
        self.current_note.tags = self.note_service.extract_tags(self.current_note)

        success = self.note_service.save_note(self.current_note)
        if success:
            self.event_bus.publish("note_saved", {"path": self.current_note.path, "title": title})
        return success

    def create_new_note(self, folder_path: Optional[str] = None, filename: str = "Sem Título.md") -> Optional[Note]:
        """Cria uma nova nota no workspace ativo ou em pasta específica."""
        active_vault = self.vault_service.get_active_vault()
        target_dir = folder_path or (active_vault.path if active_vault else None)

        if not target_dir:
            logger.warning("Não é possível criar nota sem um workspace aberto.")
            return None

        base_name = Path(filename).stem
        candidate_path = Path(target_dir) / f"{base_name}.md"
        counter = 1
        while candidate_path.exists():
            candidate_path = Path(target_dir) / f"{base_name} {counter}.md"
            counter += 1

        note = self.note_service.create_note(
            folder_path=target_dir,
            filename=candidate_path.name,
            title=candidate_path.stem,
            content="",
        )
        self.current_note = note
        self.event_bus.publish("note_created", {"path": note.path, "title": note.title})
        return note

    def delete_note(self, note_path: str) -> bool:
        """Remove a nota do disco e limpa a nota ativa se for a mesma."""
        success = self.note_service.delete_note(note_path)
        if success:
            if self.current_note and Path(self.current_note.path).resolve() == Path(note_path).resolve():
                self.current_note = None
            self.event_bus.publish("note_deleted", {"path": note_path})
        return success

    def create_folder(self, parent_path: str, folder_name: str) -> Optional[Path]:
        """Cria uma subpasta dentro do workspace."""
        try:
            folder = self.vault_service.create_folder(parent_path, folder_name)
            self.event_bus.publish("folder_created", {"path": str(folder), "parent": parent_path})
            return folder
        except Exception as e:
            logger.error(f"Erro ao criar pasta {folder_name} em {parent_path}: {e}")
            return None

    def delete_folder(self, folder_path: str) -> bool:
        """Exclui uma pasta recursivamente."""
        resolved = Path(folder_path).resolve()
        success = self.vault_service.delete_folder(folder_path)
        if success:
            # Se a nota ativa estava dentro da pasta excluída, reseta
            if self.current_note:
                note_file = Path(self.current_note.path).resolve()
                if resolved in note_file.parents:
                    self.current_note = None
            self.event_bus.publish("folder_deleted", {"path": folder_path})
        return success

    def rename_note(self, old_path: str, new_name: str) -> Optional[Note]:
        """Renomeia a nota no disco e atualiza a nota ativa se for a mesma."""
        renamed_note = self.note_service.rename_note(old_path, new_name)
        if renamed_note:
            if self.current_note and Path(self.current_note.path).resolve() == Path(old_path).resolve():
                self.current_note = renamed_note
            self.event_bus.publish("note_renamed", {
                "old_path": old_path,
                "new_path": renamed_note.path,
                "title": renamed_note.title,
            })
        return renamed_note

    def rename_folder(self, old_path: str, new_name: str) -> Optional[Path]:
        """Renomeia uma pasta no workspace e atualiza o caminho da nota ativa se estiver contida nela."""
        old_resolved = Path(old_path).resolve()
        new_folder = self.vault_service.rename_folder(old_path, new_name)
        if new_folder:
            if self.current_note:
                note_resolved = Path(self.current_note.path).resolve()
                if old_resolved in note_resolved.parents:
                    relative_path = note_resolved.relative_to(old_resolved)
                    new_note_path = new_folder / relative_path
                    self.current_note.path = str(new_note_path)

            self.event_bus.publish("folder_renamed", {
                "old_path": old_path,
                "new_path": str(new_folder),
            })
        return new_folder

    def refresh_workspace(self) -> None:
        """Atualiza a lista de notas do workspace ativo."""
        self.vault_service.refresh_vault()
        self.event_bus.publish("workspace_refreshed", {})
