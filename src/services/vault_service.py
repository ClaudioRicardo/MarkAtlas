"""Serviço de gerenciamento de Workspace e Cofres (Vaults)."""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.config import AppConfig, default_config
from src.core.exceptions import VaultNotFoundError
from src.models.note import Note
from src.models.vault import Vault
from src.repositories.base import VaultRepositoryInterface
from src.repositories.vault_repository import FileSystemVaultRepository

logger = logging.getLogger(__name__)


class VaultService:
    """Regras de negócio para abertura, varredura, manipulação de pastas e persistência de Vaults."""

    def __init__(
        self,
        vault_repository: Optional[VaultRepositoryInterface] = None,
        config: Optional[AppConfig] = None,
    ) -> None:
        self.vault_repo = vault_repository or FileSystemVaultRepository()
        self.config = config or default_config
        self.active_vault: Optional[Vault] = None

    def open_vault(self, path: str) -> Vault:
        """
        Abre um diretório local como workspace/cofre ativo, escaneando suas notas.
        
        :param path: Caminho do diretório
        :return: Instância de Vault com notas carregadas
        """
        folder_path = Path(path).resolve()
        if not folder_path.exists() or not folder_path.is_dir():
            raise VaultNotFoundError(f"O diretório selecionado não é válido: {path}")

        vault = Vault(path=str(folder_path), name=folder_path.name)
        self.vault_repo.scan(vault)

        self.active_vault = vault
        self.config.active_vault_path = str(folder_path)

        # Atualiza histórico de cofres recentes
        if str(folder_path) not in self.config.recent_vaults:
            self.config.recent_vaults.insert(0, str(folder_path))
            self.config.recent_vaults = self.config.recent_vaults[:10]

        logger.info(f"Workspace ativo alterado para: {folder_path}")
        return vault

    def get_active_vault(self) -> Optional[Vault]:
        """Retorna o cofre ativo na sessão."""
        return self.active_vault

    def get_vault_tree(self, vault: Optional[Vault] = None) -> Dict[str, Any]:
        """Retorna a estrutura em árvore de arquivos e diretórios do cofre."""
        target_vault = vault or self.active_vault
        if not target_vault:
            return {"name": "Sem Workspace", "path": "", "type": "folder", "children": []}

        return self.vault_repo.get_vault_structure(target_vault)

    def refresh_vault(self, vault: Optional[Vault] = None) -> List[Note]:
        """Re-escaneia o cofre para refletir arquivos criados/modificados externamente."""
        target_vault = vault or self.active_vault
        if not target_vault:
            return []

        return self.vault_repo.scan(target_vault)

    def create_folder(self, parent_path: str, folder_name: str) -> Path:
        """
        Cria uma nova pasta dentro de um diretório pai no workspace.
        
        :param parent_path: Caminho da pasta pai
        :param folder_name: Nome da nova pasta
        :return: Path da pasta criada
        """
        clean_name = folder_name.strip()
        if not clean_name:
            raise ValueError("O nome da pasta não pode ser vazio.")

        target_dir = Path(parent_path).resolve() / clean_name
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Pasta criada com sucesso: {target_dir}")
        return target_dir

    def delete_folder(self, folder_path: str) -> bool:
        """
        Remove uma pasta e todo seu conteúdo recursivamente do workspace.
        Impede a exclusão caso o caminho seja a raiz do workspace ativo.
        
        :param folder_path: Caminho do diretório a ser excluído
        :return: True se excluído com sucesso
        """
        target = Path(folder_path).resolve()
        if not target.exists() or not target.is_dir():
            logger.warning(f"Pasta não encontrada para exclusão: {target}")
            return False

        # Proteção: Impede excluir a pasta raiz do workspace ativo
        if self.active_vault and target == Path(self.active_vault.path).resolve():
            logger.warning("Tentativa bloqueada de excluir a pasta raiz do workspace.")
            return False

        try:
            shutil.rmtree(target)
            logger.info(f"Pasta excluída com sucesso: {target}")
            return True
        except Exception as e:
            logger.error(f"Falha ao excluir pasta {target}: {e}")
            return False

    def rename_folder(self, old_path: str, new_name: str) -> Optional[Path]:
        """
        Renomeia uma pasta no workspace.
        Impede renomear a pasta raiz do workspace ativo diretamente por este método.
        
        :param old_path: Caminho atual da pasta
        :param new_name: Novo nome da pasta
        :return: Path da pasta renomeada ou None em caso de falha
        """
        clean_name = new_name.strip()
        if not clean_name:
            raise ValueError("O novo nome da pasta não pode ser vazio.")

        target = Path(old_path).resolve()
        if not target.exists() or not target.is_dir():
            logger.warning(f"Pasta não encontrada para renomear: {target}")
            return None

        # Proteção: Impede renomear a pasta raiz do workspace
        if self.active_vault and target == Path(self.active_vault.path).resolve():
            logger.warning("Tentativa bloqueada de renomear a pasta raiz do workspace.")
            return None

        new_target = target.parent / clean_name
        if new_target.exists() and new_target != target:
            raise FileExistsError(f"Já existe uma pasta com o nome '{clean_name}'.")

        try:
            target.rename(new_target)
            logger.info(f"Pasta renomeada de {target.name} para {new_target.name}")
            return new_target
        except Exception as e:
            logger.error(f"Falha ao renomear pasta {old_path} para {new_name}: {e}")
            return None
