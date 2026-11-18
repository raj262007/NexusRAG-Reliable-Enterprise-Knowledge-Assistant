import logging
import sys
from pathlib import Path

_LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOGS_DIR / "nexusrag.log"


def setup_logger(name: str = "nexusrag", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass

    return logger


logger = setup_logger()
