"""Contratos abstratos (Interfaces) da camada de persistência e acesso a dados."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.models.note import Note
from src.models.vault import Vault


class NoteRepositoryInterface(ABC):
    """Interface abstrata para persistência e recuperação de Notas."""

    @abstractmethod
    def get_by_path(self, path: str) -> Optional[Note]:
        """Recupera uma nota a partir de seu caminho de arquivo."""
        pass

    @abstractmethod
    def save(self, note: Note) -> bool:
        """Salva ou atualiza uma nota no armazenamento persistente."""
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Remove uma nota do armazenamento persistente."""
        pass

    @abstractmethod
    def list_all(self) -> List[Note]:
        """Lista todas as notas disponíveis."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Verifica se uma nota existe no caminho fornecido."""
        pass

    @abstractmethod
    def extract_tags(self, metadata: Dict[str, Any], body: str) -> List[str]:
        """Extrai tags do frontmatter e do corpo do texto."""
        pass


class VaultRepositoryInterface(ABC):
    """Interface abstrata para operações e varredura de diretórios de Vault."""

    @abstractmethod
    def scan(self, vault: Vault) -> List[Note]:
        """Varre o diretório do cofre e carrega todas as notas Markdown encontradas."""
        pass

    @abstractmethod
    def get_vault_structure(self, vault: Vault) -> Dict[str, Any]:
        """Retorna a árvore hierárquica de arquivos e diretórios do Vault."""
        pass
