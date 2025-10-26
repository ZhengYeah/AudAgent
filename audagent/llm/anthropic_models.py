from typing import Any, Optional
from datetime import datetime

from presidio_analyzer import AnalyzerEngine

from audagent.graph.consts import APP_NODE_ID
from audagent.graph.enums import HttpModel
from audagent.graph.models import (Edge, GraphExtractor, GraphStructure, LLMNode, ModelGenerateEdge, Node, ToolCallEdge, ToolNode, graph_extractor_fm)
from audagent.llm.models import AssistantMessage, SystemMessage, TextContent, Tool, ToolUse, UserMessage
from audagent.presidio.models import PresidioOut

@graph_extractor_fm.flavor(HttpModel.ANTHROPIC_REQUEST)
class AnthropicRequestModel(GraphExtractor):
    messages: list[UserMessage | AssistantMessage | SystemMessage]
    model: str
    tools: list[Tool]
    model_config = {"extra": "ignore"} # Ignore validation for extra fields

    def extract_graph_structure(self, **kwargs: Any) -> GraphStructure:
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

    def presidio_annotate(self) -> Optional[PresidioOut]:
        analyzer = AnalyzerEngine()
        full_text = ""
        for message in self.messages:
            if isinstance(message, UserMessage):
                full_text += message.content + " "
            elif isinstance(message, AssistantMessage):
                for content in message.content:
                    if isinstance(content, TextContent):
                        full_text += content.text + " "
                    elif isinstance(content, ToolUse):
                        full_text += f"Tool called: {content.name} with input {content.input} "
            elif isinstance(message, SystemMessage):
                full_text += message.content + " "
        full_text = full_text.strip()
        results = analyzer.analyze(text=full_text, language="en")
        pii_output = [(res.entity_type, res.start, res.end) for res in results]
        return PresidioOut(direction=("app", "llm"), pii_output=pii_output, timestamp=datetime.now().timestamp())

@graph_extractor_fm.flavor(HttpModel.ANTHROPIC_RESPONSE)
class AnthropicResponseModel(GraphExtractor):
    model: str
    id: str
    type: str
    role: str
    content: list[TextContent | ToolUse]
    model_config = {"extra": "ignore"}

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

    def presidio_annotate(self) -> Optional[PresidioOut]:
        analyzer = AnalyzerEngine()
        full_text = ""
        for content in self.content:
            if isinstance(content, TextContent):
                full_text += content.text + " "
            elif isinstance(content, ToolUse):
                full_text += f"Tool called: {content.name} with input {content.input} "
        full_text = full_text.strip()
        results = analyzer.analyze(text=full_text, language="en")
        pii_output = [(res.entity_type, res.start, res.end) for res in results]
        return PresidioOut(direction=("llm", "app"), pii_output=pii_output, timestamp=datetime.now().timestamp())
