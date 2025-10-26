from abc import abstractmethod
from typing import Any, Optional

from pydantic import BaseModel

from audagent.hooks.base import BaseHook, HookCallBackProto


class HttpInterceptRule(BaseModel):
    host: str
    port: Optional[int] = None

class HttpInterceptHook(BaseHook):
    def __init__(self, callback_handler: HookCallBackProto) -> None:
        super().__init__(callback_handler)
        self._intercept_rule: list[HttpInterceptRule] = []

    def add_intercept_rule(self, host: str, port: Optional[int] = None) -> None:
        rule = HttpInterceptRule(host=host, port=port)
        self._intercept_rule.append(rule)

    def should_intercept(self, host: str, port: Optional[int] = None, path: str = "/", scheme: str = "https", **kwargs: Any) -> bool:
        for rule in self._intercept_rule:
            if rule.host == host and (rule.port is None or rule.port == port):
                return True
        return False

    # Normalize requests and responses to a common format if needed
    @abstractmethod
    def _normalize_request(self, *args: Any, **kwargs: Any) -> Any: ...

    @abstractmethod
    def _normalize_response_sync(self, *args: Any, **kwargs: Any) -> Any: ...
