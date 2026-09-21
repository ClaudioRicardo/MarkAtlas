"""Testes unitários para o componente ImageLightboxDialog (visualização ampliada e zoom)."""

import tempfile
import unittest
from pathlib import Path

from src.views.components.image_lightbox import ImageLightboxDialog


class TestImageLightboxDialog(unittest.TestCase):
    """Suíte de testes para o modal de lightbox de imagens e diagramas."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name).resolve()

        # Cria uma imagem de teste simulada
        self.sample_img = self.root_path / "diagrama_teste.png"
        self.sample_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lightbox_initialization(self):
        """Valida inicialização do diálogo com caminho e título customizado."""
        dlg = ImageLightboxDialog(
            image_path=str(self.sample_img),
            title="Fluxo de Autenticação",
        )
        self.assertEqual(dlg.image_path, str(self.sample_img))
        self.assertEqual(dlg._custom_title, "Fluxo de Autenticação")
        self.assertEqual(dlg._current_zoom, 1.0)

    def test_zoom_in_and_zoom_out_limits(self):
        """Valida incremento de zoom (+25%) e limites de 25% a 400%."""
        dlg = ImageLightboxDialog(image_path=str(self.sample_img))

        # Zoom In
        dlg.zoom_in()
        self.assertEqual(dlg._current_zoom, 1.25)
        dlg.zoom_in()
        self.assertEqual(dlg._current_zoom, 1.50)

        # Zoom Out
        dlg.zoom_out()
        self.assertEqual(dlg._current_zoom, 1.25)

        # Zoom Reset
        dlg.zoom_reset()
        self.assertEqual(dlg._current_zoom, 1.0)

        # Limite mínimo
        for _ in range(10):
            dlg.zoom_out()
        self.assertGreaterEqual(dlg._current_zoom, 0.25)

        # Limite máximo
        for _ in range(20):
            dlg.zoom_in()
        self.assertLessEqual(dlg._current_zoom, 4.0)

    def test_lightbox_non_existent_image_graceful(self):
        """Valida que imagem inexistente não lança exceção não tratada."""
        dlg = ImageLightboxDialog(image_path="caminho_inexistente.png")
        self.assertEqual(dlg._current_zoom, 1.0)


if __name__ == "__main__":
    unittest.main()
