import time
import uuid
from abc import abstractmethod, ABC
from enum import Enum
from typing import Any, Optional, Type, TypeAlias

from pydantic import BaseModel, Field

from audagent.graph.consts import APP_NODE_ID
from audagent.graph.enums import EdgeType, NodeType
from audagent.utils.flavor_manager import FlavorManager

class GraphExtractor(BaseModel, ABC):
    @abstractmethod
    def extract_graph_structure(self, *args: Any, **kwargs: Any) -> "GraphStructure":
        ...

class Node(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType
    created_at: float = Field(default_factory=lambda: time.time())

class LLMNode(Node):
    node_type: NodeType = NodeType.LLM

class MCPServerNode(Node):
    node_type: NodeType = NodeType.MCP_SERVER

class ToolNode(Node):
    node_type: NodeType = NodeType.TOOL
    tool_description: str
    host_node: Optional[str] = None

class AppNode(Node):
    node_id: str = APP_NODE_ID
    node_type: NodeType = NodeType.APPLICATION

class Edge(BaseModel):
    edge_type: EdgeType
    source_node_id: str
    target_node_id: str
    created_at: float = Field(default_factory=lambda: time.time())

class ModelGenerateEdge(Edge):
    """
    Edge representing a model generation event
    """
    edge_type: EdgeType = EdgeType.MODEL_GENERATE
    prompt: str
    class Config:
        extra = "allow"

class ToolCallEdge(Edge):
    edge_type: EdgeType = EdgeType.TOOL_CALL
    tool_input: dict[str, Any]
    tool_name: Optional[str] = None

class MCPMethodType(str, Enum):
    TOOL_CALL = "tools/call"
    TOOL_LIST = "tools/list"

class McpCallEdge(Edge):
    edge_type: EdgeType = EdgeType.MCP_CALL
    method: MCPMethodType
    payload: Optional[dict[str, Any]] = None

GraphStructure: TypeAlias = tuple[list[Node], list[Edge]]

graph_extractor_fm: FlavorManager[str, Type[GraphExtractor]] = FlavorManager() # Flavor manager for GraphExtractor class
