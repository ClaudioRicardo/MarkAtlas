"""Gerenciamento de configurações e caminhos da aplicação MarkAtlas."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# Constantes para acessibilidade e dimensionamento de fonte
DEFAULT_FONT_SIZE: int = 14
MIN_FONT_SIZE: int = 10
MAX_FONT_SIZE: int = 32
FONT_SIZE_STEP: int = 2


@dataclass
class AppConfig:
    """Configurações gerais da aplicação."""
    app_name: str = "MarkAtlas"
    app_id: str = "org.markatlas.MarkAtlas"
    version: str = "0.1.0"
    theme: str = "dark"  # Padrão: 'dark' (ou 'light')
    font_size: int = DEFAULT_FONT_SIZE
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    recent_vaults: List[str] = field(default_factory=list)
    active_vault_path: Optional[str] = None

    def increase_font_size(self) -> int:
        """Aumenta o tamanho da fonte respeitando o limite máximo."""
        self.font_size = min(self.font_size + FONT_SIZE_STEP, MAX_FONT_SIZE)
        return self.font_size

    def decrease_font_size(self) -> int:
        """Diminui o tamanho da fonte respeitando o limite mínimo."""
        self.font_size = max(self.font_size - FONT_SIZE_STEP, MIN_FONT_SIZE)
        return self.font_size

    def reset_font_size(self) -> int:
        """Restaura o tamanho padrão da fonte."""
        self.font_size = DEFAULT_FONT_SIZE
        return self.font_size

    @property
    def assets_dir(self) -> Path:
        """Diretório de assets da aplicação."""
        return self.project_root / "assets"

    @property
    def styles_dir(self) -> Path:
        """Diretório de estilos CSS modulares."""
        return self.assets_dir / "styles"

    @property
    def icons_dir(self) -> Path:
        """Diretório de ícones da aplicação."""
        return self.assets_dir / "icons"

    def get_style_sheets(self, theme: Optional[str] = None) -> List[Path]:
        """
        Retorna os arquivos CSS modulares na ordem correta de carregamento.
        Inicia pelos tokens de cores do tema selecionado, seguidos pelos estilos de componentes e estrutura.
        """
        selected_theme = theme or self.theme
        token_file = "tokens_light.css" if selected_theme == "light" else "tokens_dark.css"

        order = [token_file, "main.css", "sidebar.css", "editor.css", "components.css"]
        return [self.styles_dir / filename for filename in order if (self.styles_dir / filename).exists()]


# Instância global padrão de configuração
default_config = AppConfig()
