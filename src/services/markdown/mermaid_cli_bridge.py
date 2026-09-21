"""Ponte de execução para Mermaid CLI (mmdc global ou npx @mermaid-js/mermaid-cli).

Permite renderização fiel de qualquer um dos 30 tipos de diagramas Mermaid oficiais
(incluindo C4, Sankey, Packet, Architecture, Radar, etc.) com cache persistente em disco.

Estratégia de resolução do executável (ordem de preferência):
  1. mmdc global instalado via `npm install -g @mermaid-js/mermaid-cli` (mais estável)
  2. mmdc.cmd (Windows, instalação global)
  3. npx/npx.cmd com pacote previamente instalado em cache local

Nota: o uso de `npx -y` para baixar e executar @mermaid-js/mermaid-cli on-demand
tende a falhar no Windows por um bug de resolução de fontes do FontAwesome dentro do
Puppeteer. A instalação global (`npm install -g`) resolve esse problema de forma definitiva.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

from src.services.markdown.theme_colors import ThemeColors

logger = logging.getLogger(__name__)


class MermaidCliBridge:
    """Invoca o utilitário Mermaid CLI para compilar código Mermaid complexo em SVG."""

    # Timeout (segundos) para cada execução de diagrama
    _RENDER_TIMEOUT_S = 30

    def __init__(self) -> None:
        # Tenta encontrar mmdc instalado globalmente (mais estável que npx on-demand)
        self._mmdc_path = self._find_mmdc_global()
        # npx como fallback (só funciona se a dependência já estiver em cache)
        self._npx_path: Optional[str] = shutil.which("npx") or shutil.which("npx.cmd")
        self._cache_dir = Path(tempfile.gettempdir()) / "markatlas_diagrams"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        if self._mmdc_path:
            logger.debug(f"MermaidCliBridge: usando mmdc global em {self._mmdc_path}")
        elif self._npx_path:
            logger.debug(f"MermaidCliBridge: mmdc não encontrado; usando npx ({self._npx_path})")

    @staticmethod
    def _find_mmdc_global() -> Optional[str]:
        """Tenta localizar o executável mmdc instalado globalmente pelo npm."""
        # Tentativa direta via PATH
        for candidate in ("mmdc", "mmdc.cmd"):
            found = shutil.which(candidate)
            if found:
                return found

        # Tenta prefixo global do npm em casos onde PATH não está atualizado
        try:
            result = subprocess.run(
                ["npm", "root", "-g"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=sys.platform == "win32",
            )
            if result.returncode == 0:
                npm_global_root = result.stdout.strip()
                # Localização típica: <npm_global_root>/.bin/mmdc
                bin_dir = Path(npm_global_root).parent / ".bin"
                for candidate in ("mmdc", "mmdc.cmd"):
                    candidate_path = bin_dir / candidate
                    if candidate_path.exists():
                        return str(candidate_path)
        except Exception:
            pass

        return None

    @property
    def is_available(self) -> bool:
        """Retorna True se mmdc (global) ou npx estão disponíveis no sistema."""
        return bool(self._mmdc_path or self._npx_path)

    @property
    def has_global_mmdc(self) -> bool:
        """Retorna True se o mmdc global está instalado (método preferencial)."""
        return bool(self._mmdc_path)

    def render_to_svg_file(self, code: str, colors: ThemeColors) -> Optional[Path]:
        """Compila o código Mermaid em um arquivo SVG em disco com cache persistente.

        Usa o mmdc global quando disponível (instalação estável com todas as dependências).
        Usa npx como fallback apenas se o cache local já contiver o pacote.

        :param code: Código bruto do bloco Mermaid
        :param colors: Cores do tema ativo para estilização de fundo
        :return: Path absoluto do SVG gerado, ou None se a compilação falhar
        """
        if not code.strip():
            return None

        # Sem executável disponível: fallback imediato
        if not self._mmdc_path and not self._npx_path:
            return None

        # Se só temos npx (sem mmdc global), não tenta executar on-demand com -y
        # pois causa erros de FontAwesome no Windows (bug do Puppeteer)
        if not self._mmdc_path:
            logger.debug(
                "MermaidCliBridge: mmdc não instalado globalmente. "
                "Execute `npm install -g @mermaid-js/mermaid-cli` para ativar a ponte CLI."
            )
            return None

        # Detecta tema pelo background (ThemeColors não expõe is_dark diretamente)
        is_dark = colors.code_bg.lower() not in ("#ffffff", "#f8f9fa", "#f1f5f9", "#e2e8f0", "#eff6ff")
        theme_arg = "dark" if is_dark else "default"

        # Hash determinístico para cache: código + tema
        diag_hash = hashlib.md5((code.strip() + theme_arg).encode("utf-8")).hexdigest()[:16]
        output_svg = self._cache_dir / f"mmd_cli_{diag_hash}.svg"

        # Serve do cache se o SVG já existir
        if output_svg.exists() and output_svg.stat().st_size > 0:
            return output_svg

        input_mmd = self._cache_dir / f"temp_{diag_hash}.mmd"
        try:
            # Normaliza recuo: blocos Mermaid em Markdown frequentemente vêm
            # indentados (ex: com 4 espaços de recuo do code fence), o que
            # confunde o parser do mmdc em algumas situações.
            normalized_code = textwrap.dedent(code).strip()
            input_mmd.write_text(normalized_code, encoding="utf-8")

            cmd = [
                self._mmdc_path,
                "-i", str(input_mmd),
                "-o", str(output_svg),
                "-t", theme_arg,
                "-b", "transparent",
                "--quiet",
            ]

            logger.info(f"Renderizando diagrama Mermaid via CLI: {self._mmdc_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._RENDER_TIMEOUT_S,
                shell=sys.platform == "win32",
                env={**os.environ, "PUPPETEER_SKIP_CHROMIUM_DOWNLOAD": "false"},
            )

            if result.returncode == 0 and output_svg.exists() and output_svg.stat().st_size > 0:
                logger.info(f"Diagrama Mermaid gerado com sucesso: {output_svg.name}")
                return output_svg
            else:
                stderr_short = (result.stderr or "")[:300]
                logger.warning(
                    f"Mermaid CLI retornou código {result.returncode}. "
                    f"Stderr (primeiros 300 chars): {stderr_short}"
                )
                return None

        except subprocess.TimeoutExpired:
            logger.warning(
                f"Tempo limite de {self._RENDER_TIMEOUT_S}s expirado ao compilar diagrama Mermaid"
            )
            return None
        except FileNotFoundError:
            logger.warning(f"Executável mmdc não encontrado: {self._mmdc_path}")
            self._mmdc_path = None
            return None
        except Exception as e:
            logger.warning(f"Falha inesperada ao executar Mermaid CLI: {e}")
            return None
        finally:
            if input_mmd.exists():
                try:
                    input_mmd.unlink()
                except OSError:
                    pass
