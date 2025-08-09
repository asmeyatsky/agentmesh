from loguru import logger
import sys


def setup_logging():
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level="INFO")
    logger.add("file.log", rotation="10 MB", level="DEBUG")
