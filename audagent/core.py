"""
Core (entrance) module for the Audagent package.
Enter to initialize and get the singleton AudagentClient instance.
"""
from audagent.client import AudagentClient
from audagent.singleton import Singleton

# Create a singleton manager for an AudagentClient instance
# Refer to Singleton class in audagent/singleton.py for Type details
_singleton = Singleton[AudagentClient]()

def initialize() -> AudagentClient:
    return _singleton.initialize(AudagentClient)

def get_instance() -> AudagentClient:
    return _singleton.get_instance()

def set_verbose() -> None:
    _singleton.get_instance().set_verbose()
