"""Exceções de domínio e erros customizados do MarkAtlas."""


class MarkAtlasError(Exception):
    """Exceção base para todos os erros do MarkAtlas."""
    pass


class NoteError(MarkAtlasError):
    """Exceção base para erros relacionados a Notas."""
    pass


class NoteNotFoundError(NoteError):
    """Lançada quando uma nota solicitada não é encontrada."""
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Nota não encontrada no caminho: {path}")


class InvalidFrontmatterError(NoteError):
    """Lançada quando os metadados YAML (frontmatter) são inválidos."""
    def __init__(self, path: str, reason: str = ""):
        self.path = path
        self.reason = reason
        msg = f"Frontmatter inválido na nota '{path}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class VaultError(MarkAtlasError):
    """Exceção base para erros relacionados ao Vault (Cofre)."""
    pass


class VaultNotFoundError(VaultError):
    """Lançada quando um diretório de Vault não existe ou não é acessível."""
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Vault não encontrado no caminho: {path}")


class StyleError(MarkAtlasError):
    """Lançada quando ocorre falha no carregamento ou aplicação de estilos CSS."""
    pass


class RepositoryError(MarkAtlasError):
    """Lançada quando ocorre erro na camada de persistência de dados."""
    pass
