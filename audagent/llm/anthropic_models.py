from typing import Any

from presidio_analyzer import AnalyzerEngine

from audagent.auditing.checker import RuntimeChecker
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

    def extract_graph_structure(self, runtime_checker: RuntimeChecker, **kwargs: Any) -> GraphStructure:
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
                results = analyzer.analyze(text=message.content, entities=[], language="en")
                pii_info = {res.entity_type: message.content[res.start:res.end] for res in results}
                for pii in pii_info.values():
                    # This is data collection stage, so we just add data types to runtime checker (check collection compliance automatically)
                    runtime_checker.add_data_type(pii)
                edge_issues = '; '.join(runtime_checker.issues) if runtime_checker.issues else None
                model_generate_edge = ModelGenerateEdge(prompt=message.content,
                                                        source_node_id=APP_NODE_ID,
                                                        target_node_id=model.node_id,
                                                        violation_info=edge_issues)
                edges.append(model_generate_edge)
            elif isinstance(message, AssistantMessage):
                # May contain both ToolUse and TextContent in this stage
                for content in message.content:
                    analyzer = AnalyzerEngine()
                    if isinstance(content, ToolUse):
                        # convert input dict to string for PII analysis
                        text = ' '.join(f"{key}: {value}" for key, value in content.input.items())
                        results = analyzer.analyze(text=text, entities=[], language="en")
                        pii_info = {res.entity_type: text[res.start:res.end] for res in results}
                        for pii in pii_info.values():
                            # This is data processing stage and involves tool use, so we also need to update the disclosure field
                            runtime_checker.check_collection_con(pii)
                            runtime_checker.update_processing_con(pii)
                            runtime_checker.update_disclosure(pii, content.id)
                        edge_issues = '; '.join(runtime_checker.issues) if runtime_checker.issues else None
                        tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                                      target_node_id=content.name,
                                                      tool_input=content.input,
                                                      tool_name=content.name,
                                                      violation_info=edge_issues)
                        edges.append(tool_call_edge)
                    elif isinstance(content, TextContent):
                        results = analyzer.analyze(text=content.text, entities=[], language="en")
                        pii_info = {res.entity_type: content.text[res.start:res.end] for res in results}
                        for pii in pii_info.values():
                            # This is data processing stage, so we check the collection compliance first, then update processing constraint if allowed
                            runtime_checker.check_collection_con(pii)
                            runtime_checker.update_processing_con(pii)
                        edge_issues = '; '.join(runtime_checker.issues) if runtime_checker.issues else None
                        model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                                source_node_id=self.model,
                                                                target_node_id=APP_NODE_ID,
                                                                violation_info=edge_issues)
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

    def extract_graph_structure(self, runtime_checker: RuntimeChecker, **kwargs: Any) -> GraphStructure:
        edges: list[Edge] = []
        for content in self.content:
            analyzer = AnalyzerEngine()
            if isinstance(content, ToolUse):
                # convert input dict to string for PII analysis
                text = ' '.join(f"{key}: {value}" for key, value in content.input.items())
                results = analyzer.analyze(text=text, entities=[], language="en")
                pii_info = {res.entity_type: text[res.start:res.end] for res in results}
                for pii in pii_info.values():
                    # This is data processing stage and involves tool use, so we also need to update the disclosure field
                    runtime_checker.check_collection_con(pii)
                    runtime_checker.update_processing_con(pii)
                    runtime_checker.update_disclosure(pii, content.id)
                edge_issues = '; '.join(runtime_checker.issues) if runtime_checker.issues else None
                tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                              target_node_id=content.name,
                                              tool_input=content.input,
                                              violation_info=edge_issues)
                edges.append(tool_call_edge)
            elif isinstance(content, TextContent):
                results = analyzer.analyze(text=content.text, entities=[], language="en")
                pii_info = {res.entity_type: content.text[res.start:res.end] for res in results}
                for pii in pii_info.values():
                    # This is data processing stage, so we check the collection compliance first, then update processing constraint if allowed
                    runtime_checker.check_collection_con(pii)
                    runtime_checker.update_processing_con(pii)
                edge_issues = '; '.join(runtime_checker.issues) if runtime_checker.issues else None
                model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                        source_node_id=self.model,
                                                        target_node_id=APP_NODE_ID,
                                                        violation_info=edge_issues)
                edges.append(model_generate_edge)
        return [], edges
