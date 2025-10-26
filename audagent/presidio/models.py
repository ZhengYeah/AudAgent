from typing import Any

from pydantic import BaseModel


class PresidioOut(BaseModel):
    direction: tuple[str, str]
    pii_output: list[tuple[str, int, int]] # List of (entities, start, end) annotations
    timestamp: float
