import json
import logging
import os
import sys

import argparse
import hcl2
import structlog

# Pull in the wrapped stdlib logger for use in the module
# If structlog has not been configured, see the following for how the stdlib logger will be wrapped:
# https://www.structlog.org/en/stable/configuration.html
logger = structlog.get_logger()


def main():
    """
    Parse a given HCL file path positional argument and
    emit as native JSON to stdout
    """
    # Configure structured logging
    json_renderer = os.environ.get("JSON_LOG_RENDERER", "False")
    if json_renderer.lower() == "true":
        structlog_log_renderer = structlog.processors.JSONRenderer()
    else:
        structlog_log_renderer = structlog.dev.ConsoleRenderer()

    # Structlog wraps the stdlib logger, so any configuration of it
    # will work together with the third party library
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(),
            structlog_log_renderer,
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=structlog.contextvars,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    # Read in the file path given on the CLI
    parser = argparse.ArgumentParser(
        description="Reads values from an environment configuration HCL file"
    )

    parser.add_argument(
        "hcl_file_path",
        help="The file path to the particular environment HCL configuration",
    )

    parser.add_argument(
        "key",
        help="The key to look up in the given HCL file path",
    )

    args = parser.parse_args()

    try:
        with open(args.hcl_file_path, "r") as hcl_file:
            hcl_data = hcl2.load(hcl_file)
    except (IOError, OSError):
        logger.error("error opening HCL file path", hcl_file=args.hcl_file_path)
        raise

    try:
        value = hcl_data[args.key]
    except KeyError:
        logger.error("the requested key was not found", key=args.key, hcl_data=hcl_data)
        raise

    # Emit the value in JSON form
    print(json.dumps({args.key: value}))


if __name__ == "__main__":
    main()