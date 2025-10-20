import os
import sys
from multiprocessing import current_process

from audagent.core import initialize


def _is_direct_execution() -> bool:
    """
    Check if the module is being executed directly.
    This is determined by checking if the script name ends with "audagent".
    """
    return sys.argv[0].endswith("audagen