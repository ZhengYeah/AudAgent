"""
Event Processor for handling HookEvents in the pipe,
including worker management and command processing.
"""
import asyncio
import logging
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event
from tabnanny import verbose
from typing import Optional

from pydantic import ValidationError

from audagent.enums import CommandAction
from audagent.hooks.models import HookEvent
from audagent.models import Command, CommandResponse
from audagent.pipes import Pipes
from audagent.processing.base import BaseProcessor
from audagent.processing.http_processing import HttpProcessor
from audagent.graph.graph import GraphBuilder
from audagent.webhooks.handler import WebhookHandler
from audagent.webhooks.models import Webhook

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        self._command_queue: Optional[asyncio.Queue] = None
        self._workers: list[asyncio.Task[None]] = [] # See python asyncio documentation for concepts on Python coroutines and tasks
        self._event_poller: Optional[asyncio.Task[None]] = None
        self._graph_builder = GraphBuilder()
        self._webhook_handler: Optional[WebhookHandler] = None
        self._supported_processors: list[type[BaseProcessor]] = [HttpProcessor]

    def start(self, pipe: Connection, init_event: Event) -> None:
        self._pipe = pipe
        self._init_event = init_event
        try:
            asyncio.run(self._start()) # asyncio.run to start the event loop and run the _start coroutine
        except Exception as e:
            pass
        logger.info("Audagent shutdown successfully")

    async def _start(self) -> None:
        self._command_queue = asyncio.Queue()
        await self._register_processors()
        for task_num in range(self.NUM_WORKERS):
            self._workers.append(asyncio.create_task(self._consume_events(), name=f"task-{task_num}"))
        logger.debug("EventProcessor started")
        if self._init_event:
            # An Event object wraps a boolean flag that can be in one of two states: "set" (True) or "not set" (False).
            self._init_event.set()
        self._event_poller = asyncio.create_task(self._poll_events(), name="event-poller")
        await self._event_poller
        logger.debug("Stopped polling events")
        await asyncio.gather(*self._workers)
        logger.info("Audagent workers stopped")

    async def _register_processors(self) -> None:
        for processor in self._supported_processors:
            self._processors.append(processor())
            logger.debug(f"Registered processor: {processor.__name__}")

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
        try:
            while True:
                logger.debug("Polling for events...")
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
            logger.error(f"Error decoding command: {e}")

    async def _handle_event(self, callback_id: str, event: HookEvent) -> Optional[CommandResponse]:
        for processor in self._processors:
            if processor.can_handle(event.event_type):
                # Process the event data to extract graph structure; refer to audagent/processing/http_processing.py for processing details
                structure = await processor.process(event.event_type, event.data)
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

    def _set_verbose(self) -> None:
        logging.basicConfig(level=logging.DEBUG)
        for logger_name, logger_instance in logging.root.manager.loggerDict.items():
            logger_instance.setLevel(logging.DEBUG)
            for handler in logger_instance.handlers:
                handler.setLevel(logging.DEBUG)
