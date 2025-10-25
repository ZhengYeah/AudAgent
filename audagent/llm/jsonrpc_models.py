from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field

from audagent.graph.consts import APP_NODE_ID
from audagent.graph.enums import HttpModel
from audagent.graph.models import (Edge, GraphExtractor, GraphStructure, McpCallEdge, MCPMethodType, MCPServerNode, Node, ToolCallEdge, ToolNode, graph_extractor_fm)
from audagent.hooks.http.models import HttpRequestData, HttpResponseData


class ContentItem(BaseModel):
    type: str
    text: str

class InputSchema(BaseModel):
    properties: dict[str, Any]
    required: list[str] = []
    title: str
    type: str = "object"

class Tool(BaseModel):
    name: str
    description: str
    inputSchema: InputSchema

class ToolListResult(BaseModel):
    tools: list[Tool]

class ToolCallResult(BaseModel):
    content: list[ContentItem]
    isError: bool

class Params(BaseModel):
    name: str
    arguments: dict[str, Any]

@graph_extractor_fm.flavor(HttpModel.MCP_JSONRPC_REQUEST)
class JSONRPCRequest(GraphExtractor):
    method: MCPMethodType
    params: Optional[Params] = None
    jsonrpc: str
    id: int | str 

    def extract_graph_structure(self, reqres: HTTPRequestData | HTTPResponseData, **kwargs: Any) -> GraphStructure:
        if self.method == MCPMethodType.TOOL_CALL:
            return self._extract_tool_call_graph_structure(reqres)
        elif self.method == MCPMethodType.TOOL_LIST:
            return self._extract_tool_list_graph_structure(reqres)
        else:
            raise ValueError(f"Unsupported method: {self.method}")
    
    def _extract_tool_list_graph_structure(self, reqres: HTTPRequestData | HTTPResponseData) -> GraphStructure:
        nodes: list[Node] = []
        edges: list[Edge] = []

        server_node = MCPServerNode(node_id=reqres.headers.get('host', 'localhost'))
        nodes.append(server_node)
        edge = McpCallEdge(
            source_node_id=APP_NODE_ID,
            target_node_id=server_node.node_id,
            method=self.method
        )
        edges.append(edge)
        return nodes, edges
    
    def _extract_tool_call_graph_structure(self, reqres: HTTPRequestData | HTTPResponseData) -> GraphStructure:
        nodes: list[Node] = []
        edges: list[Edge] = []

        host = reqres.headers.get('host', 'localhost')

        mcp_call_edge = McpCallEdge(
            source_node_id=APP_NODE_ID,
            target_node_id=host,
            method=self.method,
            payload=self.params.model_dump() if self.params else None
        )
        edges.append(mcp_call_edge)

        tool_call_edge = ToolCallEdge(
            source_node_id=host,
            target_node_id=self.params.name if self.params else str(),
            tool_input=self.params.arguments if self.params else {},
            tool_name=self.params.name if self.params else str()
        )

        edges.append(tool_call_edge)

        server_node = MCPServerNode(node_id=host)
        nodes.append(server_node)
        return nodes, edges

@graph_extractor_fm.flavor(HttpModel.MCP_JSONRPC_RESPONSE)
class JSONRPCResponse(GraphExtractor):
    jsonrpc: str
    id: int | str
    result: ToolCallResult | ToolListResult
    request: Optional[JSONRPCRequest] = None

    def extract_graph_structure(self, reqres: HTTPRequestData | HTTPResponseData, **kwargs: Any) -> GraphStructure:
        if isinstance(self.result, ToolCallResult):
            if self.result.isError:
                return ([], [])
            return self._extract_tool_call_graph_structure(reqres)
        elif isinstance(self.result, ToolListResult):
            return self._extract_tool_list_graph_structure(reqres)
        else:
            raise ValueError(f"Unsupported method: {self.method}")
    
    def _extract_tool_list_graph_structure(self, reqres: HTTPRequestData | HTTPResponseData) -> GraphStructure:
        nodes: list[Node] = []
        edges: list[Edge] = []

        host = reqres.headers.get('host', 'localhost')
        server_node = MCPServerNode(node_id=host)
        nodes.append(server_node)

        edge = McpCallEdge(
            source_node_id=server_node.node_id,
            target_node_id=APP_NODE_ID,
            method=MCPMethodType.TOOL_LIST,
            payload=self.result.model_dump()
        )

        edges.append(edge)
        for tool in self.result.tools:  # type: ignore
            tool_node = ToolNode(
                node_id=tool.name,
                tool_description=tool.description,
                host_node=host
            )
            nodes.append(tool_node)

        return nodes, edges
    
    def _extract_tool_call_graph_structure(self, reqres: HTTPRequestData | HTTPResponseData) -> GraphStructure:
        nodes: list[Node] = []
        edges: list[Edge] = []

        server_node = MCPServerNode(node_id=reqres.headers.get('host', 'localhost'))
        nodes.append(server_node)

        edge = McpCallEdge(
            source_node_id=server_node.node_id,
            target_node_id=APP_NODE_ID,
            method=MCPMethodType.TOOL_CALL,
            payload=self.result.model_dump()
        )

        edges.append(edge)
        return nodes, edges