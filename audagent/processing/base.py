from abc import ABC, abstractmethod
from typing import Any, Optional

from audagent.enums import HookEventType


class BaseProcessor(ABC):
    def __init__(self) -> None:
        self._supported_events: list[HookEventType] = []

    @property
    def supported_events(self) -> list[HookEventType]:
        return self._supported_events

    @abstractmethod
    async def process(self, event_type: HookEventType, data: dict[str, Any]) -> Optional[Any]: ...

    def can_handle(self, event_type: HookEventType) -> bool:
        return event_type in self._supported_events