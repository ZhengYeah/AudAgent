"""
Audagent client for managing the process and sending commands via IPC.
"""
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
from audagent.pipes import Pipes

logger = logging.getLogger(__name__)
class AudagentClient(HookCallBackProto):
    def __init__(self) -> None:
        """
        _process: The multiprocessing.Process instance for the audagent process.
        _running: A boolean flag indicating if the audagent process is running.
        _initialized_event: A primitive (multiprocessing.Event) used to signal when the library process is initialized.
        _client_fd: The client file descriptor (the sender process) of the `multiprocessing.Pipe` for sending commands to the pipe.
        _audagent_fd: The server file descriptor (the receiver process) of the `multiprocessing.Pipe` for receiving commands from the pipe.
        _audagent: An instance of the `EventProcessor`, aka the library process.
        _llm_hosts: A list of allowed LLM API hosts for network interception.
        _execution_id: A unique identifier for this client instance, used in commands.
        """
        # Refer to `multiprocessing.Process` documentation for details on process management.
        self._process: Optional[multiprocessing.Process] = None
        self._running = False
        self._initialized_event = multiprocessing.Event()
        self._client_fd, self._audagent_fd = multiprocessing.Pipe() # Two `Connection` objects for IPC.
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

    def _write_command(self, cmd: Command) -> None:
        """Write a command to the pipe."""
        try:
            logger.debug(f"Sending command: {cmd.action} with callback_id: {cmd.callback_id} to file descriptor {self._audagent_fd.fileno()}")
            Pipes.write_payload_sync(self._audagent_fd, cmd) # Write the command to the pipe, refer to the Pipes class
        except Exception as e:
            logger.error(f"Error writing command {cmd.action}: {e}")
            raise

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

    def _start_audagent(self) -> None:
        """
        Initialize the command-response pipes and start the library process.
        """
        if self._running:
            logger.warning("The library process is already running")
            return
        logger.debug("Initializing the library process and command-response pipe...")
        self._process = multiprocessing.Process(
            # TODO: Write the event processer.
            target=self._audagent.start, # The event processor. Start the library process.
            args=(self._client_fd, self._initialized_event),
            daemon=True
        )
        self._process.start()
        self._running = True
        try:
            # The wait() method blocks until the Event flag is true.
            # Wait up to 5 seconds for pipe initialization, refer to event_processor.py.
            self._initialized_event.wait(5)
        except multiprocessing.TimeoutError:
            logger.error("Timeout waiting for audagent to initialize")
        if self._initialized_event.is_set():
            logger.info("Audagent process initialized successfully")

    def _apply_hooks(self, hooks: list[Type[BaseHook]]) -> None:
        for hook in hooks:
            hook_instance = hook(callback_handler=self) # callback handler is this client
            hook_instance.apply_hook()

    def _cleanup(self) -> None:
        """Cleanup the audagent process and pipes"""
        if self._running:
            self.shutdown()

    def shutdown(self) -> None:
        if not self._running:
            logger.warning("Audagent process is not running")
            return
        logger.debug("Shutting down audagent process...")
        try:
            self.send_command(CommandAction.SHUTDOWN) # Send shutdown command to the pipe
            self._audagent_fd.close()
            if self._process:
                self._process.join(5)
            if self._process and self._process.is_alive():
                logger.warning("Audagent process did not shut down gracefully, terminating...")
                self._process.terminate()
            time.sleep(0.5) # Give some time to terminate
            if self._process.is_alive() and self._process.pid:
                logger.error("Audagent process still alive after terminate, killing...")
                os.kill(self._process.pid, signal.SIGKILL)
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            self._running = False
            logger.info("Audagent process shut down successfully")
