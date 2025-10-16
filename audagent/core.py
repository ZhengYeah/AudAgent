from audagent.client import AudagentClient
from audagent.singleton import Singleton

_singleton = Singleton[AudagentClient]()

def initialize() -> AudagentClient:
    return _singleton.initialize(AudagentClient)
