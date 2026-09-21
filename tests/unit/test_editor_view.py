"""Testes unitários para o componente MarkdownEditorView e resolução de anexos/imagens."""

import tempfile
import unittest
from pathlib import Path

from src.core.config import default_config
from src.views.components.markdown_editor import MarkdownEditorView


class TestMarkdownEditorView(unittest.TestCase):
    """Testes para o editor de Markdown e resolução de caminhos de imagens locais."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name).resolve()
        default_config.active_vault_path = str(self.root_path)

        self.editor = MarkdownEditorView()

    def tearDown(self):
        self.temp_dir.cleanup()
        default_config.active_vault_path = None

    def test_resolve_image_relative_to_note_folder(self):
        """Valida que uma imagem salva na mesma pasta da nota é resolvida corretamente."""
        subfolder = self.root_path / "SubPasta"
        subfolder.mkdir(parents=True, exist_ok=True)
        img_file = subfolder / "diagrama1.png"
        img_file.write_bytes(b"fake png data")

        note_file = subfolder / "MinhaNota.md"
        self.editor.set_note(title="Minha Nota", content="![Diagrama](diagrama1.png)", note_path=str(note_file))

        resolved = self.editor._resolve_local_image_path("diagrama1.png")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.resolve(), img_file.resolve())

    def test_resolve_image_in_note_assets_subfolder(self):
        """Valida que uma imagem na subpasta assets/ da pasta da nota é resolvida."""
        subfolder = self.root_path / "Documentos"
        assets_dir = subfolder / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        img_file = assets_dir / "fluxo.png"
        img_file.write_bytes(b"fake png data")

        note_file = subfolder / "Doc.md"
        self.editor.set_note(title="Doc", content="![Fluxo](fluxo.png)", note_path=str(note_file))

        resolved = self.editor._resolve_local_image_path("fluxo.png")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.resolve(), img_file.resolve())

    def test_resolve_image_in_vault_root_and_vault_assets(self):
        """Valida resolução de imagem na raiz do workspace e na pasta assets/ raiz."""
        img_root = self.root_path / "logo.png"
        img_root.write_bytes(b"fake png data")

        vault_assets = self.root_path / "attachments"
        vault_assets.mkdir(parents=True, exist_ok=True)
        img_attachment = vault_assets / "anexo.png"
        img_attachment.write_bytes(b"fake png data")

        note_file = self.root_path / "Sub" / "Nota.md"
        self.editor.set_note(title="Nota", content="", note_path=str(note_file))

        # 1. Imagem na raiz do vault
        res_root = self.editor._resolve_local_image_path("logo.png")
        self.assertIsNotNone(res_root)
        self.assertEqual(res_root.resolve(), img_root.resolve())

        # 2. Imagem em attachments/ raiz
        res_att = self.editor._resolve_local_image_path("anexo.png")
        self.assertIsNotNone(res_att)
        self.assertEqual(res_att.resolve(), img_attachment.resolve())

    def test_resolve_image_url_encoded_path(self):
        """Valida que caminhos com espaços codificados em URL (%20) são decodificados."""
        img_file = self.root_path / "diagrama de fluxo.png"
        img_file.write_bytes(b"fake png data")

        self.editor.set_note(title="Nota", content="", note_path=str(self.root_path / "Nota.md"))

        resolved = self.editor._resolve_local_image_path("diagrama%20de%20fluxo.png")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.resolve(), img_file.resolve())

    def test_resolve_image_not_found_returns_none(self):
        """Valida que arquivo inexistente retorna None sem lançar exceção."""
        resolved = self.editor._resolve_local_image_path("imagem_fantasma.png")
        self.assertIsNone(resolved)

    def test_set_note_and_clear_state(self):
        """Valida que set_note define o caminho e clear reseta o estado."""
        note_path = str(self.root_path / "teste.md")
        self.editor.set_note(title="Título", content="Conteúdo", note_path=note_path)
        self.assertEqual(self.editor._current_note_path, note_path)

        self.editor.clear()
        self.assertIsNone(self.editor._current_note_path)


if __name__ == "__main__":
    unittest.main()
