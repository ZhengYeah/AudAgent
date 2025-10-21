from typing import Any, Optional

from audagent.graph.consts import APP_NODE_ID
from audagent.graph.enums import HttpModel
from audagent.graph.models import (Edge, GraphExtractor, GraphStructure, LLMNode, ModelGenerateEdge, Node,
                                     ToolCallEdge, ToolNode, graph_extractor_fm)
from audagent.llm.models import AssistantMessage, SystemMessage, TextContent, Tool, ToolUse, UserMessage


@graph_extractor_fm.flavor(HttpModel.ANTHROPIC_REQUEST)
class AnthropicRequestModel(GraphExtractor):
    messages: list[UserMessage | AssistantMessage | SystemMessage]
    model: str
    tools: list[Tool] = []

    def extract_graph_structure(self, **kwargs: Any) -> GraphStructure:
        """
        self.model: Model name
        self.tools: List of Tools
        self.messages: List of messages
        """
        nodes: list[Node] = []
        edges: list[Edge] = []
        model: LLMNode = LLMNode(node_id=self.model)
        nodes.append(model)
        for tool in self.tools:
            tool_node = ToolNode(node_id=tool.name, tool_description=tool.description)
            nodes.append(tool_node)
        # Parse all messages, worst case we'll have duplicate edges but that's fine
        for message in self.messages:
            if isinstance(message, UserMessage):
                model_generate_edge = ModelGenerateEdge(prompt=message.content,
                                                        source_node_id=APP_NODE_ID,
                                                        target_node_id=model.node_id)
                edges.append(model_generate_edge)
            elif isinstance(message, AssistantMessage):
                # May contain both ToolUse and TextContent
                for content in message.content:
                    if isinstance(content, ToolUse):
                        tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                                      target_node_id=content.name,
                                                      tool_input=content.input,
                                                      tool_name=content.name)
                        edges.append(tool_call_edge)
                    elif isinstance(content, TextContent):
                        model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                                source_node_id=self.model,
                                                                target_node_id=APP_NODE_ID)
                        edges.append(model_generate_edge)
        return nodes, edges

@graph_extractor_fm.flavor(HttpModel.ANTHROPIC_RESPONSE)
class AnthropicResponseModel(GraphExtractor):
    id: str
    type: str
    role: str
    model: str
    content: list[TextContent | ToolUse]
    stop_reason: Optional[str]

    def extract_graph_structure(self, **kwargs: Any) -> GraphStructure:
        edges: list[Edge] = []
        for content in self.content:
            if isinstance(content, ToolUse):
                tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                              target_node_id=content.name,
                                              tool_input=content.input)
                edges.append(tool_call_edge)
            elif isinstance(content, TextContent):
                model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                        source_node_id=self.model,
                                                        target_node_id=APP_NODE_ID)
                edges.append(model_generate_edge)
        return [], edges
