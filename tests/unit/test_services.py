"""Testes unitários para a camada de serviços e controllers (VaultService, NoteService, WorkspaceController)."""

import tempfile
import unittest
from pathlib import Path
from src.core.config import AppConfig
from src.core.events import EventBus
from src.core.exceptions import VaultNotFoundError
from src.services.note_service import NoteService
from src.services.vault_service import VaultService
from src.controllers.workspace_controller import WorkspaceController
from src.repositories.note_repository import MarkdownNoteRepository
from src.repositories.vault_repository import FileSystemVaultRepository


class TestServicesAndController(unittest.TestCase):
    """Testes para serviços de workspace, notas e controlador."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.config = AppConfig(project_root=self.base_path)
        self.event_bus = EventBus()

        self.note_repo = MarkdownNoteRepository()
        self.vault_repo = FileSystemVaultRepository(self.note_repo)

        self.vault_service = VaultService(vault_repository=self.vault_repo, config=self.config)
        self.note_service = NoteService(note_repository=self.note_repo)
        self.controller = WorkspaceController(
            vault_service=self.vault_service,
            note_service=self.note_service,
            event_bus=self.event_bus,
            config=self.config,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_vault_service_open_and_tree(self):
        """Valida abertura de vault e recuperação da árvore hierárquica."""
        # Cria arquivo dentro do diretório
        doc_path = self.base_path / "Guia.md"
        doc_path.write_text("# Guia de Uso\n\nTexto com #tutorial", encoding="utf-8")

        vault = self.vault_service.open_vault(str(self.base_path))
        self.assertEqual(vault.path, str(self.base_path))
        self.assertEqual(vault.total_notes, 1)
        self.assertEqual(self.config.active_vault_path, str(self.base_path))

        tree = self.vault_service.get_vault_tree()
        self.assertEqual(len(tree["children"]), 1)
        self.assertEqual(tree["children"][0]["name"], "Guia.md")

    def test_vault_service_invalid_path(self):
        """Valida exceção ao abrir caminho inexistente."""
        with self.assertRaises(VaultNotFoundError):
            self.vault_service.open_vault(str(self.base_path / "inexistente"))

    def test_note_service_create_and_extract_tags(self):
        """Valida criação de nota e extração de tags."""
        note = self.note_service.create_note(
            folder_path=str(self.base_path),
            filename="Reuniao.md",
            title="Reunião de Alinhamento",
            content="# Reunião\n\nPauta com #planejamento e #sdd",
        )

        self.assertTrue(Path(note.path).exists())
        self.assertEqual(note.title, "Reunião de Alinhamento")

        tags = self.note_service.extract_tags(note)
        self.assertIn("planejamento", tags)
        self.assertIn("sdd", tags)

    def test_workspace_controller_flow(self):
        """Valida o fluxo completo do WorkspaceController."""
        # 1. Abrir Workspace
        vault = self.controller.open_workspace(str(self.base_path))
        self.assertIsNotNone(vault)

        # 2. Criar Nova Nota
        new_note = self.controller.create_new_note(filename="Anotacoes.md")
        self.assertIsNotNone(new_note)
        self.assertEqual(self.controller.current_note.path, new_note.path)

        # 3. Salvar Nota Ativa
        saved = self.controller.save_current_note(
            title="Anotações Gerais",
            content="Texto atualizado com tag #importante.",
        )
        self.assertTrue(saved)
        self.assertIn("importante", self.controller.current_note.tags)

        # 4. Carregar Nota
        loaded_note = self.controller.load_note(new_note.path)
        self.assertIsNotNone(loaded_note)
        self.assertEqual(loaded_note.title, "Anotações Gerais")


if __name__ == "__main__":
    unittest.main()
