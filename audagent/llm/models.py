from typing import Any

from pydantic import BaseModel

from audagent.llm.enums import Role

class Tool(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

class ToolUse(BaseModel):
    type: str = "tool_use"
    id: str
    name: str
    input: dict[str, Any]

class TextContent(BaseModel):
    type: str = "text"
    text: str

class Message(BaseModel):
    role: Role

class UserMessage(Message):
    role: Role = Role.USER
    content: str

class AssistantMessage(Message):
    role: Role = Role.ASSISTANT
    content: str

class SystemMessage(Message):
    role: Role = Role.SYSTEM
    content: str
