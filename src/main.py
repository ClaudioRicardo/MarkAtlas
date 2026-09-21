"""Ponto de entrada (Entry Point) da aplicação MarkAtlas."""

import logging
import sys
from pathlib import Path
from typing import List, Optional

# Garante que a raiz do projeto esteja no sys.path mesmo se executado dentro de src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import default_config
from src.core.style_manager import StyleManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("markatlas")


def run_application(argv: Optional[List[str]] = None) -> int:
    """Inicializa e executa a aplicação GTK MarkAtlas."""
    if argv is None:
        argv = sys.argv

    logger.info("Iniciando MarkAtlas v%s...", default_config.version)

    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, Gio
        from src.views.main_window import MainWindow
    except (ImportError, ValueError) as e:
        logger.error(f"Falha ao carregar PyGObject / GTK: {e}")
        logger.info("Certifique-se de que as dependências do GTK 3 estão instaladas no ambiente.")
        return 1

    class MarkAtlasApp(Gtk.Application):
        def __init__(self) -> None:
            super().__init__(
                application_id=default_config.app_id,
                flags=Gio.ApplicationFlags.FLAGS_NONE,
            )
            self.window: Optional[MainWindow] = None

        def do_activate(self) -> None:
            # Carrega e aplica o tema inicial configurado (Dark por padrão)
            StyleManager.apply_theme(default_config.theme)

            # Instancia e exibe a janela principal
            if not self.window:
                self.window = MainWindow(app=self, title=default_config.app_name)
            self.window.show_all()
            self.window.present()

        def do_startup(self) -> None:
            Gtk.Application.do_startup(self)

    app = MarkAtlasApp()
    return app.run(argv)


if __name__ == "__main__":
    sys.exit(run_application(sys.argv))
