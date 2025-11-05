"""
class PolicyChecking: Privacy policy derived from execution trace analysis.
class PolicyTarget: Target privacy policy for comparison.
"""
from typing import Optional

from pydantic import BaseModel, constr, Field

class PolicyChecking(BaseModel):
    data_type: str
    collection: Optional[constr(pattern="^(direct|indirect)$")]
    processing: Optional[constr(pattern="^(relevant|irrelevant)$")]
    disclosure: Optional[str]
    retention: float = 0.0

class PolicyTarget(BaseModel):
    data_type: str
    collection: constr(pattern="^(direct|indirect)$")
    processing: constr(pattern="^(relevant|irrelevant)$")
    disclosure: str
    retention: Optional[float]
