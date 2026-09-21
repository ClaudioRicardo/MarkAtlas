"""Testes unitários para funcionalidade de acessibilidade e ajuste de tamanho de fonte."""

import unittest
from unittest.mock import MagicMock

from src.core.config import (
    DEFAULT_FONT_SIZE,
    FONT_SIZE_STEP,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    AppConfig,
    default_config,
)
from src.views.components.markdown_editor import MarkdownEditorView
from src.views.main_window import MainWindow


class TestFontAccessibility(unittest.TestCase):
    """Testa os métodos e regras de negócio do dimensionamento de fonte para acessibilidade."""

    def setUp(self):
        default_config.font_size = DEFAULT_FONT_SIZE

    def tearDown(self):
        default_config.font_size = DEFAULT_FONT_SIZE

    def test_app_config_font_size_operations(self):
        """Valida que AppConfig respeita limites mínimo, máximo e passos de incremento."""
        config = AppConfig(font_size=14)

        # 1. Incremento padrão
        new_size = config.increase_font_size()
        self.assertEqual(new_size, 14 + FONT_SIZE_STEP)
        self.assertEqual(config.font_size, 16)

        # 2. Incrementos sucessivos até o limite máximo
        config.font_size = MAX_FONT_SIZE - 1
        new_size = config.increase_font_size()
        self.assertEqual(new_size, MAX_FONT_SIZE)

        # Incremento além do máximo não ultrapassa MAX_FONT_SIZE
        new_size = config.increase_font_size()
        self.assertEqual(new_size, MAX_FONT_SIZE)

        # 3. Decrementos sucessivos até o limite mínimo
        config.font_size = MIN_FONT_SIZE + 1
        new_size = config.decrease_font_size()
        self.assertEqual(new_size, MIN_FONT_SIZE)

        # Decremento além do mínimo não ultrapassa MIN_FONT_SIZE
        new_size = config.decrease_font_size()
        self.assertEqual(new_size, MIN_FONT_SIZE)

        # 4. Restauração do padrão
        config.font_size = 28
        new_size = config.reset_font_size()
        self.assertEqual(new_size, DEFAULT_FONT_SIZE)
        self.assertEqual(config.font_size, DEFAULT_FONT_SIZE)

    def test_markdown_editor_view_font_size_methods(self):
        """Valida os métodos de controle de fonte no MarkdownEditorView."""
        editor = MarkdownEditorView()

        # Verifica valor inicial
        self.assertEqual(editor.get_font_size(), DEFAULT_FONT_SIZE)

        # Aplica tamanho específico
        clamped = editor.apply_font_size(18)
        self.assertEqual(clamped, 18)
        self.assertEqual(editor.get_font_size(), 18)
        self.assertEqual(default_config.font_size, 18)

        # Aumentar
        new_size = editor.increase_font_size()
        self.assertEqual(new_size, 20)

        # Diminuir
        new_size = editor.decrease_font_size()
        self.assertEqual(new_size, 18)

        # Reset
        new_size = editor.reset_font_size()
        self.assertEqual(new_size, DEFAULT_FONT_SIZE)

        # Clamping com valores fora dos limites
        self.assertEqual(editor.apply_font_size(5), MIN_FONT_SIZE)
        self.assertEqual(editor.apply_font_size(100), MAX_FONT_SIZE)

    def test_main_window_font_handlers(self):
        """Valida que os manipuladores de MainWindow invocam os métodos do editor e atualizam o status."""
        window = MainWindow()
        mock_editor = MagicMock()
        mock_editor.increase_font_size.return_value = 16
        mock_editor.decrease_font_size.return_value = 12
        mock_editor.reset_font_size.return_value = 14

        mock_status = MagicMock()

        window._editor_view = mock_editor
        window._lbl_status = mock_status

        # Teste Aumentar
        window._on_increase_font()
        mock_editor.increase_font_size.assert_called_once()
        mock_status.set_label.assert_called_with("🔍 Tamanho da fonte: 16px")

        # Teste Reduzir
        window._on_decrease_font()
        mock_editor.decrease_font_size.assert_called_once()
        mock_status.set_label.assert_called_with("🔍 Tamanho da fonte: 12px")

        # Teste Reset
        window._on_reset_font()
        mock_editor.reset_font_size.assert_called_once()
        mock_status.set_label.assert_called_with("🔍 Tamanho da fonte restaurado: 14px (padrão)")


if __name__ == "__main__":
    unittest.main()
