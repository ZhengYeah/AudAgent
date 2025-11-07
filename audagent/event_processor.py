"""
Event Processor for handling HookEvents in the pipe,
including worker management and command processing.
"""
import asyncio
import json
import logging
import os
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event
from typing import Optional

from pydantic import ValidationError

from audagent.enums import CommandAction
from audagent.hooks.models import HookEvent
from audagent.models import Command, CommandResponse
from audagent.pipes import Pipes
from audagent.processing.base import BaseProcessor
from audagent.processing.http_processing import HttpProcessor
from audagent.graph.graph import GraphBuilder
from audagent.visualization.consts import VISUALIZATION_SERVER_PORT
from audagent.webhooks.handler import WebhookHandler
from audagent.webhooks.models import Webhook
from audagent.auditor.checker import RuntimeChecker
from audagent.auditor.format_target_policy import PolicyTargetFormatter, PolicyTarget

logger = logging.getLogger(__name__)


class EventProcessor:
    """
    _init_event: An Event to signal initialization.
    _pipe: The Connection object for IPC.
    _command_queue: An asyncio Queue for commands.
    _workers: A list of asyncio Tasks for worker management.
    _event_poller: An asyncio Task for polling events.
    Methods:
        start: Initializes and starts the event processor.
        register_processors: Registers supported processors.
    """
    NUM_WORKERS = 1

    def __init__(self):
        self._init_event: Optional[Event] = None
        self._processors: list[BaseProcessor] = [] # This version only supports HttpProcessor.
        self._pipe: Optional[Connection] = None
        self._command_queue: Optional[asyncio.Queue[Command]] = None
        self._workers: list[asyncio.Task[None]] = [] # See python asyncio documentation for concepts on Python coroutines and tasks
        self._event_poller: Optional[asyncio.Task[None]] = None
        # Concrete processors
        self._graph_builder = GraphBuilder()
        self._webhook_handler: Optional[WebhookHandler] = None
        self._supported_processors: list[type[BaseProcessor]] = [HttpProcessor]
        # One runtime checker shared across http payloads
        self._runtime_checker = RuntimeChecker(policies=self._load_policies_from_env())

    @staticmethod
    def _load_policies_from_env() -> Optional[list[PolicyTarget]]:
        path_env = os.getenv("AUDAGENT_PRIVACY_POLICIES")
        if not path_env:
            logger.info("AUDAGENT_PRIVACY_POLICIES not set.")
            return None
        try:
            with open(path_env, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Load to PolicyTarget models
            policy_targets = PolicyTargetFormatter(simplified_json=data).format_target_policy()
            logger.debug(f"Loaded privacy policies from '{path_env}'.")
            return policy_targets
        except Exception as e:
            logger.error(f"Failed to read AUDAGENT_POLICIES_PATH '{path_env}': {e}", exc_info=True)
            return None

    def start(self, pipe: Connection, init_event: Event) -> None:
        self._pipe = pipe
        self._init_event = init_event
        try:
            asyncio.run(self._start()) # asyncio.run to start the event loop and run the _start coroutine
        except Exception:
            pass
        logger.info("Audagent shutdown successfully")

    async def _start(self) -> None:
        # Initialize command queue and webhook handler
        self._command_queue = asyncio.Queue()
        self._webhook_handler = WebhookHandler()

        await self._register_processors()

        for task_num in range(self.NUM_WORKERS):
            self._workers.append(asyncio.create_task(self._consume_events(), name=f"task-{task_num}"))

        self._register_visualization_webhook()

        logger.debug("EventProcessor started")
        if self._init_event:
            # An Event object wraps a boolean flag that can be in one of two states: "set" (True) or "not set" (False).
            self._init_event.set()
        self._event_poller = asyncio.create_task(self._poll_events(), name="event-poller")
        await self._event_poller
        logger.debug("Stopped polling events")
        await asyncio.gather(*self._workers)
        logger.info("Audagent workers stopped")

    def _register_visualization_webhook(self) -> None:
        """
        Here is the http port to the FastAPI server for visualization.
        """
        if self._webhook_handler is None:
            return
        webhook = Webhook(url=f"http://localhost:{VISUALIZATION_SERVER_PORT}/api/events",)
        self._webhook_handler.register_webhook(webhook)

    async def _register_processors(self) -> None:
        for processor_cls in self._supported_processors:
            if processor_cls is HttpProcessor:
                self._processors.append(processor_cls(runtime_checker=self._runtime_checker))
            else:
                self._processors.append(processor_cls())
            logger.debug(f"Registered processor: {processor_cls.__name__}")

    async def _consume_events(self) -> None:
        logger.debug(f"Worker {asyncio.current_task().get_name()} started")
        if not self._command_queue or not self._pipe:
            raise RuntimeError("Command queue or pipe not initialized, check whether Audagent started correctly")
        try:
            while True:
                logger.debug("Waiting for command...")
                cmd = await self._command_queue.get()
                logger.debug(f"Consuming command: {cmd.callback_id} with action: {cmd.action}")
                response = await self._on_command(cmd) # Process the command and get the response
                logger.debug(f"Command processed: {cmd.callback_id} with action: {cmd.action}")
                if response:
                    # Send the response back through the pipe; refer to the Pipes class for IPC handling - /audagent/pipes.py
                    await Pipes.write_payload(self._pipe, response)
                    logger.debug(f"Response sent for command: {response}")
                self._command_queue.task_done()
        except asyncio.CancelledError as e:
            logger.debug(f"Worker {asyncio.current_task().get_name()} cancelled: {e}")
        except Exception as e:
            logger.error(f"Error consuming events: {e}", exc_info=True)
            raise

    async def _poll_events(self) -> None:
        if not self._pipe or not self._command_queue:
            raise RuntimeError("Pipe or command queue not initialized, check whether Audagent started correctly")

        logger.debug("Polling for events...")
        try:
            while True:
                try:
                    payload = await Pipes.read_payload(self._pipe) # Read payload from the pipe asynchronously
                    if payload is None:
                        logger.debug("No payload received, continuing...")
                        continue
                    cmd = Command.model_validate_json(payload) # Validate and parse the payload into a Command object
                    self._command_queue.put_nowait(cmd)
                except ValidationError as e:
                    logger.error(f"Error decoding payload to Command: {e}")
        except asyncio.CancelledError as e:
            logger.debug(f"Event polling cancelled: {e}")
        except Exception as e:
            logger.error(f"Error polling events: {e}", exc_info=True)
            raise

    async def _on_command(self, cmd: Command) -> Optional[CommandResponse]:
        logger.debug(f"Received event: {cmd.model_dump_json()}") # Log the received command
        try:
            match cmd.action:
                case CommandAction.EVENT:
                    event = HookEvent.model_validate(cmd.params)
                    return await self._handle_event(cmd.callback_id, event) # Build graph based on the event
                case CommandAction.ADD_WEBHOOK:
                    webhook = Webhook.model_validate(cmd.params)
                    if self._webhook_handler is not None:
                        self._webhook_handler.register_webhook(webhook)
                    return CommandResponse(success=True, callback_id=cmd.callback_id)
                case CommandAction.SHUTDOWN:
                    await self._shutdown()
                    return CommandResponse(success=True, callback_id=cmd.callback_id)
                case CommandAction.PING:
                    return CommandResponse(success=True, callback_id=cmd.callback_id)
                case CommandAction.VERBOSE:
                    self._set_verbose()
                    return CommandResponse(success=True, callback_id=cmd.callback_id)
        except Exception as e:
            logger.error(f"Error in decoding command -- somewhere at: {e}")
        return None

    async def _handle_event(self, callback_id: str, event: HookEvent) -> Optional[CommandResponse]:
        for processor in self._processors:
            if processor.can_handle(event.event_type):
                # Process the event data to extract graph structure, done by http hooks;
                # refer to audagent/processing/http_processing.py for processing details
                structure = await processor.process(event.event_type, event.data) # Refer to HttpProcessor.process()
                if structure:
                    self._graph_builder.append_structure(structure)
                    if self._webhook_handler is not None:
                        # Notify registered webhooks about the updated graph structure
                        await self._webhook_handler.notify_webhooks(self._graph_builder.get_structure())
                break
        return CommandResponse(success=True, callback_id=callback_id)

    async def _shutdown(self) -> None:
        logger.info("Shutting down EventProcessor...")
        if self._webhook_handler:
            await self._webhook_handler.close()
        if self._event_poller:
            self._event_poller.cancel()
            await self._event_poller
        # TODO: Gather or cancel?
        for task in self._workers:
            task.cancel()
            await task
        if self._pipe:
            self._pipe.close()
        logger.info("EventProcessor shutdown complete")

    @staticmethod
    def _set_verbose() -> None:
        logging.basicConfig(level=logging.DEBUG)
        for logger_name, logger_instance in logging.root.manager.loggerDict.items():
            logger_instance.setLevel(logging.DEBUG)
            for handler in logger_instance.handlers:
                handler.setLevel(logging.DEBUG)
