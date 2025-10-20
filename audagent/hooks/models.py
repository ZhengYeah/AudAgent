from datetime import datetime
from typing import Any

from audagent.enums import HookEventType
from audagent.models import RemoveNoneBaseModel


class HookEvent(RemoveNoneBaseModel):
    event_type: HookEventType
    data: dict[str, Any]
    timestamp: datetime = datetime.now()
