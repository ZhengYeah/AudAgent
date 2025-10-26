"""
Parse Agents' messages and tool uses based on their request and response.
"""
from typing import Any, Optional

from pydantic import BaseModel

from audagent.llm.enums import Role

class Tool(BaseModel):
    name: str
    input_schema: dict[str, Any]
    description: str
    # parameters: dict[str, Any]

class ToolUse(BaseModel):
    type: str = "tool_use"
    id: str
    name: str
    input: dict[str, Any]

class TextContent(BaseModel):
    type: str = "text"
    text: str
    model_config = {"extra": "ignore"}

class Message(BaseModel):
    role: Role

class UserMessage(Message):
    role: Role = Role.USER
    content: str

class AssistantMessage(Message):
    role: Role = Role.ASSISTANT
    content: list[ToolUse | TextContent]

class SystemMessage(Message):
    role: Role = Role.SYSTEM
    content: str
