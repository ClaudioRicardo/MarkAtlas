"""Testes unitários para o módulo core (Config, EventBus, Exceptions, StyleManager)."""

import unittest
from src.core.config import AppConfig, default_config
from src.core.events import EventBus
from src.core.style_manager import StyleManager
from src.core.exceptions import (
    MarkAtlasError,
    NoteNotFoundError,
    InvalidFrontmatterError,
    VaultNotFoundError,
)


class TestCore(unittest.TestCase):
    """Suíte de testes para a camada core do MarkAtlas."""

    def test_app_config_paths_and_theming(self):
        """Valida resolução de caminhos de assets, estilos e tokens de tema na configuração."""
        config = AppConfig()
        self.assertEqual(config.app_name, "MarkAtlas")
        self.assertEqual(config.theme, "dark")
        self.assertTrue(config.assets_dir.exists())
        self.assertTrue(config.styles_dir.exists())

        # Tema escuro (padrão)
        dark_sheets = config.get_style_sheets(theme="dark")
        self.assertGreaterEqual(len(dark_sheets), 5)
        sheet_names_dark = [s.name for s in dark_sheets]
        self.assertEqual(sheet_names_dark[0], "tokens_dark.css")
        self.assertIn("main.css", sheet_names_dark)
        self.assertIn("sidebar.css", sheet_names_dark)
        self.assertIn("editor.css", sheet_names_dark)
        self.assertIn("components.css", sheet_names_dark)

        # Tema claro
        light_sheets = config.get_style_sheets(theme="light")
        sheet_names_light = [s.name for s in light_sheets]
        self.assertEqual(sheet_names_light[0], "tokens_light.css")
        self.assertIn("main.css", sheet_names_light)

    def test_style_manager_apply_theme(self):
        """Valida a alternância de tema no StyleManager."""
        config = AppConfig(theme="dark")
        # Em ambiente de teste unitário sem display/GTK inicializado, deve lidar graciosamente
        StyleManager.apply_theme("light", config=config)
        self.assertEqual(config.theme, "light")

        StyleManager.apply_theme("dark", config=config)
        self.assertEqual(config.theme, "dark")

        # Teste com tema inválido (deve reverter para 'dark')
        StyleManager.apply_theme("invalid_theme", config=config)
        self.assertEqual(config.theme, "dark")

    def test_event_bus_pub_sub(self):
        """Valida o funcionamento do barramento de eventos (subscribe, publish, unsubscribe)."""
        bus = EventBus()
        received_data = []

        def on_note_saved(payload):
            received_data.append(payload)

        bus.subscribe("note_saved", on_note_saved)
        bus.publish("note_saved", {"path": "test.md"})

        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0]["path"], "test.md")

        # Unsubscribe
        bus.unsubscribe("note_saved", on_note_saved)
        bus.publish("note_saved", {"path": "test2.md"})
        self.assertEqual(len(received_data), 1)

        # Clear
        bus.subscribe("note_deleted", on_note_saved)
        bus.clear()
        bus.publish("note_deleted", {"path": "deleted.md"})
        self.assertEqual(len(received_data), 1)

    def test_domain_exceptions_hierarchy(self):
        """Valida a hierarquia e formatação de mensagens das exceções de domínio."""
        err_note = NoteNotFoundError("docs/plan.md")
        self.assertIsInstance(err_note, MarkAtlasError)
        self.assertIn("docs/plan.md", str(err_note))

        err_fm = InvalidFrontmatterError("notes/intro.md", "YAML inválido na linha 4")
        self.assertIsInstance(err_fm, MarkAtlasError)
        self.assertIn("YAML inválido na linha 4", str(err_fm))

        err_vault = VaultNotFoundError("/vault/empty")
        self.assertIsInstance(err_vault, MarkAtlasError)
        self.assertIn("/vault/empty", str(err_vault))


if __name__ == "__main__":
    unittest.main()
