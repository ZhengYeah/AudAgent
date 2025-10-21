"""
Base class for hooks and callback handler protocol.
"""
from abc import ABC, abstractmethod
from typing import Any, Protocol

class BaseHook(ABC):
    """
    Attributes:
    - callback_handler: An instance implementing HookCallBackProto to handle hook events.
    - hooked: A boolean indicating whether the hook has been applied.
    Methods:
    - apply_hook: Abstract method to apply the hook.
    - should_intercept: Abstract method to determine if an event should be intercepted.
    """
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
