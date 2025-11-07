import json
import os
import sys
from multiprocessing import current_process

from audagent.consts import AUDAGENT_INTERNAL
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
    - Must not be running.
    - Must not be running in a pytest environment.
    - Must not be directly executing the "audagent" package
    """
    autostart = os.environ.get("AUDAGENT_AUTOSTART", "1") == "0"
    return current_process().name == "MainProcess" \
        and not hasattr(sys, '_called_from_spawn') \
        and os.environ.get(AUDAGENT_INTERNAL) is None \
        and "PYTEST_VERSION" not in os.environ \
        and not _is_direct_execution() \
        and autostart

def initialize_with_privacy_policy(policies_path: str):
    """
    Initialize the Audagent client with a specified privacy policy.
    - policy: path to the json file
    """
    os.environ["AUDAGENT_PRIVACY_POLICIES"] = policies_path
    initialize()

if _safe_to_start():
    # Controlled by autostart condition; default is not to autostart
    initialize()
