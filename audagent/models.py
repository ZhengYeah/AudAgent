"""
Data models and data validation in IPC communication using Pydantic.
"""
import time
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field

from audagent.enums import CommandAction


class RemoveNoneBaseModel(BaseModel):
    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        This Overrides the default model dump method to exclude None values
        """
        return super().model_dump(exclude_none=True)

class Command(RemoveNoneBaseModel):
    """
    Command class for IPC communication
    Attributes:
        action (str): The action to be performed.
        params (dict[str, Any]): Parameters for the action.
        callback_id (str): Unique identifier for the callback.
        execution_id (str): Identifier for the execution context.
        timestamp (float): Time when the command was created.
    Methods:
        to_dict(): Converts the Command instance to a dictionary.
        from_dict(): Creates a Command instance from a dictionary.
    """
    action: CommandAction
    params: dict[str, Any] = Field(default_factory=dict)
    callback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    timestamp: float = Field(default_factory=time.time)

    def __str__(self) -> str:
        return f"Command({self.action}, params={self.params}, callback_id={self.callback_id})"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, execution_id: str, action: CommandAction, params: Optional[dict[str, Any]] = None) -> "Command":
        """
        Create a Command instance from a given dictionary.
        """
        return cls(
            execution_id=execution_id,
            action=action,
            params=params or {}
        )

class CommandResponse(RemoveNoneBaseModel):
    """
    Response class for IPC communication
    Attributes:
        success (bool): Indicates if the response was successful.
        data (Any): Data returned from the command execution.
        error (Optional[str]): Error message if the command failed.
        callback_id (Optional[str]): Identifier for the callback.
        timestamp (float): Time when the response was created.
    Methods:
        to_dict(): Converts the CommandResponse instance to a dictionary.
        from_dict(): Creates a CommandResponse instance from a dictionary.
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    callback_id: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

    def __str__(self) -> str:
        return f"Response({self.model_dump()})"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommandResponse":
        """
        Create a CommandResponse instance from a given dictionary.
        """
        return cls(**data)
