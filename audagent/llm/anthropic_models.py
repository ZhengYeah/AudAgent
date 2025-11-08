from typing import Any, Optional

from presidio_analyzer import AnalyzerEngine

from audagent.auditor.checker import RuntimeChecker
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
                # Note that `runtime_checker` may be None if no policies are provided
                try:
                    edge_issues = self.helper_checker_add(runtime_checker, text=message.content) if runtime_checker else None
                except Exception as e:
                    print(f"Error in auditing user message content: {message.content} with error {e}")
                    edge_issues = None
                model_generate_edge = ModelGenerateEdge(prompt=message.content,
                                                        source_node_id=APP_NODE_ID,
                                                        target_node_id=model.node_id,
                                                        violation_info=edge_issues)
                edges.append(model_generate_edge)
            elif isinstance(message, AssistantMessage):
                # May contain both ToolUse and TextContent in this stage
                for content in message.content:
                    if isinstance(content, ToolUse):
                        # convert input dict to string for PII analysis
                        text = ' '.join(f"{value}" for _, value in content.input.items())
                        try:
                            edge_issues = self.helper_checker_switch(runtime_checker, text=text, switch_dis=True, name_dis=content.id) if runtime_checker else None
                        except Exception as e:
                            print(f"Error in auditing tool use content: {text} with error {e}")
                            edge_issues = None
                        tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                                      target_node_id=content.name,
                                                      tool_input=content.input,
                                                      tool_name=content.name,
                                                      violation_info=edge_issues)
                        edges.append(tool_call_edge)
                    elif isinstance(content, TextContent):
                        edge_issues = self.helper_checker_switch(runtime_checker, text=content.text, switch_dis=False) if runtime_checker else None
                        model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                                source_node_id=self.model,
                                                                target_node_id=APP_NODE_ID,
                                                                violation_info=edge_issues)
                        edges.append(model_generate_edge)
        return nodes, edges

    @staticmethod
    def helper_checker_add(runtime_checker: RuntimeChecker, text: str) -> Optional[str]:
        # This is data collection stage, so we just add data types to runtime checker (check collection compliance automatically)
        if not text: return None
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text, entities=[], language="en")
        pii_info = {res.entity_type: text[res.start:res.end] for res in results}
        for data_type, pii in pii_info.items():
            runtime_checker.add_data_name(data_name=pii, data_type=data_type)
        edge_issues = ' '.join(runtime_checker.issues) if runtime_checker.issues else None
        runtime_checker.issues.clear()  # Clear issues after reporting for this edge
        return edge_issues

    @staticmethod
    def helper_checker_switch(runtime_checker: RuntimeChecker, text: str, switch_dis: bool, name_dis: str = None) -> Optional[str]:
        if not text: return None
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text, entities=[], language="en")
        pii_info = {res.entity_type: text[res.start:res.end] for res in results}
        for data_type, pii in pii_info.items():
            runtime_checker.check_collection_allowed(data_type) # Privacy policy often focuses on data types
            runtime_checker.update_processing_con(pii)
            if switch_dis:
                runtime_checker.update_disclosure_con(pii, name_dis)
        edge_issues = ' '.join(runtime_checker.issues) if runtime_checker.issues else None
        runtime_checker.issues.clear()
        return edge_issues


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
            if isinstance(content, ToolUse):
                # convert input dict to string for PII analysis
                text = ' '.join(f"{value}" for _, value in content.input.items())
                try:
                    edge_issues = self.helper_checker_switch(runtime_checker, text=text, switch_dis=True, name_dis=content.id) if runtime_checker else None
                except Exception as e:
                    print(f"Error in auditing tool use content: {text} with error {e}")
                    edge_issues = None
                tool_call_edge = ToolCallEdge(source_node_id=APP_NODE_ID,
                                              target_node_id=content.name,
                                              tool_input=content.input,
                                              violation_info=edge_issues)
                edges.append(tool_call_edge)
            elif isinstance(content, TextContent):
                try:
                    edge_issues = self.helper_checker_switch(runtime_checker, text=content.text, switch_dis=False) if runtime_checker else None
                except Exception as e:
                    print(f"Error in auditing text content: {content.text} with error {e}")
                    edge_issues = None
                model_generate_edge = ModelGenerateEdge(prompt=content.text,
                                                        source_node_id=self.model,
                                                        target_node_id=APP_NODE_ID,
                                                        violation_info=edge_issues)
                edges.append(model_generate_edge)
        return [], edges

    @staticmethod
    def helper_checker_switch(runtime_checker: RuntimeChecker, text: str, switch_dis: bool, name_dis: str = None) -> Optional[str]:
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text, entities=[], language="en")
        pii_info = {res.entity_type: text[res.start:res.end] for res in results}
        for data_type, pii in pii_info.items():
            runtime_checker.check_collection_allowed(data_type)
            runtime_checker.update_processing_con(pii)
            if switch_dis:
                runtime_checker.update_disclosure_con(pii, name_dis)
        edge_issues = ' '.join(runtime_checker.issues) if runtime_checker.issues else None
        runtime_checker.issues.clear()
        return edge_issues
