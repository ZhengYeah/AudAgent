"""
Managing pipes for inter-process communication (IPC) between the client and library processes,
including asynchronous and synchronous read/write commands.
"""
import asyncio
import logging
import time
from multiprocessing.connection import Connection
from typing import Optional

from pydantic import BaseModel, ValidationError

from audagent.models import CommandResponse

logger = logging.getLogger(__name__)

class Pipes:
    """
    Manages pipes for IPC
    Methods:
        read_payload: Read a payload from pipe asynchronously, used by the library process.
        write_payload_sync: Write a command to the command pipe synchronously, used by the client process.
        write_payload: Write a command to the command pipe asynchronously, used by the client process.
        read_response: Read a response from the response pipe synchronously with timeout, used by the client process.
    """
    def __init__(self) -> None:
        pass

    @classmethod
    async def read_payload(cls, reader_fd: Connection) -> Optional[str]:
        loop = asyncio.get_running_loop() # Get the current event loop from asyncio event loop; refer to asyncio documentation
        return await loop.run_in_executor(None, reader_fd.recv) # Use run_in_executor to run the blocking recv call in a separate thread

    @classmethod
    def write_payload_sync(cls, writer_fd: Connection, payload: BaseModel) -> None:
        try:
            writer_fd.send(payload.model_dump_json())
        except Exception as e:
            logger.error(f"Error writing payload: {e}")

    @classmethod
    async def write_payload(cls, writer_fd: Connection, payload: BaseModel) -> None:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, writer_fd.send, payload.model_dump_json())
        except Exception as e:
            logger.error(f"Error writing payload: {e}")

    @classmethod
    def read_response(cls, reader_fd: Connection, timeout: float = 5.0) -> Optional[CommandResponse]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data = reader_fd.recv()
                return CommandResponse.model_validate_json(data)
            except BlockingIOError:
                time.sleep(0.1)
                continue
            except ValidationError as e:
                logger.error(f"Error decoding response payload: {e}")
                return None
        raise TimeoutError("Timeout waiting for response")

