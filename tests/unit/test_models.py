"""Testes unitários para as entidades de domínio puras."""

import unittest
from datetime import datetime
from src.models.note import Note
from src.models.tag import Tag
from src.models.vault import Vault
from src.models.backlink import Backlink


class TestModels(unittest.TestCase):
    """Suíte de testes para os modelos de domínio."""

    def test_note_creation_and_properties(self):
        """Valida a instanciação e propriedades calculadas da entidade Note."""
        note = Note(
            path="notes/welcome.md",
            title="Welcome Note",
            content="Hello world!\nEsta é uma linha de teste.\nMarkAtlas rocks.",
            metadata={"author": "Claudio", "status": "draft"},
            tags=["markdown", "docs"],
            created_at=datetime(2026, 8, 13, 10, 0, 0),
        )

        self.assertEqual(note.path, "notes/welcome.md")
        self.assertEqual(note.title, "Welcome Note")
        self.assertEqual(note.word_count, 10)
        self.assertEqual(note.line_count, 3)
        self.assertEqual(note.metadata["author"], "Claudio")
        self.assertTrue(note.has_tag("markdown"))
        self.assertTrue(note.has_tag("#markdown"))
        self.assertFalse(note.has_tag("nonexistent"))

    def test_note_tag_operations(self):
        """Valida adição e remoção de tags na entidade Note."""
        note = Note(path="test.md", title="Test")
        self.assertEqual(len(note.tags), 0)

        note.add_tag("#project")
        self.assertTrue(note.has_tag("project"))
        self.assertIn("project", note.tags)

        # Evita duplicação
        note.add_tag("project")
        self.assertEqual(len(note.tags), 1)

        note.remove_tag("project")
        self.assertFalse(note.has_tag("project"))
        self.assertEqual(len(note.tags), 0)

    def test_tag_model(self):
        """Valida o modelo Tag e contagem de referências."""
        tag = Tag(name="#knowledge")
        self.assertEqual(tag.name, "knowledge")
        self.assertEqual(tag.formatted_name, "#knowledge")
        self.assertEqual(tag.note_count, 0)

        tag.add_note_path("note1.md")
        tag.add_note_path("note2.md")
        self.assertEqual(tag.note_count, 2)

        tag.remove_note_path("note1.md")
        self.assertEqual(tag.note_count, 1)

    def test_vault_model(self):
        """Valida o gerenciamento de notas dentro da entidade Vault."""
        vault = Vault(path="/tmp/my_vault", name="Workspace")
        self.assertEqual(vault.name, "Workspace")
        self.assertEqual(vault.total_notes, 0)

        note1 = Note(path="a.md", title="Nota A")
        note2 = Note(path="b.md", title="Nota B")

        vault.add_note(note1)
        vault.add_note(note2)
        self.assertEqual(vault.total_notes, 2)
        self.assertEqual(vault.get_note("a.md"), note1)
        self.assertEqual(len(vault.list_notes()), 2)

        removed = vault.remove_note("a.md")
        self.assertEqual(removed, note1)
        self.assertEqual(vault.total_notes, 1)
        self.assertIsNone(vault.get_note("a.md"))

    def test_backlink_model(self):
        """Valida a entidade Backlink e detecção de wikilinks."""
        bl_wiki = Backlink(
            source_path="index.md",
            target_path="guides/getting-started.md",
            anchor_text="Getting Started Guide",
            line_number=12,
        )
        self.assertTrue(bl_wiki.is_wikilink)
        self.assertEqual(bl_wiki.line_number, 12)

        bl_web = Backlink(
            source_path="index.md",
            target_path="https://example.com",
            anchor_text="http://example.com",
        )
        self.assertFalse(bl_web.is_wikilink)


if __name__ == "__main__":
    unittest.main()
