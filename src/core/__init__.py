"""Módulo de infraestrutura central do MarkAtlas."""

from src.core.exceptions import (
    MarkAtlasError,
    NoteError,
    NoteNotFoundError,
    InvalidFrontmatterError,
    VaultError,
    VaultNotFoundError,
    StyleError,
    RepositoryError,
)
from src.core.config import AppConfig, default_config
from src.core.events import EventBus, default_event_bus
from src.core.style_manager import StyleManager

__all__ = [
    "MarkAtlasError",
    "NoteError",
    "NoteNotFoundError",
    "InvalidFrontmatterError",
    "VaultError",
    "VaultNotFoundError",
    "StyleError",
    "RepositoryError",
    "AppConfig",
    "default_config",
    "EventBus",
    "default_event_bus",
    "StyleManager",
]
