"""
Event Processor for handling HookEvents in the pipe,
including worker management and command processing.
"""
import asyncio
import logging
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EventProcessor:
    """
    _init_event: An Event to signal initialization.
    _pipe: The Connection object for IPC.
    _command_queue: An asyncio Queue for commands.
    _workers: A list of asyncio Tasks for worker management.
    _event_poller: An asyncio Task for polling events.
    """
    NUM_WORKERS = 1

    def __init__(self):
        self._init_event: Optional[Event] = None
        self._pipe: Optional[Connection] = None
        self._command_queue: Optional[asyncio.Queue] = None
        # See python asyncio documentation for concepts on Python coroutines and tasks
        self._workers: list[asyncio.Task[None]] = []
        self._event_poller: Optional[asyncio.Task[None]] = None

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
        for processor in self._