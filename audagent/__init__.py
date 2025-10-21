import os
import sys
from multiprocessing import current_process

from audagent.core import initialize


def _is_direct_execution() -> bool:
    """
    Whether the name (or path) of the currently running script ends with "audagent".
    If True, it indicates that Audagent package is being executed directly.
    """
    return sys.argv[0].endswith("audagent")

def _safe_to_start() -> bool:
    """
    Conditions:
    - Must be in the main process.
    - Must not be called from a spawned subprocess.
    - Must not be running in a pytest environment.
    - Must not be directly executing the "audagent" package
    """
    return current_process().name == "MainProcess" \
        and not hasattr(sys, '_called_from_spawn') \
        and "PYTEST_VERSION" not in os.environ \
        and not _is_direct_execution()

if _safe_to_start():
    initialize()
