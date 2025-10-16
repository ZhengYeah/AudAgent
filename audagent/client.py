import atexit
import logging
import multiprocessing
import multiprocessing.synchronize
import os
import signal
import time
import uuid
from typing import Any, Optional, Type

from audagent.event_processor import EventProcessor
from audagent.hooks.base import BaseHook, HookCallBackProto
from audagent.models import Command, CommandResponse

logger = logging.getLogger(__name__)
class AudagentClient(HookCallBackProto):
    def __init__(self) -> None:
        """
        _process: The multiprocessing.Process instance for the audagent process.
        _running: A boolean flag indicating if the audagent process is running.
        _initialized_event: A multiprocessing.Event used to signal when the audagent process has initialized.
        _client_fd: The client end of the multiprocessing.Pipe for sending commands to the audagent process.
        _audagent_fd: The server end of the multiprocessing.Pipe for the audagent process to receive commands.
        _audagent: An instance of the EventProcessor that runs in the audagent process.
        _llm_hosts: A list of allowed LLM API hosts for network interception.
        _execution_id: A unique identifier for this client instance, used in commands.
        """
        self._process: Optional[multiprocessing.Process] = None
        self._running = False
        self._initialized_event = multiprocessing.Event()
        self._client_fd, self._audagent_fd = multiprocessing.Pipe()
        self._audagent = EventProcessor()
        self._llm_hosts = [
            "api.openai.com",
            "api.anthropic.com",
            "api.cohere.ai",
            "api.mistral.ai",
            "api.groq.com",
            "api.together.xyz",
            "localhost",
        ]
        atexit.register(self.cleanup)
        self._execution_id = uuid.uuid4().hex
        self._start_audagent()

    @staticmethod
    def set_verbose() -> None:
        logging.getLogger().setLevel(logging.DEBUG)



    def send_command(self, action: str, params: Optional[dict[str, Any]] = None, timeout: float = 5.0) -> Optional[CommandResponse]:
        if not self._running or not self._client_fd:
            logging.error("Audagent is not running")
            return None

        command = Command.from_dict(
            execution_id=self._execution_id,
            action=action,
            params=params or {}
        )

        logging.debug(f"Sending command: {command}")

        try:
            Pipes.write_payload_sync(self._client_fd, command)
        except Exception as e:
            logging.error(f"Error sending command: {e}")
            return None

        response = Pipes.read_response(self._client_fd, timeout=timeout)
        if response:
            logging.debug(f"Received response: {response}")
        else:
            logging.error("No response received or timeout occurred")

        return response
