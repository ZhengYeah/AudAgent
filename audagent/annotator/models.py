from typing import Any

from pydantic import BaseModel


class TextToPresidio(BaseModel):
    direction: tuple[str, str]
    data: list[str]
    timestamp: float
