# app/logger.py

import logging
from app.config import Config


def setup_logger(config: Config) -> logging.Logger:
    logger = logging.getLogger("YourAppLogger")
    logger.setLevel(getattr(logging, config.logging.level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    formatter = logging.Formatter(config.logging.format)
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger