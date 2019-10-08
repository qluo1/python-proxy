""" proxy server handle incomming connection


"""

import os
import logging
import logging.config
from pathlib import Path
import argparse
import asyncio

# from subprocess import Popen, PIPE
import uvloop
import toml
from box import Box
from .singleton import SingleInstance
from .handle import Proxy

# using uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

cur_dir = Path(__file__).resolve().parent
root_dir = cur_dir.parent
log_dir = root_dir / "log"
log_file = log_dir / "px.log"
log_level = os.environ.get("LOG_LEVEL", "INFO")

LOG_CFG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(module)s %(lineno)d %(process)d [%(threadName)s]: %(message)s"
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

log = logging.getLogger(__name__)


def main():
    """ """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration file")

    args = parser.parse_args()

    if args.config:

        me = SingleInstance("socketserver")  # noqa
        config = Path(args.config)
        assert config.exists(), f"config file not found: {config}"
        settings = toml.load(str(config.resolve()))

        settings = Box(settings)
        ports = settings.listen_ports
        print(f"listen on {ports}")

        manager = Proxy(settings)
        loop = asyncio.get_event_loop()
        loop.set_debug(True)

        try:
            for port in ports:
                port = int(port)
                loop.run_until_complete(
                    asyncio.start_server(manager.handle_client, "0.0.0.0", port)
                )

                loop.run_forever()

        except KeyboardInterrupt:
            # cleanup
            print("shutting down")
        except RuntimeError as e:
            log.exception(e)
        finally:
            loop.close()
            del me
    else:
        parser.print_usage()


if __name__ == "__main__":
    main()
