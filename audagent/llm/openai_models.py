import json
from typing import Any, Optional

from pydantic import BaseModel

from audagent.graph.consts import APP_NODE_ID
from audagent.graph.enums import HttpModel
from audagent.graph.models import (Edge, GraphExtractor, GraphStructure, LLMNode, ModelGenerateEdge, Node, ToolCallEdge, ToolNode, graph_extractor_fm)
from audagent.llm.enums import Role
from audagent.llm.models import SystemMessage, UserMessage


class FunctionDetails(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

class Tool(BaseModel):
    type: str
    function: FunctionDetails

class Message(BaseModel):
    role: Role

class ToolMessage(Message):
    role: Role = Role.TOOL
    content: str
    tool_call_id: str

class AssistantMessage(Message):
    role: Role = Role.ASSISTANT
    content: Optional[str]
    tool_calls: list["ToolCall"]

@graph_extractor_fm.flavor(HttpModel.OPENAI_REQUEST)
class OpenAIRequestModel(GraphExtractor):
    messages: list[UserMessage | AssistantMessage | SystemMessage | ToolMessage]
    model: str
    stream: bool
    tools: list[Tool] = []

    def extract_graph_structure(self, **kwargs: Any) -> GraphStructure:
        nodes: list[Node] = []
        edges: list[Edge] = []

        model_node = LLMNode(node_id=self.model)
        nodes.append(model_node)

        for message in self.messages:
            if isinstance(message, ToolMessage):
                pass
                # Not sure I want this, it includes the actual tool call result from the app
                # edges.append(ToolCallEdge(source_node_id=APP_NODE_ID,
                #                           target_node_id=self.model,
                #                           tool_input={"input": message.content}))
            elif isinstance(message, UserMessage):
                edges.append(ModelGenerateEdge(source_node_id=APP_NODE_ID,
                                              target_node_id=self.model,
                                              prompt=message.content,
                                              history_size=len(self.messages)))  # type: ignore
            elif isinstance(message, AssistantMessage):
                if message.content is not None:
                    edges.append(ModelGenerateEdge(source_node_id=self.model,
                                                 target_node_id=APP_NODE_ID,
                                                 prompt=message.content))
        for tool in self.tools:
            tool_node = ToolNode(node_id=tool.function.name, tool_description=tool.function.description)
            nodes.append(tool_node)
        
        return nodes, edges

class ResponseFunctionDetails(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: str
    function: ResponseFunctionDetails

class ResponseMessage(BaseModel):
    role: str
    content: Optional[str]
    tool_calls: list[ToolCall] = []
    refusal: Optional[str]
    
class Choice(BaseModel):
    index: int
    message: ResponseMessage
    logprobs: Optional[str]
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@graph_extractor_fm.flavor(HttpModel.OPENAI_RESPONSE)
class OpenAIResponseModel(GraphExtractor):
    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]

    def extract_graph_structure(self, **kwargs: Any) -> GraphStructure:
        nodes: list[Node] = []
        edges: list[Edge] = []

        for choice in self.choices:
            for tool_call in choice.message.tool_calls:
                edges.append(ToolCallEdge(source_node_id=self.model,
                            target_node_id=APP_NODE_ID, 
                            tool_name=tool_call.function.name,
                            tool_input=json.loads(tool_call.function.arguments))
                            )
                
                edges.append(ToolCallEdge(source_node_id=APP_NODE_ID, 
                                          target_node_id=tool_call.function.name, 
                                          tool_input=json.loads(tool_call.function.arguments)))
            if choice.message.content is not None:
                edges.append(ModelGenerateEdge(source_node_id=self.model,
                                               target_node_id=APP_NODE_ID,
                                               prompt=str(choice.message.content)))

        return nodes, edges


