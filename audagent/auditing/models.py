"""
class PolicyChecking: Privacy policy derived from execution trace analysis.
class PolicyTarget: Target privacy policy for comparison.
"""
from typing import Optional
import time

from pydantic import BaseModel, constr, Field

class PolicyChecking(BaseModel):
    data_type: str
    collection: Optional[constr(pattern="^(direct|indirect)$")]
    processing: Optional[constr(pattern="^(relevant|irrelevant)$")]
    disclosure: Optional[str]
    retention: float = Field(default_factory=time.time)

class PolicyTarget(BaseModel):
    data_type: str
    prohibited_col: bool = False
    collection: Optional[constr(pattern="^(direct|indirect)$")]
    processing: Optional[constr(pattern="^(relevant|irrelevant)$")]
    disclosure: Optional[str]
    prohibited_dis: bool = False
    retention: Optional[float]
