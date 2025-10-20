from enum import Enum


class WebhookEventType(str, Enum):
    NODES = "nodes"
    EDGES = "edges"
