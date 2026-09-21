"""Sistema de eventos / Barramento desacoplado (Event Bus) para o MarkAtlas."""

from typing import Any, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], None]


class EventBus:
    """Barramento de eventos síncrono para comunicação desacoplada entre camadas."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Registra um ouvinte para um determinado tipo de evento."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove um ouvinte de um determinado tipo de evento."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def publish(self, event_type: str, data: Any = None) -> None:
        """Publica um evento para todos os ouvintes inscritos."""
        handlers = list(self._subscribers.get(event_type, []))
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Erro ao executar handler para o evento '{event_type}': {e}", exc_info=True)

    def clear(self) -> None:
        """Remove todos os ouvintes registrados."""
        self._subscribers.clear()


# Instância global padrão do barramento de eventos
default_event_bus = EventBus()
