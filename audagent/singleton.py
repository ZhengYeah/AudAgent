import threading
from typing import Any, Callable, Generic, Optional, TypeVar, cast

T = TypeVar("T")

class SingletonMeta(Generic[T]):
    _instances: Optional[T] = None
    _sync_lock = threading.Lock() # Ensures thread-safe singleton initialization
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> T:
        """

        :return:
        """
        if cls._instances is None:
            raise Exception("Singleton instance not initialized. Call 'initialize' first.")
        return cls._instances
