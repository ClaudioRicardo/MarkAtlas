"""Testes unitários para a camada de repositórios (MarkdownNoteRepository, FileSystemVaultRepository)."""

import tempfile
import unittest
from pathlib import Path
from src.models.note import Note
from src.models.vault import Vault
from src.repositories.note_repository import MarkdownNoteRepository
from src.repositories.vault_repository import FileSystemVaultRepository


class TestRepositories(unittest.TestCase):
    """Testes para repositórios de sistema de arquivos e parsing de Markdown."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.note_repo = MarkdownNoteRepository(str(self.base_path))
        self.vault_repo = FileSystemVaultRepository(self.note_repo)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_get_note_with_frontmatter_and_tags(self):
        """Valida escrita e leitura de nota com YAML frontmatter e tags extraídas."""
        note_path = self.base_path / "ideias.md"
        content_raw = """---
title: Minhas Ideias Incríveis
tags:
  - inovacao
  - pkm
---
# Minhas Ideias Incríveis

Este é o corpo com uma tag adicional #inteligencia-artificial e #pkm duplicada.
"""
        note_path.write_text(content_raw, encoding="utf-8")

        note = self.note_repo.get_by_path(str(note_path))
        self.assertIsNotNone(note)
        self.assertEqual(note.title, "Minhas Ideias Incríveis")
        self.assertIn("inovacao", note.tags)
        self.assertIn("pkm", note.tags)
        self.assertIn("inteligencia-artificial", note.tags)

        # Modifica e salva a nota
        note.content = "Conteúdo atualizado com nova tag #python."
        saved = self.note_repo.save(note)
        self.assertTrue(saved)

        reloaded = self.note_repo.get_by_path(str(note_path))
        self.assertIsNotNone(reloaded)
        self.assertIn("#python", reloaded.content)

    def test_note_title_fallback_to_h1_and_filename(self):
        """Valida fallback de título para primeiro H1 e para nome do arquivo."""
        # Fallback para H1
        note_h1 = self.base_path / "nota_sem_frontmatter.md"
        note_h1.write_text("# Título H1 do Documento\n\nTexto de teste.", encoding="utf-8")

        n1 = self.note_repo.get_by_path(str(note_h1))
        self.assertEqual(n1.title, "Título H1 do Documento")

        # Fallback para nome do arquivo
        note_plain = self.base_path / "rascunho.md"
        note_plain.write_text("Apenas texto sem cabeçalho.", encoding="utf-8")

        n2 = self.note_repo.get_by_path(str(note_plain))
        self.assertEqual(n2.title, "rascunho")

    def test_delete_and_exists_note(self):
        """Valida exclusão e verificação de existência."""
        note_file = self.base_path / "temp.md"
        note_file.write_text("Teste", encoding="utf-8")
        self.assertTrue(self.note_repo.exists(str(note_file)))

        deleted = self.note_repo.delete(str(note_file))
        self.assertTrue(deleted)
        self.assertFalse(self.note_repo.exists(str(note_file)))

    def test_vault_repository_scan_and_tree_structure(self):
        """Valida varredura de diretórios e construção da árvore ignorando pastas ocultas."""
        # Cria estrutura de pastas
        sub1 = self.base_path / "Projetos"
        sub1.mkdir()
        (sub1 / "projeto1.md").write_text("# Projeto 1\nTag: #dev", encoding="utf-8")
        (sub1 / "projeto2.md").write_text("# Projeto 2", encoding="utf-8")

        # Pasta oculta que deve ser ignorada
        hidden_dir = self.base_path / ".git"
        hidden_dir.mkdir()
        (hidden_dir / "ignored.md").write_text("Ignorar", encoding="utf-8")

        vault = Vault(path=str(self.base_path), name="Meu Cofre")
        scanned_notes = self.vault_repo.scan(vault)

        self.assertEqual(len(scanned_notes), 2)
        self.assertEqual(vault.total_notes, 2)

        tree = self.vault_repo.get_vault_structure(vault)
        self.assertEqual(tree["type"], "folder")
        self.assertEqual(len(tree["children"]), 1)  # Apenas a pasta Projetos
        self.assertEqual(tree["children"][0]["name"], "Projetos")
        self.assertEqual(len(tree["children"][0]["children"]), 2)  # projeto1.md e projeto2.md


if __name__ == "__main__":
    unittest.main()
