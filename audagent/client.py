import atexit
import logging
import multiprocessing
import multiprocessing.synchronize
import os
import signal
import time
import uuid
from http.client import responses
from typing import Any, Optional, Type

from audagent.enums import CommandAction
from audagent.event_processor import EventProcessor
from audagent.hooks.base import BaseHook, HookCallBackProto
from audagent.hooks.models import HookEvent
from audagent.models import Command, CommandResponse

logger = logging.getLogger(__name__)
class AudagentClient(HookCallBackProto):
    def __init__(self) -> None:
        """
        _process: The multiprocessing.Process instance for the audagent process.
        _running: A boolean flag indicating if the audagent process is running.
        _initialized_event: A primitive (multiprocessing.Event) used to signal when the audagent process has initialized.
        _client_fd: The client end (receiver process) of the multiprocessing.Pipe for sending commands to the audagent process.
        _audagent_fd: The server end (sender process) of the multiprocessing.Pipe for the audagent process to receive commands.
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

    async def on_hook_callback(self, hook: BaseHook, event: HookEvent) -> None:
        logger.debug(f"Hook callback received: {event.event_type}")
        self.send_command(CommandAction.EVENT, event.model_dump())

    def on_hook_callback_sync(self, hook: BaseHook, event: HookEvent) -> None:
        logger.debug(f"Hook callback received: {event.event_type}")
        self.send_command(CommandAction.EVENT, event.model_dump())

    def send_command(self, action: CommandAction, params: Optional[dict[str, Any]] = None) -> str:
        if not self._running:
            raise RuntimeError("Audagent process is not running")
        cmd = Command.from_dict(self._execution_id, action, params) # Create Command instance with the Command model
        self._write_command(cmd)
        return cmd.callback_id

    def send_command_wait(self, action: CommandAction, params: Optional[dict[str, Any]] = None, timeout: float = 5.0) -> Optional[CommandResponse]:
        if not self._running:
            raise RuntimeError("Audagent process is not running")
        cmd = Command.from_dict(self._execution_id, action, params) # Create Command instance with the Command model
        self._write_command(cmd)
        # Wait for response
        start_time = time.time()
        while True:
            try:
                response = self._read_response(timeout) # always returns CommandResponse or None or raises TimeoutError
                if response:
                    if response.callback_id == cmd.callback_id:
                        logger.debug(f"Received response for command {cmd.callback_id}: {response}")
                        return response
                    else:
                        logger.debug(f"Ignoring response for different command {response.callback_id}")
                        continue
                else:
                    logger.debug("No response received yet, continuing to wait...")
                    return None
            except TimeoutError:
                logger.debug(f"Timeout waiting for response to {action}")

    def _start_audagent(self)           -> None:
        if self._process is not None and self._process.is_alive():
            logger.warning("Audagent process is already running")
            return
        self._process = multiprocessing.Process(target=self._run_audagent_process, args=(self._audagent_fd,), daemon=True)
        self._process.start()
        # Wait for initialization
        if not self._initialized_event.wait(timeout=10.0):
            raise RuntimeError("Timeout waiting for audagent process to initialize")
        self._running = True
        logger.info(f"Audagent process started with PID {self._process.pid}")