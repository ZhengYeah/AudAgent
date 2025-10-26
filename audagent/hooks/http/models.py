from typing import Any, Optional

from pydantic import BaseModel


class HttpRequestData(BaseModel):
    method: str
    url: str
    headers: dict[str, str]
    body: Optional[str] = None

class HttpResponseData(BaseModel):
    status_code: int
    headers: dict[str, str]
    body: Optional[str] = None
    request: dict[str, Any] = {}
