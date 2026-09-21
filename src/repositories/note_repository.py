"""Repositório de Notas Markdown no sistema de arquivos local."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import frontmatter
except ImportError:
    frontmatter = None  # type: ignore

from src.models.note import Note
from src.repositories.base import NoteRepositoryInterface
from src.core.exceptions import NoteNotFoundError, InvalidFrontmatterError

logger = logging.getLogger(__name__)


class MarkdownNoteRepository(NoteRepositoryInterface):
    """Persistência e recuperação de notas Markdown (.md) em disco com Frontmatter."""

    TAG_PATTERN = re.compile(r"(?<!\S)#([a-zA-Z0-9_\-\/]+)")
    FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.DOTALL)

    def __init__(self, base_directory: Optional[str] = None) -> None:
        self.base_directory = Path(base_directory).resolve() if base_directory else None

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute() and self.base_directory:
            p = self.base_directory / p
        return p.resolve()

    def get_by_path(self, path: str) -> Optional[Note]:
        """Lê um arquivo Markdown do disco e instancia um objeto Note."""
        file_path = self._resolve_path(path)
        if not file_path.exists() or not file_path.is_file():
            logger.warning(f"Nota não encontrada no caminho: {file_path}")
            return None

        try:
            content_text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Erro ao ler arquivo {file_path}: {e}")
            return None

        metadata, body = self._parse_frontmatter(content_text)
        tags = self.extract_tags(metadata, body)
        title = self._resolve_title(metadata, body, file_path)

        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        updated_at = datetime.fromtimestamp(stat.st_mtime)

        return Note(
            path=str(file_path),
            title=title,
            content=body,
            metadata=metadata,
            tags=list(tags),
            created_at=created_at,
            updated_at=updated_at,
            is_dirty=False,
        )

    def save(self, note: Note) -> bool:
        """Salva a nota no disco, serializando metadados Frontmatter se houver."""
        file_path = self._resolve_path(note.path)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            full_text = self._serialize_frontmatter(note.metadata, note.content)

            file_path.write_text(full_text, encoding="utf-8")
            note.is_dirty = False
            note.updated_at = datetime.now()
            logger.info(f"Nota salva com sucesso: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Falha ao salvar nota {file_path}: {e}")
            return False

    def delete(self, path: str) -> bool:
        """Remove um arquivo Markdown do disco."""
        file_path = self._resolve_path(path)
        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            logger.info(f"Nota excluída com sucesso: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Falha ao excluir nota {file_path}: {e}")
            return False

    def list_all(self) -> List[Note]:
        """Lista todas as notas no diretório base se configurado."""
        if not self.base_directory or not self.base_directory.exists():
            return []

        notes: List[Note] = []
        for file_path in self.base_directory.rglob("*.md"):
            if any(part.startswith(".") for part in file_path.parts):
                continue
            note = self.get_by_path(str(file_path))
            if note:
                notes.append(note)
        return notes

    def exists(self, path: str) -> bool:
        """Verifica se o arquivo de nota existe no caminho."""
        return self._resolve_path(path).exists()

    def _parse_frontmatter(self, content_text: str) -> Tuple[Dict[str, Any], str]:
        """Extrai dicionário de metadados e corpo do texto."""
        if frontmatter is not None:
            try:
                parsed = frontmatter.loads(content_text)
                return dict(parsed.metadata), parsed.content
            except Exception as e:
                logger.debug(f"Falha no parser frontmatter externo: {e}")

        # Parser YAML embutido resiliente
        match = self.FRONTMATTER_PATTERN.match(content_text)
        if not match:
            return {}, content_text

        raw_yaml, body = match.group(1), match.group(2)
        metadata: Dict[str, Any] = {}
        current_key: Optional[str] = None

        for line in raw_yaml.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            if line.startswith("  - ") or line.startswith("- "):
                val = line.lstrip(" -").strip().strip("'\"")
                if current_key and isinstance(metadata.get(current_key), list):
                    metadata[current_key].append(val)
            elif ":" in line_str:
                key, val = line_str.split(":", 1)
                key = key.strip()
                val = val.strip()
                if not val:
                    metadata[key] = []
                    current_key = key
                elif val.startswith("[") and val.endswith("]"):
                    items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
                    metadata[key] = items
                    current_key = None
                else:
                    metadata[key] = val.strip("'\"")
                    current_key = None
            else:
                current_key = None

        return metadata, body

    def _serialize_frontmatter(self, metadata: Dict[str, Any], content: str) -> str:
        """Serializa metadados e corpo em formato Markdown com cabeçalho YAML."""
        if not metadata:
            return content

        if frontmatter is not None:
            try:
                post = frontmatter.Post(content, **metadata)
                return frontmatter.dumps(post)
            except Exception as e:
                logger.debug(f"Falha no serializer frontmatter externo: {e}")

        # Serializer embutido
        yaml_lines = ["---"]
        for k, v in metadata.items():
            if isinstance(v, list):
                yaml_lines.append(f"{k}:")
                for item in v:
                    yaml_lines.append(f"  - {item}")
            else:
                yaml_lines.append(f"{k}: {v}")
        yaml_lines.append("---")
        yaml_lines.append("")
        if content:
            yaml_lines.append(content)
        return "\n".join(yaml_lines)

    def extract_tags(self, metadata: Dict[str, Any], body: str) -> List[str]:
        """Extrai tags do frontmatter YAML e do corpo do texto (#tags)."""
        tags_set: Set[str] = set()

        # 1. Tags no Frontmatter
        fm_tags = metadata.get("tags", [])
        if isinstance(fm_tags, list):
            for t in fm_tags:
                clean = str(t).strip().lstrip("#")
                if clean:
                    tags_set.add(clean)
        elif isinstance(fm_tags, str):
            for t in fm_tags.split(","):
                clean = t.strip().lstrip("#")
                if clean:
                    tags_set.add(clean)

        # 2. Tags no corpo do Markdown (#tag)
        if body:
            matches = self.TAG_PATTERN.findall(body)
            for m in matches:
                clean = m.strip().lstrip("#")
                if clean:
                    tags_set.add(clean)

        return sorted(list(tags_set))

    def _resolve_title(self, metadata: Dict[str, Any], body: str, file_path: Path) -> str:
        """Resolve o título da nota a partir de Frontmatter, H1 ou nome do arquivo."""
        # 1. Título explícito no Frontmatter
        if "title" in metadata and metadata["title"]:
            return str(metadata["title"]).strip()

        # 2. Primeiro H1 no corpo do texto (# Título)
        if body:
            for line in body.splitlines():
                line_stripped = line.strip()
                if line_stripped.startswith("# ") and not line_stripped.startswith("##"):
                    return line_stripped[2:].strip()

        # 3. Nome do arquivo sem extensão
        return file_path.stem
