from enum import Enum


class WebsocketEvent(str, Enum):
    ADD_NODE = "add_node"
    ADD_EDGE = "add_edge"
