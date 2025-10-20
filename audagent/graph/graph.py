from audagent.graph.models import AppNode, Edge, GraphStructure, Node


class GraphBuilder:
    def __init__(self) -> None:
        self._nodes: list[Node] = [AppNode()]
        self._edges: list[Edge] = []

    def append_structure(self, structure: GraphStructure) -> None:
        nodes, edges = structure
        self.append_nodes(nodes)
        self.append_edges(edges)

    def append_nodes(self, nodes: list[Node]) -> None:
        for node in nodes:
            if node.node_id not in {n.node_id for n in self._nodes}:
                self._nodes.append(node)

    def append_edges(self, edges: list[Edge]) -> None:
        self._edges.extend(edges)

    def get_structure(self) -> GraphStructure:
        return self._nodes, self._edges
