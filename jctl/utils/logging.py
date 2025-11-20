"""Logging configuration."""

import logging
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(level: str = "INFO", log_file: Path | None = None, debug: bool = False) -> None:
    """Configure logging with Rich output.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        debug: Enable debug mode with tracebacks
    """
    # Convert level string to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure handlers
    handlers: list[logging.Handler] = []

    # Rich handler for console output
    console_handler = RichHandler(
        rich_tracebacks=debug,
        tracebacks_show_locals=debug,
        markup=True,
    )
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # File handler if log file specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG if debug else log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )

    # Reduce verbosity of third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
