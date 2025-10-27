from typing import Any

from presidio_analyzer import AnalyzerEngine

from audagent.graph.consts import APP_NODE_ID
from audagent.graph.enums import HttpModel
from audagent.graph.models import (Edge, GraphExtractor, GraphStructure, LLMNode, ModelGenerateEdge, Node, ToolCallEdge, ToolNode, graph_extractor_fm)
from audagent.llm.models import AssistantMessage, SystemMessage, TextContent, Tool, ToolUse, UserMessage


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
                analyzer = AnalyzerEngine()
                results = analyzer.analyze(text=message.content, language="en")
                pii_info = {res.entity_type: (res.start, res.end) for res in results}
                model_generate_edge = ModelGenerateEdge(prompt=message.content,
                                                        source_node_id=APP_NODE_ID,
                                                        target_node_id=model.node_id,
                                                        pii_info=pii_info)
                edges.append(model_generate_edge)
            elif isinstance(message, AssistantMessage):
                # May contain both ToolUse and TextContent in this stage
                for content in message.content:
                    analyzer = AnalyzerEngine()
                    if isinstance(content, ToolUse):
                        results = analyzer.analyze(text=content.input, language="en")
                        pii_info = {res.entity_type: (res.start, res.end) for res in results}
                        tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                                      target_node_id=content.name,
                                                      tool_input=content.input,
                                                      tool_name=content.name,
                                                      pii_info=pii_info)
                        edges.append(tool_call_edge)
                    elif isinstance(content, TextContent):
                        results = analyzer.analyze(text=content.text, language="en")
                        pii_info = {res.entity_type: (res.start, res.end) for res in results}
                        model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                                source_node_id=self.model,
                                                                target_node_id=APP_NODE_ID,
                                                                pii_info=pii_info)
                        edges.append(model_generate_edge)
        return nodes, edges

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
            analyzer = AnalyzerEngine()
            if isinstance(content, ToolUse):
                results = analyzer.analyze(text=content.input, language="en")
                pii_info = {res.entity_type: (res.start, res.end) for res in results}

                tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                              target_node_id=content.name,
                                              tool_input=content.input,
                                              pii_info=pii_info)
                edges.append(tool_call_edge)
            elif isinstance(content, TextContent):
                results = analyzer.analyze(text=content.text, language="en")
                pii_info = {res.entity_type: (res.start, res.end) for res in results}
                model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                        source_node_id=self.model,
                                                        target_node_id=APP_NODE_ID,
                                                        pii_info=pii_info)
                edges.append(model_generate_edge)
        return [], edges
