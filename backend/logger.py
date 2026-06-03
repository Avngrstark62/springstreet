import logging


def _configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name)


def log_error(logger: logging.Logger, message: str, exc: Exception) -> None:
    root_cause = getattr(exc, "orig", exc)
    logger.error("%s: %s", message, root_cause)
