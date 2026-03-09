AudAgent uses inter-process communication (IPC) to track AI agent interactions in real time.
- client (`audagent/client.py`) is the public-facing API that sends commands and receives responses. It serializes commands, writes them to the IPC channel (see `audagent/pipes.py`), and reads back `CommandResponse` objects.
- event_processor (`audagent/event_processor.py`) runs on the worker/library side. It reads incoming command payloads (i.e., actual data or content) from the IPC reader, validates them, and routes each command to the appropriate handler.
- hooks (`audagent/hooks/`) contains pluggable handlers. These hook implementations are invoked by `event_processor` to perform the actual processing for each received command or event.

Interaction flow:
client → send events/commands via pipes → event_processor (receive) → dispatch → hooks (execute) → event_processor → return response → client.