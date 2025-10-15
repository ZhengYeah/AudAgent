"""
Central event processing module.
"""
import asyncio
import logging
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event
from typing import Optional


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EventProcessor:
    NUM_WORKERS = 1

    def __init__(self):
        self._init_event: Optional[Event] = None
        self._pipe: Optional[Connection] = None
        self._command_queue: Optional[asyncio.Queue] = None
        self._workers: list[asyncio.Task[None]] = []
        self._event_poller: Optional[asyncio.Task[None]] = None

    def start(self, pipe: Connection, init_event: Event) -> None:
        self._pipe = pipe
        self._init_event = init_event
        try:
            asyncio.run(self._start())
        except Exception as e:
            pass
        logger.info("agentwatch shutdown successfully")

    async def _start(self) -> None:
        self._command_queue = asyncio.Queue()
        for task_num in range(self.NUM_WORKERS):
            self._workers.append(asyncio.create_task(self._consume_events(), name=f"task-{task_num}"))