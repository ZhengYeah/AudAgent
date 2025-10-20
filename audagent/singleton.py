"""
The Singleton pattern in Python ensures that a class has only one instance and provides a global point of access to that instance.
This pattern is often used for managing resources like connections, loggers, or configuration settings where a single, shared instance is desired.
"""
import threading
from typing import Any, Callable, Generic, Optional, TypeVar, cast

T = TypeVar("T")

class Singleton(Generic[T]):
    _instances: Optional[T] = None
    _sync_lock = threading.Lock() # Ensures thread-safe singleton initialization
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> T:
        with cls._sync_lock:
            if cls._instances is None or not cls._initialized:
                raise RuntimeError("Singleton instance is not initialized. Call 'initialize' first.")
            return cast(T, cls._instances) # Cast `_instances` to type T for type checking

    @classmethod
    def initialize(cls, factory: Callable[..., T], *args: Any, **kwargs: Any) -> T: # Type of factory: Callable with any args returning T
        with cls._sync_lock:
            if cls._instances is None or not cls._initialized:
                cls._instances = factory(*args, **kwargs)
                cls._initialized = True
            return cast(T, cls._instances)
