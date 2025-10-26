import uuid
from http import HTTPMethod
from typing import Any, Optional

from pydantic import Field

from audagent.models import RemoveNoneBaseModel
from audagent.webhooks.enums import WebhookEventType


class Webhook(RemoveNoneBaseModel):
    guid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    method: HTTPMethod = HTTPMethod.POST
    headers: dict[str, Any] = {}

    @classmethod
    def create_webhook(cls, url: str, method: HTTPMethod = HTTPMethod.POST, headers: Optional[dict[str, Any]] = None) -> "Webhook":
        return cls(url=url, method=method, headers=headers or {})

    def __str__(self) -> str:
        return f"Webhook[{self.method}, {self.url}]"

class WebhookEvent(RemoveNoneBaseModel):
    event_type: WebhookEventType
    data: list[dict[str, Any]]
    