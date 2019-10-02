""" enable logging

"""
import os
import logging
import logging.config
from pathlib import Path


cur_dir = Path(__file__).resolve().parent
root_dir = cur_dir.parent
log_dir = root_dir / "log"
log_file = log_dir / "pproxy.log"
log_level = os.environ.get("LOG_LEVEL", "DEBUG")

LOG_CFG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(module)s:%(lineno)d %(process)d [%(threadName)s]: %(message)s"
        },
        "simple": {"format": "%(asctime)s %(levelname)s %(message)s"},
    },
    "handlers": {
        "logfile": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_file),
            "level": log_level,
            "when": "midnight",
            "interval": 1,
            "backupCount": 0,
            "delay": True,
            "formatter": "verbose",
        },
        "console": {
            "level": "WARN",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {"handlers": ["logfile", "console"], "level": log_level, "propagate": True}
    },
}

logging.config.dictConfig(LOG_CFG)


if __name__ == "__main__":
    from .server import main

    logging.info("\n ==== pproxy start ==== \n")
    main()
