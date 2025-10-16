from enum import Enum


class CommandAction(Enum):
    """
    Enum for `actions` used in IPC communication.
    """
    EVENT = "event"
    SHUTDOWN = "shutdown"
    PING = "ping"
    ADD_WEBHOOK = "add_webhook"
    VERBOSE = "verbose"

class HookEventType(Enum):
    """
    Events
    """
    HTTP_REQUEST = "http_request"
    HTTP_RESPONSE = "http_response"
