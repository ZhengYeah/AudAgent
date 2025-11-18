"""
Use this logger format in your modules as follows:
```
setup_logging(logging.DEBUG)
logger = logging.getLogger()
```
You can also use icon representations for log levels if preferred.
"""
import logging

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[37m",     # White
        "INFO": "\033[36m",      # Cyan
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        log_time = self.formatTime(record, "%H:%M:%S")
        message = f"{log_time} | {record.levelname:<8} | {record.name} | {record.getMessage()}"
        return f"{color}{message}{self.RESET}"

def setup_logging(level=logging.DEBUG) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Remove any existing handlers (to avoid duplicates)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter())
    root_logger.addHandler(handler)
    # Disable noisy loggers
    for noisy_logger_name in ["presidio"]:
        noisy_logger = logging.getLogger(noisy_logger_name)
        noisy_logger.setLevel(logging.ERROR)
