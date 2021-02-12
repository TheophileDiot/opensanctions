import sys
import logging
import structlog
from structlog.contextvars import merge_contextvars

# from structlog.contextvars import clear_contextvars, bind_contextvars

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpstream").setLevel(logging.WARNING)


def store_event(logger, log_method, data):
    # level = getattr(logging, data.get("level").upper())
    # if level > logging.INFO:
    #     print("FOO", logger, log_method)
    data.pop("run_id", None)
    data.pop("dataset", None)
    return data


def configure_logging(quiet=False):
    """Configure log levels and structured logging"""
    active_level = logging.ERROR if quiet else logging.DEBUG
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        merge_contextvars,
        store_event,
    ]
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=list(processors),
        processor=structlog.dev.ConsoleRenderer(),
    )

    processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)

    # configuration for structlog based loggers
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(active_level)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(active_level)
    logger.addHandler(handler)
