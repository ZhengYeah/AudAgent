from datetime import datetime
from typing import Any

from audagent.models import RemoveNoneBaseModel


class HookEvent(RemoveNoneBaseModel):
    event_type: str
    data: dict[str, Any]
    timestamp: datetime = datetime.now()
