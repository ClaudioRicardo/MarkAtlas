"""Entry point principal do MarkAtlas na raiz do projeto."""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.main import run_application

if __name__ == "__main__":
    sys.exit(run_application(sys.argv))
