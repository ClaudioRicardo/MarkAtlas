"""Gerenciador de Estilos CSS para PyGObject / GTK."""

import logging
from pathlib import Path
from typing import List, Optional, Union
from src.core.exceptions import StyleError

logger = logging.getLogger(__name__)


class StyleManager:
    """Carrega, injeta e alterna temas CSS modulares no contexto visual do GTK."""

    _loaded_providers: List[object] = []

    @classmethod
    def clear_styles(cls) -> None:
        """Remove todos os provedores CSS previamente adicionados à tela do GTK."""
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk, Gdk
        except (ImportError, ValueError):
            cls._loaded_providers.clear()
            return

        try:
            screen = Gdk.Screen.get_default()
            if screen:
                for provider in cls._loaded_providers:
                    try:
                        Gtk.StyleContext.remove_provider_for_screen(screen, provider)
                    except Exception as err:
                        logger.debug(f"Erro ao remover provider CSS: {err}")
        except Exception as e:
            logger.warning(f"Falha ao limpar provedores CSS: {e}")
        finally:
            cls._loaded_providers.clear()

    @classmethod
    def load_styles(cls, css_paths: List[Union[str, Path]], clear_previous: bool = False) -> bool:
        """
        Carrega uma lista de arquivos CSS e adiciona ao StyleContext global do GTK.
        
        :param css_paths: Lista de caminhos para arquivos .css
        :param clear_previous: Se True, remove os provedores anteriores antes de carregar
        :return: True se todos os estilos foram carregados com sucesso
        """
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk, Gdk
        except (ImportError, ValueError) as e:
            logger.warning(f"PyGObject / GTK 3.0 não disponível para carregamento de estilos: {e}")
            return False

        try:
            screen = Gdk.Screen.get_default()
            if not screen:
                logger.warning("Gdk.Screen padrão não está disponível (ambiente headless ou GTK não inicializado).")
                return False

            if clear_previous:
                cls.clear_styles()

            for path in css_paths:
                file_path = Path(path).resolve()
                if not file_path.exists():
                    logger.warning(f"Arquivo CSS não encontrado: {file_path}")
                    continue

                try:
                    provider = Gtk.CssProvider()
                    provider.load_from_path(str(file_path))

                    Gtk.StyleContext.add_provider_for_screen(
                        screen,
                        provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                    )
                    cls._loaded_providers.append(provider)
                    logger.info(f"Estilo CSS carregado com sucesso: {file_path.name}")
                except Exception as file_err:
                    logger.warning(f"Falha ao carregar estilo CSS '{file_path.name}': {file_err}")

            return True
        except Exception as e:
            raise StyleError(f"Erro ao injetar estilos CSS no GTK: {e}") from e

    @classmethod
    def apply_theme(cls, theme_name: str, config: Optional[object] = None) -> bool:
        """
        Alterna o tema visual da aplicação em tempo de execução.
        
        :param theme_name: 'dark' ou 'light'
        :param config: Objeto AppConfig opcional (usa default_config se omitido)
        :return: True se o tema foi aplicado com sucesso
        """
        from src.core.config import default_config
        target_config = config or default_config

        if theme_name not in ("dark", "light"):
            logger.warning(f"Tema inválido '{theme_name}'. Usando 'dark' como padrão.")
            theme_name = "dark"

        target_config.theme = theme_name

        # Notifica o GTK sobre preferência de tema escuro se aplicável
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
            settings = Gtk.Settings.get_default()
            if settings:
                settings.set_property("gtk-application-prefer-dark-theme", theme_name == "dark")
        except Exception as e:
            logger.debug(f"Não foi possível definir propriedade gtk-application-prefer-dark-theme: {e}")

        # Recarrega os estilos com os novos tokens de tema
        style_sheets = target_config.get_style_sheets(theme=theme_name)
        success = cls.load_styles(style_sheets, clear_previous=True)
        logger.info(f"Tema '{theme_name}' aplicado com sucesso.")
        return success

    @classmethod
    def load_from_string(cls, css_content: str) -> bool:
        """
        Injeta código CSS diretamente a partir de uma string.
        
        :param css_content: Código CSS formatado
        :return: True se aplicado com sucesso
        """
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk, Gdk
        except (ImportError, ValueError) as e:
            logger.warning(f"PyGObject / GTK 3.0 não disponível: {e}")
            return False

        try:
            screen = Gdk.Screen.get_default()
            if not screen:
                return False

            provider = Gtk.CssProvider()
            provider.load_from_data(css_content.encode("utf-8"))

            Gtk.StyleContext.add_provider_for_screen(
                screen,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
            cls._loaded_providers.append(provider)
            return True
        except Exception as e:
            raise StyleError(f"Erro ao injetar CSS customizado: {e}") from e
