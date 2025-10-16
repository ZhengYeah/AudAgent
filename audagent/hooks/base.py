"""
Base class for hooks and callback handler protocol.
TODO:
Hooks:
Callback handlers: Client.
"""
from abc import ABC, abstractmethod
from typing import Any, Protocol

class BaseHook(ABC):
    def __init__(self, callback_handler: "HookCallBackProto") -> None:
        self._callback_handler = callback_handler
        self._hooked = False

    @abstractmethod
    def apply_hook(self) -> None: ...

    @abstractmethod
    def should_intercept(self, *args: Any, **kwargs: Any) -> bool: ...


class HookCallBackProto(Protocol):
    def on_hook_callback_sync(self, hook: BaseHook, event: Any) -> None: ...
    async def on_hook_callback(self, hook: BaseHook, event: Any) -> None: ...
