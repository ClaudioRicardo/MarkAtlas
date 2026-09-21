"""Testes unitários para operações contextuais de pastas e arquivos (criação, renomeação e exclusão)."""

import tempfile
import unittest
from pathlib import Path
from src.core.config import AppConfig
from src.core.events import EventBus
from src.services.note_service import NoteService
from src.services.vault_service import VaultService
from src.controllers.workspace_controller import WorkspaceController
from src.repositories.note_repository import MarkdownNoteRepository
from src.repositories.vault_repository import FileSystemVaultRepository


class TestFolderOperations(unittest.TestCase):
    """Testes para criação/renomeação/exclusão de subpastas e notas."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.config = AppConfig(project_root=self.base_path)
        self.event_bus = EventBus()

        self.note_repo = MarkdownNoteRepository()
        self.vault_repo = FileSystemVaultRepository(self.note_repo)
        self.vault_service = VaultService(self.vault_repo, self.config)
        self.note_service = NoteService(self.note_repo)
        self.controller = WorkspaceController(
            self.vault_service,
            self.note_service,
            self.event_bus,
            self.config,
        )

        self.controller.open_workspace(str(self.base_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_delete_subfolder(self):
        """Valida criação e exclusão de subpastas."""
        subfolder = self.controller.create_folder(str(self.base_path), "Projetos")
        self.assertIsNotNone(subfolder)
        self.assertTrue(subfolder.exists())
        self.assertTrue(subfolder.is_dir())

        note_in_sub = self.controller.create_new_note(folder_path=str(subfolder), filename="Doc.md")
        self.assertIsNotNone(note_in_sub)
        self.assertTrue(Path(note_in_sub.path).exists())

        deleted = self.controller.delete_folder(str(subfolder))
        self.assertTrue(deleted)
        self.assertFalse(subfolder.exists())
        self.assertIsNone(self.controller.current_note)

    def test_rename_folder_operation(self):
        """Valida renomeação de subpasta e atualização de caminhos."""
        subfolder = self.controller.create_folder(str(self.base_path), "Antigo")
        self.assertIsNotNone(subfolder)

        note = self.controller.create_new_note(folder_path=str(subfolder), filename="Texto.md")
        self.assertIsNotNone(note)

        renamed_folder = self.controller.rename_folder(str(subfolder), "Novo")
        self.assertIsNotNone(renamed_folder)
        self.assertTrue(renamed_folder.exists())
        self.assertFalse(subfolder.exists())
        self.assertIn("Novo", self.controller.current_note.path)

    def test_root_workspace_deletion_and_rename_protection(self):
        """Valida que a pasta raiz do workspace não pode ser excluída nem renomeada."""
        deleted = self.vault_service.delete_folder(str(self.base_path))
        self.assertFalse(deleted)
        self.assertTrue(self.base_path.exists())

        renamed = self.vault_service.rename_folder(str(self.base_path), "OutroNome")
        self.assertIsNone(renamed)

    def test_rename_note_operation(self):
        """Valida renomeação de arquivo Markdown."""
        note = self.controller.create_new_note(filename="Rascunho.md")
        self.assertIsNotNone(note)
        self.assertEqual(self.controller.current_note.path, note.path)

        renamed_note = self.controller.rename_note(note.path, "ArtigoFinal.md")
        self.assertIsNotNone(renamed_note)
        self.assertTrue(Path(renamed_note.path).exists())
        self.assertFalse(Path(note.path).exists())
        self.assertEqual(self.controller.current_note.path, renamed_note.path)

    def test_delete_note_operation(self):
        """Valida exclusão de nota ativa e limpeza de estado."""
        note = self.controller.create_new_note(filename="ParaDeletar.md")
        self.assertIsNotNone(note)
        self.assertEqual(self.controller.current_note.path, note.path)

        deleted = self.controller.delete_note(note.path)
        self.assertTrue(deleted)
        self.assertFalse(Path(note.path).exists())
        self.assertIsNone(self.controller.current_note)


if __name__ == "__main__":
    unittest.main()
